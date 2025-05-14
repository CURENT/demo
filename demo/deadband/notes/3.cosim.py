import pandas as pd

import andes
import ams

andes.config_logger(stream_level=30)
ams.config_logger(stream_level=30)

# --- file loading ---
# 1. syntheric curve
curve = pd.read_csv('./../cases/Curve.csv')

# 2. OPF case
sp1 = ams.load('./../cases/IL200_rted_db.xlsx',
               setup=True, no_output=True,
               default_config=True)

# set Wind and Solar to be uncontrollable
stg_wind, stg_pv = sp1.StaticGen.find_idx(keys='genfuel',
                                          values=['wind', 'solar'], allow_all=True)
sp1.StaticGen.set(src='ctrl', attr='v', idx=stg_wind, value=0.0)
sp1.StaticGen.set(src='ctrl', attr='v', idx=stg_pv, value=0.0)

# 3. dynamic case
s1 = sp1.to_andes(addfile='./../cases/IL200_dyn_db.xlsx',
                  setup=False,
                  no_output=True,
                  default_config=True,)

# bias is manually measured, in unit MW/0.1Hz
slack_bus = s1.Slack.bus.v
s1.add('ACEc', param_dict=dict(bus=slack_bus, bias=-45))

s1.setup()
# scale up Turbine Governor VMAX
vmax0 = s1.TGOV1NDB.get(src='VMAX', attr='v', idx=s1.TGOV1NDB.idx.v)
s1.TGOV1NDB.set(src='VMAX', attr='v', idx=s1.TGOV1NDB.idx.v,
                value=10 * vmax0)

stg = sp1.StaticGen.get_all_idxes()
# sacle down StaticGen.pmin
sp1.StaticGen.set(src='pmin', attr='v', idx=stg, value=0)


# set load levels
p0 = sp1.PQ.get(src='p0', attr='v', idx=sp1.PQ.idx.v).copy()
sp1.PQ.set(src='p0', attr='v', idx=sp1.PQ.idx.v,
           value=curve['Load'].values[0:5].mean() * p0,
        #    value=0.85 * p0,
           )

# set wind power
p0_wind = sp1.StaticGen.get(src='p0', attr='v', idx=stg_wind).copy()
sp1.StaticGen.set(src='p0', attr='v', idx=stg_wind,
                  value=curve['Wind'].values[0:5].mean() * p0_wind)

# set solar power
p0_pv = sp1.StaticGen.get(src='p0', attr='v', idx=stg_pv).copy()
sp1.StaticGen.set(src='p0', attr='v', idx=stg_pv,
                  value=curve['PV'].values[0:5].mean() * p0_pv)

# pg0 <- p0, relax RTED ramping constraints
sp1.StaticGen.set(src='pg0', attr='v', idx=stg,
                  value=sp1.StaticGen.get(src='p0', attr='v', idx=stg))

sp1.RTED.run(solver='CLARABEL')
sp1.RTED.dc2ac()

sp1.dyn.send(adsys=s1, routine='RTED')

s1.PFlow.run()

_ = s1.TDS.init()

s1.TDS.run()
