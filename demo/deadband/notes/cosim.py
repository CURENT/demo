"""
Script to run a cosimulation.
"""

import os
import warnings

from dataclasses import dataclass

import numpy as np
import pandas as pd

import andes
import ams

# Seed the random number generator
np.random.seed(2025)

warnings.filterwarnings("ignore", category=np.ComplexWarning)


class AGC:
    def __init__(self,
                 sp: ams.system.System,
                 sa: andes.system.System,
                 curve: pd.DataFrame,
                 hour: int = 0,
                 addfile: str = None,
                 res_csv: str = 'cosim_results_h0.csv'):
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
        self.stg = sp.StaticGen.get_all_idxes()
        sn = self.sp.StaticGen.get(src='Sn', attr='v',
                                   idx=self.stg)
        self.bf0 = sn / sn.sum()  # Base participation factor
        self.bf = self.bf0.copy()  # Participation factor for AGC
        self.sp.StaticGen.set(src='pmin', attr='v',
                              idx=self.stg, value=0)

        # turn off ACOPF messaging
        self.sp.ACOPF.config.update(verbose=0, out_all=0)

        stg_slack = self.sp.Slack.idx.v
        self.syn_slack = self.sa.SynGen.find_idx(
            keys='gen', values=stg_slack)[0]

        self.spp0 = sp.PQ.p0.v.copy()  # Copy of initial AMS active load
        self.spq0 = sp.PQ.q0.v.copy()  # Copy of initial AMS reactive load

      #   self.sppg = sp.PQ.p0.v.copy()  # Copy of current AMS active load

        self.sap0 = sa.PQ.p0.v.copy()  # Copy of initial ANDES active load
        self.saq0 = sa.PQ.q0.v.copy()  # Copy of initial ANDES reactive load

      #   self.sapg = sa.PQ.p0.v.copy()  # Copy of current ANDES active gen
      #   self.saqg = sa.PQ.q0.v.copy()  # Copy of current ANDES reactive gen

        # NOTE: we are running cosim hour by hour, so do not
        # change the total_hour
        self.total_hour: int = 1  # total hours to simulate, 24 for a full day
        # total seconds in one hour to simulate, 3600 for a full hour
        self.total_sec: int = 3600
        self.RTED_interval: int = 300
        self.sp.RTED.config.update(
            t=self.RTED_interval/60)  # update RTED interval
        self.AGC_interval: int = 4  # AGC interval in seconds
        self.id_hour: int = hour  # Hour counter
        self.id_rted: int = 0  # RTED interval counter
        self.id_agc: int = 0  # AGC interval counter
        self.t: int = 0  # second
        self.kp: float = 0.2  # Proportional gain for AGC
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

        # new link table
        self.link = self.sp.dyn.link.copy().fillna(False)
        # existence of each type of generator
        self.link['has_gov'] = self.link['gov_idx'].fillna(
            0, inplace=False).astype(bool).astype(int)
        self.link['has_dg'] = self.link['dg_idx'].fillna(
            0, inplace=False).astype(bool).astype(int)
        self.link['has_rg'] = self.link['rg_idx'].fillna(
            0, inplace=False).astype(bool).astype(int)

    def ams_update_rted(self):
        """
        Update the load and generation in the AMS system based on curve.
        """
        # get the current time in hours and seconds
        mins_per_RTED = int(self.RTED_interval / 60)
        row_start = (self.id_hour-1) * 60 + (self.id_rted-1) * mins_per_RTED
        print(f"row_start: {row_start}, "
              f"mins_per_RTED: {mins_per_RTED}, ")

        # --- load ---
        load = self.curve['Load'].iloc[row_start:row_start +
                                       mins_per_RTED].values.mean()
        solar = self.curve['PV'].iloc[row_start:row_start +
                                      mins_per_RTED].values.mean()
        wind = self.curve['Wind'].iloc[row_start:row_start +
                                       mins_per_RTED].values.mean()

        pq_idx = self.sp.PQ.idx.v
        self.sp.PQ.set(src='p0', attr='v', idx=pq_idx,
                       value=1.0*load*self.spp0)
        self.sp.PQ.set(src='q0', attr='v', idx=pq_idx,
                       value=1.0*load*self.spq0)

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

        # DEBUG: skip AC conversion, instead, scale up RTED load a
        # little bit
        #   self.sp.RTED.dc2ac()
        #   if not self.sp.RTED.converted:
        #       raise RuntimeError(
        #           f'dc2ac failed at Hour: {self.id_hour}, '
        #           f'RTED: {self.id_rted}')

        # update bf
        stg_on_uid = np.where(self.sp.RTED.pg.v > 1e-4)[0]
        stg = self.sp.RTED.pg.get_all_idxes()
        stg_on = np.array(
            [1 if uid in stg_on_uid else 0 for uid in range(self.sp.RTED.pg.n)])
        sn = self.sp.StaticGen.get(src='Sn', attr='v', idx=stg)
        self.bf[:] = stg_on * sn / (stg_on * sn).sum()

        # send RTED results to ANDES
        self.sp.dyn.send(adsys=self.sa, routine='RTED')

    def loop_AGC(self):
        """
        Run the AGC logic for a single AGC interval.
        """
        self.link['agov'] = self.ACE_raw * self.bf * \
            self.link['has_gov'] * self.link['gammap']
        self.link['adg'] = self.ACE_raw * self.bf * \
            self.link['has_dg'] * self.link['gammap']
        self.link['arg'] = self.ACE_raw * self.bf * \
            self.link['has_rg'] * self.link['gammap']

      #   # DEBUG, block AGC for testing
      #   self.link['agov'] = 0
      #   self.link['adg'] = 0
      #   self.link['arg'] = 0

        # set into governor, Exclude NaN values for governor index
        agov_to_set = {gov: agov for gov, agov in zip(
            self.link['gov_idx'], self.link['agov']) if bool(gov)}
        self.sa.TurbineGov.set(src='paux0', idx=list(
            agov_to_set.keys()), attr='v', value=list(agov_to_set.values()))

        # set into dg, Exclude NaN values for dg index
        adg_to_set = {dg: adg for dg, adg in zip(
            self.link['dg_idx'], self.link['adg']) if bool(dg)}
        self.sa.DG.set(src='Pext0', idx=list(adg_to_set.keys()),
                       attr='v', value=list(adg_to_set.values()))

    def loop_SEC(self):
        """
        Run the main loop for a single second.
        """
        if self.t > 0:
         kbase = self.curve['Load'].iloc[self.t // 60]
         dp = self.out.loc[self.t, 'dp']  # get the dp value for this second
         kload = kbase + dp
         self.sa.PQ.set(src='Ppf', attr='v', idx=self.sa.PQ.idx.v,
                        value=kload * self.sap0)
         self.sa.PQ.set(src='Qpf', attr='v', idx=self.sa.PQ.idx.v,
                        value=kload * self.saq0)
         self.sa.TDS.config.tf = self.t % 3600  # set the time in seconds
         self.sa.TDS.run()  # run the time domain simulation
         self.record_output()  # Record output at the start of the second
         self.out.loc[self.t, 'kload'] = kload  # store the kload value

        # Update AGC PI controller
        self.ACE_raw = -(self.kp * self.sa.ACEc.ace.v.sum() +
                         self.ki * self.ACE_integral)
        self.ACE_integral = self.ACE_integral + self.sa.ACEc.ace.v.sum()

        if self.sa.exit_code != 0:
           raise RuntimeError(
               f'ANDES TDS exited with code {self.sa.exit_code} at '
               f'Hour: {self.id_hour}, Second: {self.t}')

    def record_output(self):
        """
        Record the output for the current hour and second.
        """
        mva = self.sa.config.mva
        freq = self.sa.config.freq

        self.out.loc[self.t, 'time'] = self.t
        omega = self.sa.SynGen.get(
            src='omega', attr='v', idx=self.syn_slack)
        self.out.loc[self.t, 'freq'] = omega * freq  # frequency in Hz

        self.out.loc[self.t, 'ACE'] = mva * self.ACE_raw
        agc_total = self.link[['agov', 'adg', 'arg']].sum().sum()
        self.out.loc[self.t, 'AGC'] = mva * agc_total

    def loop(self):
      """
      Main loop for the co-sim.
      """
      # --- Output ---
      # NOTE: since ANDES save_every is set to 0, we need to collect
      # the output manually. Add extra columns for any other outputs
      cols = ['time', 'freq', 'kload', 'ACE', 'AGC']
      self.out = pd.DataFrame(
          -1.0,
          index=np.arange(self.total_hour * self.total_sec),
          columns=cols,
          dtype=float
      )

      self.out['dp'] = np.random.normal(loc=0,
                                        scale=0.0001,
                                        size=self.total_hour * self.total_sec)

      for SEC in range(self.total_hour * self.total_sec):
         if self.t % 3600 == 0:
            print(f'--- Hour: {self.id_hour} ---')
            self.loop_HR()
            self.id_hour += 1  # increment hour counter
            self.id_rted = 0  # reset RTED counter

         if self.t % self.RTED_interval == 0:
            print(f'--- RTED: {self.id_rted} ---')
            self.id_rted += 1
            self.id_agc = 0
            self.loop_RTED()
            mva = self.sp.config.mva
            print(f'Load: {mva * self.sp.RTED.pd.v.sum():.2f} MW,'
                  f' Gen.: {mva * self.sp.RTED.pg.v.sum():.2f} MW'
                  f' Cost: {self.sp.RTED.obj.v:.2f} $')

         if self.t % self.AGC_interval == 0:
            self.loop_AGC()
            self.id_agc += 1

         self.loop_SEC()

         # --- Watchdog ---
         if self.t % 100 == 0:
            print(f'Watchdog: Second: {self.t % 3600}')
         self.t += 1

         if self.t > 601:
            print('Simulation stopped for testing.')
            break

      # --- Export results to CSV ---
      self.out.to_csv(self.res_csv, index=False)
      print(f'Co-simulation completed. Results saved to {self.res_csv}')
