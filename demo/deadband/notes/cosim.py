"""
Script to run a cosimulation.
"""

import os

from dataclasses import dataclass

import numpy as np
import pandas as pd

import andes
import ams


class AGC:
    def __init__(self,
                 sp: ams.system.System,
                 sa: andes.system.System,
                 curve: pd.DataFrame,
                 addfile: str = None,
                 res_csv: str = 'cosim_results.csv'):
        self.sp: ams.system.System = sp  # AMS system instance
        self.sa: andes.system.System = sa  # ANDES system instance
        self.addfile: str = addfile
        self.curve: pd.DataFrame = curve  # Load curve for RTED
        self.res_csv: str = res_csv  # Path to save results CSV

        stg_idxes = self.sp.StaticGen.find_idx(keys='gentype',
                                               values=['W2', 'PV', 'ES'],
                                               allow_all=True)

        # set controllability
        self.stg_w2t = stg_idxes[0]
        self.stg_pv = stg_idxes[1]
        self.stg_ess = stg_idxes[2]

        for gens in [self.stg_w2t, self.stg_pv, self.stg_ess]:
         self.sp.StaticGen.set(src='ctrl', attr='v', idx=gens, value=0)

        self.p0_w2t = self.sp.StaticGen.get(src='p0', attr='v',
                                            idx=self.stg_w2t)
        self.p0_pv = self.sp.StaticGen.get(src='p0', attr='v',
                                           idx=self.stg_pv)

        # relax StaticGen.pmin
        stg = sp.StaticGen.get_all_idxes()
        self.sp.StaticGen.set(src='pmin', attr='v', idx=stg, value=0)

        # turn off ACOPF messaging
        self.sp.ACOPF.config.update(verbose=0, out_all=0)

        stg_slack = self.sp.Slack.idx.v
        self.syn_slack = self.sa.SynGen.find_idx(
            keys='gen', values=stg_slack)[0]

        # In the ANDES case, get the corresponding SynGen idx
        self.syg_w2t = self.sa.SynGen.find_idx(keys='gen', values=self.stg_w2t)
        self.syg_pv = self.sa.SynGen.find_idx(keys='gen', values=self.stg_pv)
        self.syg_ess = self.sa.SynGen.find_idx(keys='gen', values=self.stg_ess)

        self.spp0 = sp.PQ.p0.v.copy()  # Copy of initial AMS active load
        self.spq0 = sp.PQ.q0.v.copy()  # Copy of initial AMS reactive load

        self.sppg = sp.PQ.p0.v.copy()  # Copy of current AMS active load

        self.sap0 = sa.PQ.p0.v.copy()  # Copy of initial ANDES active load
        self.saq0 = sa.PQ.q0.v.copy()  # Copy of initial ANDES reactive load

        self.sapg = sa.PQ.p0.v.copy()  # Copy of current ANDES active load
        self.saqg = sa.PQ.q0.v.copy()  # Copy of current ANDES reactive load

        self.total_hour: int = 2  # total hours to simulate, 24 for a full day
        self.total_sec: int = 3600  # total seconds in one hour to simulate, 3600 for a full hour
        self.RTED_interval: int = 300
        self.AGC_interval: int = 4  # AGC interval in seconds
        self.id_hour: int = 0  # Hour counter
        self.id_rted: int = 0  # RTED interval counter
        self.id_agc: int = 0  # AGC interval counter
        self.id_sec: int = 0  # second counter
        self.kp: float = 0.1  # Proportional gain for AGC
        self.ki: float = 0.05  # Integral gain for AGC
        self.ACE_integral: float = 0.0  # Integral of Area Control Error (ACE)
        self.ACE_raw: float = 0.0  # Raw Area Control Error (ACE)

    def to_andes(self):
        """
        Convert AMS system to ANDES system.
        """
        self.sa = self.sp.to_andes(addfile=self.addfile,
                                   setup=True,
                                   no_output=True,
                                   default_config=True)
        if not self.sa:
            raise ValueError('Failed to convert AMS system to ANDES system.')
        # 1) ANDES settings
        # use constant power model for PQ
        self.sa.PQ.config.p2p = 1
        self.sa.PQ.config.q2q = 1
        self.sa.PQ.config.p2z = 0
        self.sa.PQ.config.q2z = 0
        self.sa.PQ.pq2z = 0

        self.sa.TDS.config.no_tqdm = True  # turn off ANDES progress bar
        self.sa.TDS.config.criteria = 0  # turn off ANDES criteria check
        self.sa.TDS.config.save_every = 0  # turn off ANDES save every time step

    def ams_update_rted(self):
        """
        Update the load and generation in the AMS system based on curve.
        """
        # get the current time in hours and seconds
        mins_per_RTED = int(self.RTED_interval / 60)
        row_start = self.id_hour * 60 + self.id_rted * mins_per_RTED

        # --- load ---
        load = self.curve['Load'].iloc[row_start:row_start +
                                       mins_per_RTED].values.mean()
        solar = self.curve['PV'].iloc[row_start:row_start +
                                      mins_per_RTED].values.mean()
        wind = self.curve['Wind'].iloc[row_start:row_start +
                                       mins_per_RTED].values.mean()

        pq_idx = self.sp.PQ.idx.v
        self.sp.PQ.set(src='p0', attr='v', idx=pq_idx, value=load*self.spp0)
        self.sp.PQ.set(src='q0', attr='v', idx=pq_idx, value=load*self.spq0)

        # --- generation ---
        self.sp.StaticGen.set(src='p0', attr='v', idx=self.stg_w2t,
                              value=wind*self.p0_w2t)
        self.sp.StaticGen.set(src='p0', attr='v', idx=self.stg_pv,
                              value=solar*self.p0_pv)

        self.sp.RTED.update(['pd', 'pg0'])

    def loop_HR(self):
        """
        Run the main loop for a single hour.
        """
        # for each hour, reload the ANDES case
        self.to_andes()
        self.sa.PFlow.run()
        # run power flow to initialize the system
        _ = self.sa.TDS.init()  # initialize the time domain simulation
        if not self.sa.TDS.initialized:
            raise RuntimeError(
                f'ANDES TDS init failed at Hour: {self.id_hour}')

    def loop_RTED(self):
        """
        Run the RTED logic for a single RTED interval.
        """
        self.ams_update_rted()
        self.sp.RTED.run(solver='CLARABEL')
        if not self.sp.RTED.converged:
            raise RuntimeError(
                f'RTED did not converge at Hour: {self.id_hour}, '
                f'RTED: {self.id_rted}')
        self.sp.RTED.dc2ac()
        if not self.sp.RTED.converted:
            raise RuntimeError(
                f'dc2ac failed at Hour: {self.id_hour}, '
                f'RTED: {self.id_rted}')

        # send RTED results to ANDES
        self.sp.dyn.send(adsys=self.sa, routine='RTED')

    def loop_AGC(self):
        """
        Run the AGC logic for a single AGC interval.
        """
        pass
      #   TODO: Implement AGC logic

    def loop_SEC(self):
        """
        Run the main loop for a single second.
        """
        if self.id_sec > 0:
         self.sa.TDS.config.tf = self.id_sec % 3600  # set the time in seconds
         self.sa.TDS.run()  # run the time domain simulation
         self.record_output()  # Record output at the start of the second

        if self.sa.exit_code != 0:
           raise RuntimeError(
               f'ANDES TDS exited with code {self.sa.exit_code} at '
               f'Hour: {self.id_hour}, Second: {self.id_sec}')

    def record_output(self):
        """
        Record the output for the current hour and second.
        """
        self.out.loc[self.id_sec, 'time'] = self.id_sec
        self.out.loc[self.id_sec, 'freq'] = self.sa.SynGen.get(
            src='omega', attr='v', idx=self.syn_slack) * \
            self.sa.config.freq  # freq in Hz

    def loop(self):
      """
      Main loop for the co-sim.
      """
      # --- Output ---
      # NOTE: since ANDES save_every is set to 0, we need to collect
      # the output manually. Add extra columns for any other outputs
      cols = ['time', 'freq']
      self.out = pd.DataFrame(
         -1.0,
         index=np.arange(self.total_hour * self.total_sec),
         columns=cols,
         dtype=float
      )

      for SEC in range(self.total_hour * self.total_sec):
         if self.id_sec % 3600 == 0:
            print(f'--- Hour: {self.id_hour} ---')
            self.loop_HR()
            self.id_hour += 1  # increment hour counter
            self.id_rted = 0  # reset RTED counter

         if self.id_sec % self.RTED_interval == 0:
            print(f'--- RTED: {self.id_rted} ---')
            self.id_rted += 1
            self.id_agc = 0
            self.loop_RTED()

         if self.id_sec % self.AGC_interval == 0:
            self.loop_AGC()

         self.loop_SEC()

         # --- Watchdog ---
         if self.id_sec % 100 == 0:
            print(f'Watchdog: Second: {self.id_sec % 3600}')

         self.id_sec += 1

         if self.id_sec > 400:
            print('Simulation stopped for testing.')
            break

      # --- Export results to CSV ---
      self.out.to_csv(self.res_csv, index=False)
      print(f'Co-simulation completed. Results saved to {self.res_csv}')
