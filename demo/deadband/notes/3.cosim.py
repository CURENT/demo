"""
Script to run co-simulation
"""

import logging

from dataclasses import dataclass

import pandas as pd

import andes
import ams

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

andes.config_logger(stream_level=30)
ams.config_logger(stream_level=30)

# --- file loading ---
curve = pd.read_csv('./../cases/Curve.csv')
sp = ams.load('./../cases/IL200_rted.xlsx',
              setup=True, no_output=True,
              default_config=True)
sa = sp.to_andes(addfile='./../cases/IL200_dyn_db.xlsx',
                 setup=True, no_output=True,
                 default_config=True,)

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

# --- time constants ---
@dataclass
"""
Represents the Automatic Generation Control (AGC) controller for a simulation.

Attributes:
   total_time (int): Total simulation time in seconds.
   RTED_interval (int): Real-Time Economic Dispatch (RTED) interval in seconds.
"""
class AGC:
   total_time: int = 600  # total simulation time in seconds
   RTED_interval: int = 300
   AGC_interval: int = 4  # AGC interval in seconds
   id_rted: int = -1  # RTED interval counter
   id_agc: int = -1  # AGC interval counter
   kp: float = 0.1  # Proportional gain for AGC
   ki: float = 0.05  # Integral gain for AGC
   ACE_integral: float = 0.0  # Integral of Area Control Error (ACE)
   ACE_raw: float = 0.0  # Raw Area Control Error (ACE)

AGC = AGC()

# --- simulation setup ---
# 1) ANDES
# use constant power model for PQ
sa.PQ.config.p2p = 1
sa.PQ.config.q2q = 1
sa.PQ.config.p2z = 0
sa.PQ.config.q2z = 0
sa.PQ.pq2z = 0

sa.TDS.config.no_tqdm = True  # turn off ANDES progress bar
sa.TDS.config.criteria = 0  # turn off ANDES criteria check
sa.TDS.config.save_every = 0  # turn off ANDES save every time step


# # set load levels
# p0 = sp.PQ.get(src='p0', attr='v', idx=sp.PQ.idx.v).copy()
# sp.PQ.set(src='p0', attr='v', idx=sp.PQ.idx.v,
#           value=curve['Load'].values[0:5].mean() * p0,
#           #    value=0.85 * p0,
#           )

# # set wind power
# p0_wind = sp.StaticGen.get(src='p0', attr='v', idx=stg_wind).copy()
# sp.StaticGen.set(src='p0', attr='v', idx=stg_wind,
#                  value=curve['Wind'].values[0:5].mean() * p0_wind)

# # set solar power
# p0_pv = sp.StaticGen.get(src='p0', attr='v', idx=stg_pv).copy()
# sp.StaticGen.set(src='p0', attr='v', idx=stg_pv,
#                  value=curve['PV'].values[0:5].mean() * p0_pv)

# # pg0 <- p0, relax RTED ramping constraints
# sp.StaticGen.set(src='pg0', attr='v', idx=stg,
#                  value=sp.StaticGen.get(src='p0', attr='v', idx=stg))

# sp.RTED.run(solver='CLARABEL')
# sp.RTED.dc2ac()

# sp.dyn.send(adsys=sa, routine='RTED')

# sa.PFlow.run()

# _ = sa.TDS.init()

# sa.TDS.run()
