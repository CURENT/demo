
import os
import andes
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

def get_andes_case(case_path):
    '''
        Get the andes case from the case path.
    
        inputs:
        -------
        case_path: str

        returns:
        --------
        andes attribute
    '''
    # ss0 is used for PP conversion
    dir_path = os.path.abspath('..')

    case = dir_path + case_path
    ssa = andes.load(case,
                    setup=True,
                    no_output=True,
                    default_config=False)

    # Set output mode as 'manual'
    ssa.TDS.config.save_mode = 'manual'

    # set PQ constant load
    ssa.PQ.config.p2p = 1
    ssa.PQ.config.q2q = 1
    ssa.PQ.config.p2z = 0
    ssa.PQ.config.q2z = 0
    ssa.PQ.pq2z = 0

    # Turn on 'numba' to accelerate TDS.
    ssa.config.numba

    return ssa

def get_load(data_path, load_time=10, l_rate=1, scale=1):
    '''
        Get normalized load profile
    
        inputs:
        -------
        data_path: str
        load_time: int
            The time of load profile, default is 10, can also be 18
        l_rate: float
            initial load rate
        scale: float
            scale exisitng load profile

        returns:
        --------
        load data: pandas dataframe
            normalized by mean value
        load fig: load figure
        dpe: delta_Pe based on load profile
    '''

    dir_path = os.path.abspath('..')
    path = dir_path + data_path
    d_syn = pd.read_csv(path)

    caseH = load_time

    # the coefficient can be adjusted to fit the case
    if caseH == 10: # load prfile at 10am
        d_syn['sload'] = scale *(d_syn['ha10'] - d_syn['ha10'].min()) / d_syn['ha10'].min() + 1
    if caseH == 18: # load prfile at 6pm
        d_syn['sload'] = scale *(d_syn['ha18'] - d_syn['ha18'].min()) / d_syn['ha18'].min() + 1

    d_syn['sload'][2400:3000] *= 1.028

    # smooth
    d_syn['sload'] = d_syn['sload'].rolling(20).mean()
    
    # calculate expected load
    step = 300
    d_exp = d_syn.groupby(d_syn.index // step).mean()
    d_exp['time'] = range(0, 3600, 300)

    # align starting point of load with starting point of dispatch results
    d_syn['sload'][0] = d_exp['sload'].iloc[0]
    d_syn['sload'][1:100] = None
    d_syn['sload'] = d_syn['sload'].interpolate(method='polynomial', order=3)

    ystep = list(d_exp['sload'])
    ystep.insert(0, d_exp['sload'].iloc[0])

    # --- plot load curve ---
    fig_load, ax_load = plt.subplots(figsize=(5, 4))

    # tds load profile
    ax_load.plot(
                    d_syn['time'], 
                    np.array(d_syn['sload']) * l_rate, 
                    color='tab:blue', 
                    linestyle='-'
                )

    # ED load profile
    ax_load.step(
                    range(0,3900,300), 
                    np.array(ystep) * l_rate, 
                    color='tab:blue', 
                    linestyle='--'
                )
                
    ax_load.set_xlim([0, 3600])
    ax_load.legend(['Actual load', 'Forecasted load'])
    ax_load.set_title(f'Load profile at {caseH}H')
    ax_load.set_ylabel('Load rate')
    ax_load.set_xlabel('Time [s]')

    dpe = np.array(d_exp['sload']) - 1 # with base p0
    dpe *= l_rate

    return d_syn, fig_load, dpe

def disturbance(d_syn, idx_ed, intv_ed, vsg_num=4):
    """
        get disturbance
        
        return:
        ----------
        - load_exp: load forecasted value
        - dpe: delta load change
        - dvsg: vsg gen capacity change
    """
    idx0 = idx_ed * intv_ed # start index
    idx1 = idx0 + intv_ed   # end index

    # --- load change ---
    load = d_syn['sload'].iloc[idx0 : idx1] 
    load_exp = load.mean()

    # --- dpe ---
    if idx_ed == 0:
        dpe = 0
    else:
        load_early = d_syn['sload'].iloc[idx0 - intv_ed : idx1 - intv_ed]
        load_exp_early = load_early.mean()
        dpe = load_exp - load_exp_early

    # --- vsg gen capacity change ---
    # TODO: add vsg gen capacity change
    dvsg = [0] * vsg_num

    return load_exp, dpe, dvsg
