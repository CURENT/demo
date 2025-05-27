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


class CoSimulation:
    """
    Do a co-simulation for one dispatch interval, using AMS and ANDES.
    """

    def __init__(self,
                 sp: ams.system.System,
                 sa: andes.system.System,
                 curve: pd.DataFrame,
                 Dispatch_interval: int = 300,
                 AGC_interval: int = 4,
                 addfile: str = None,
                 res_csv: str = 'cosim_results.csv'):
        self.sp: ams.system.System = sp  # AMS system instance
        self.sa: andes.system.System = sa  # ANDES system instance
        self.addfile: str = addfile
        self.curve: pd.DataFrame = curve  # Interpolated curve, for one hour
        self.res_csv: str = res_csv  # Path to save results CSV

        self.stg = self.sp.StaticGen.get_all_idxes()

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

        stg_slack = self.sp.Slack.idx.v
        self.syn_slack = self.sa.SynGen.find_idx(
            keys='gen', values=stg_slack)[0]

        self.spp0 = sp.PQ.p0.v.copy()  # Copy of initial AMS active load
        self.spq0 = sp.PQ.q0.v.copy()  # Copy of initial AMS reactive load

        self.sap0 = sa.PQ.p0.v.copy()  # Copy of initial ANDES active load
        self.saq0 = sa.PQ.q0.v.copy()  # Copy of initial ANDES reactive load

        self.Dispatch_interval: int = Dispatch_interval
        self.AGC_interval: int = AGC_interval  # AGC interval in seconds
        self.t: int = 0  # current time
        self.kp: float = 0.2  # Proportional gain for AGC
        self.ki: float = 0.05  # Integral gain for AGC
        self.ACE_integral: float = 0.0  # Integral of Area Control Error (ACE)
        self.ACE_raw: float = 0.0  # Raw Area Control Error (ACE)

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

    def run(self):
      """
      Main loop for the co-sim.
      """
      # --- Output ---
      # NOTE: since ANDES save_every is set to 0, we need to collect
      # the output manually. Add extra columns for any other outputs
      cols = ['time', 'freq', 'kload', 'ACE', 'AGC']
      self.out = pd.DataFrame(
          -1.0,
          index=np.arange(self.Dispatch_interval),
          columns=cols,
          dtype=float
      )

      for self.t in range(self.Dispatch_interval):
        # --- Dispatch Interval ---
        if self.t % self.Dispatch_interval == 0:
            # 1) AMS solve dispatch
            # update load, scale up a little bit for AC PFlow
            load = self.curve['Load'].values.mean()
            pq_idx = self.sp.PQ.idx.v
            self.sp.PQ.set(src='p0', attr='v', idx=pq_idx,
                           value=1.00*load*self.spp0)
            self.sp.PQ.set(src='q0', attr='v', idx=pq_idx,
                           value=1.00*load*self.spq0)
            # update gen
            psum = self.sp.PQ.p0.v.sum()
            solar = self.curve['PV'].values.mean()
            wind = self.curve['Wind'].values.mean()
            wind_sum = wind * self.p0_w2t.sum()
            solar_sum = solar * self.p0_pv.sum()
            # NOTE: discard wind and solar if they
            # exceed the total load
            if wind_sum + solar_sum > psum:
                dgen = wind_sum + solar_sum - psum
                dwind = dgen / (wind_sum + solar_sum) * wind_sum
                dsolar = dgen / (wind_sum + solar_sum) * solar_sum
                wind = (wind_sum - 1.02*dwind) / wind_sum
                solar = (solar_sum - 1.02*dsolar) / solar_sum

            self.sp.StaticGen.set(src='p0', attr='v', idx=self.stg_w2t,
                                  value=wind*self.p0_w2t)
            self.sp.StaticGen.set(src='p0', attr='v', idx=self.stg_pv,
                                  value=solar*self.p0_pv)

            self.sp.DCOPF.update()
            self.sp.DCOPF.run(solver='CLARABEL')
            if not self.sp.DCOPF.converged:
                raise RuntimeError(f'OPF did not converge!')

            # 2) update bf
            stg_on_uid = np.where(self.sp.DCOPF.pg.v > 1e-4)[0]
            stg = self.sp.DCOPF.pg.get_all_idxes()
            stg_on = np.array(
                [1 if uid in stg_on_uid else 0 for uid in range(self.sp.OPF.pg.n)])
            sn = self.sp.StaticGen.get(src='Sn', attr='v', idx=stg)
            self.bf[:] = stg_on * sn / (stg_on * sn).sum()

            mva = self.sp.config.mva
            print(f'Load: {mva * load * self.spp0.sum():.2f} MW,'
                  f' Gen.: {mva * self.sp.DCOPF.pg.v.sum():.2f} MW'
                  f' Cost: {self.sp.DCOPF.obj.v:.2f} $')

        # --- AGC Interval ---
        # Compute AGC signals only for generators with corresponding controllers
        for col, has_col in [('agov', 'has_gov'), ('adg', 'has_dg'), ('arg', 'has_rg')]:
            self.link[col] = self.ACE_raw * self.bf * \
                self.link[has_col] * self.link['gammap']
        #   # DEBUG, block AGC for testing
        #   self.link['agov'] = 0
        #   self.link['adg'] = 0
        #   self.link['arg'] = 0
        if self.t % self.AGC_interval == 0 and self.t > 0:
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

        # --- TDS Interval ---
        if self.t > 0:  # when t>0, run TDS
            # 1) Update loads
            kload = self.curve['Load'].iloc[self.t]
            self.sa.PQ.set(src='Ppf', attr='v', idx=self.sa.PQ.idx.v,
                           value=kload * self.sap0)
            self.sa.PQ.set(src='Qpf', attr='v', idx=self.sa.PQ.idx.v,
                           value=kload * self.saq0)
            # ANDES wind and solar
            wind = self.curve['Wind'].iloc[self.t]
            self.sa.StaticGen.set(src='p0', attr='v', idx=self.stg_w2t,
                                  value=wind * self.p0_w2t)
            solar = self.curve['PV'].iloc[self.t]
            self.sa.StaticGen.set(src='p0', attr='v', idx=self.stg_pv,
                                  value=solar * self.p0_pv)

            self.sa.TDS.config.tf = self.t
            self.sa.TDS.run()
        else:  # t == 0, we run PFlow and init TDS
            self.sa.PQ.set(src='p0', attr='v',
                           idx=self.sp.DCOPF.pd.get_all_idxes(),
                           value=self.sp.DCOPF.pd.v)
            self.sa.StaticGen.set(src='p0', attr='v',
                                  idx=self.sp.DCOPF.pg.get_all_idxes(),
                                  value=self.sp.DCOPF.pg.v)
            self.sa.PFlow.run()
            _ = self.sa.TDS.init()
            if not self.sa.TDS.initialized:
                raise RuntimeError(f'ANDES TDS init failed!')

        # 2) Record output
        mva = self.sa.config.mva
        freq = self.sa.config.freq
        self.out.loc[self.t, 'time'] = self.t
        omega = self.sa.SynGen.get(src='omega', attr='v',
                                   idx=self.syn_slack)
        self.out.loc[self.t, 'freq'] = omega * freq  # frequency in Hz

        self.out.loc[self.t, 'ACE'] = mva * self.ACE_raw
        agc_total = self.link[['agov', 'adg', 'arg']].sum().sum()
        self.out.loc[self.t, 'AGC'] = mva * agc_total

        self.out.loc[self.t, 'kload'] = self.curve.loc[self.t,
                                                       'Load']  # store the kload value
        # 3) Update AGC PI controller
        self.ACE_raw = -(self.kp * self.sa.ACEc.ace.v.sum() +
                         self.ki * self.ACE_integral)
        self.ACE_integral = self.ACE_integral + self.sa.ACEc.ace.v.sum()

        if self.sa.exit_code != 0:
            raise RuntimeError(
                f'ANDES exited with {self.sa.exit_code} at {self.t}s')

         # --- Watchdog ---
        if self.t % 100 == 0 and self.t > 0:
            print(f'Watchdog: Second: {self.t}')

      # --- Export results to CSV ---
      self.out.to_csv(self.res_csv, index=False)
      print(f'Co-simulation completed. Results saved to {self.res_csv}')
