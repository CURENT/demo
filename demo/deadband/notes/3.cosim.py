"""
Script to run a cosimulation.
"""

import os

from dataclasses import dataclass

import numpy as np
import pandas as pd

import andes
import ams

andes.config_logger(stream_level=50)
ams.config_logger(stream_level=50)

script_path = os.path.dirname(os.path.abspath(__file__))
case_path = os.path.abspath(os.path.join(script_path, '..', 'cases'))
res_path = os.path.abspath(os.path.join(script_path, '..', 'results'))
res_csv = os.path.join(res_path, 'case1.csv')

# --- file loading ---
curve = pd.read_csv(case_path + '/Curve.csv')
sp = ams.load(case_path + '/IL200_rted.xlsx',
              setup=True, no_output=True,
              default_config=True)
sa = sp.to_andes(addfile=case_path + '/IL200_dyn_db.xlsx',
                  setup=True, no_output=True,
                  default_config=True,)

# turn off ACOPF messaging
sp.ACOPF.config.update(verbose=0, out_all=0)

# set Wind and Solar to be uncontrollable, so their output
# power in RTED is fixed
stg_wind, stg_pv = sp.StaticGen.find_idx(keys='genfuel',
                                         values=['wind', 'solar'],
                                         allow_all=True)
sp.StaticGen.set(src='ctrl', attr='v', idx=stg_wind, value=0)
sp.StaticGen.set(src='ctrl', attr='v', idx=stg_pv, value=0)

# relax StaticGen.pmin
stg = sp.StaticGen.get_all_idxes()
sp.StaticGen.set(src='pmin', attr='v', idx=stg, value=0)

stg_slack = sp.Slack.idx.v
syn_slack = sa.SynGen.find_idx(keys='gen', values=stg_slack)[0]

# --- AGC Controller ---
@dataclass
class AGC:
   total_hour: int = 1  # total hours to simulate, 24 for a full day
   total_sec: int = 301  # total seconds in one hour to simulate, 3600 for a full hour
   RTED_interval: int = 300
   AGC_interval: int = 4  # AGC interval in seconds
   id_hour: int = -1  # Hour counter
   id_rted: int = -1  # RTED interval counter
   id_agc: int = -1  # AGC interval counter
   kp: float = 0.1  # Proportional gain for AGC
   ki: float = 0.05  # Integral gain for AGC
   ACE_integral: float = 0.0  # Integral of Area Control Error (ACE)
   ACE_raw: float = 0.0  # Raw Area Control Error (ACE)

AGC = AGC()

# --- Output ---
# NOTE: since ANDES save_every is set to 0, we need to collect
# the output manually. Add extra columns for any other outputs
cols = ['time', 'freq']
out = pd.DataFrame(
    -1.0,
    index=np.arange(AGC.total_hour * AGC.total_sec),
    columns=cols,
    dtype=float
)

# --- simulation setup ---

for HR in range(AGC.total_hour):
   # -- New Hour --
   AGC.id_rted = -1  # reset RTED counter
   # for each hour, reload the ANDES case
   sa = sp.to_andes(addfile=case_path + '/IL200_dyn_db.xlsx',
                    setup=True, no_output=True,
                    default_config=True,)
   # 1) ANDES settings
   # use constant power model for PQ
   sa.PQ.config.p2p = 1
   sa.PQ.config.q2q = 1
   sa.PQ.config.p2z = 0
   sa.PQ.config.q2z = 0
   sa.PQ.pq2z = 0

   sa.TDS.config.no_tqdm = True  # turn off ANDES progress bar
   sa.TDS.config.criteria = 0  # turn off ANDES criteria check
   sa.TDS.config.save_every = 0  # turn off ANDES save every time step

   # TODO: init the TDS
   sa.PFlow.run()  # run power flow to initialize the system
   _ = sa.TDS.init()  # initialize the time domain simulation

   if not sa.TDS.initialized:
      exit(f'ANDES TDS init failed at Hour: {HR}')

   for SEC in range(AGC.total_sec):
      # --- Wathdog ---
      if (SEC % 200 == 0) and (SEC > 0):
         print(f'Hour: {HR}, Second: {SEC}, '
               f'RTED ID: {AGC.id_rted}, AGC ID: {AGC.id_agc}')

      # --- RTED ---
      if SEC % AGC.RTED_interval == 0:
         AGC.id_rted += 1  # increment RTED counter
         AGC.id_agc = -1  # reset AGC counter for new RTED interval

         # run RTED
         sp.RTED.run(solver='CLARABEL')
         sp.RTED.dc2ac()

         # send RTED results to ANDES
         sp.dyn.send(adsys=sa, routine='RTED')

      # --- AGC ---
      if SEC % AGC.AGC_interval == 0:
         AGC.id_agc += 1
         # TODO: implement AGC logic

      # --- TDS ---
      sa.TDS.run()

      # --- Output ---
      current_time = HR * AGC.total_sec + SEC
      out.loc[current_time, 'time'] = HR * AGC.total_sec + SEC
      out.loc[current_time, 'freq'] = sa.SynGen.get(
          src='omega', attr='v', idx=syn_slack) * sa.config.freq  # freq in Hz

      if sa.exit_code != 0:
         exit(f'ANDES TDS exited with code {sa.exit_code} at '
              f'Hour: {HR}, Second: {SEC}')

# --- Export results to CSV ---
out.to_csv(res_csv, index=False)
print(f'Co-simulation completed. Results saved to {res_csv}')
