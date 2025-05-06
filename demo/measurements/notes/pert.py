"""
A pert file template.
"""

import numpy as np


def pert(t, system):
    """
    Perturbation function called at each step.

    The function needs to be named ``pert`` and takes two positional arguments:
    ``t`` for the simulation time, and ``system`` for the system object.
    Arbitrary logic and calculations can be applied in this function to
    ``system``.

    If the perturbation event involves switching, such as disconnecting a line,
    one will need to set the ``system.TDS.custom_event`` flag to ``True`` to
    trigger a system connectivity checking, and Jacobian rebuilding and
    refactorization. To implement, add the following line to the scope where the
    event is triggered:

    .. code-block :: python

        system.TDS.custom_event = True

    In other scopes of the code where events are not triggered, do not add the
    above line as it may cause significant slow-down.

    The perturbation file can be supplied to the CLI using the ``--pert``
    argument or supplied to :py:func:`andes.main.run` using the ``pert``
    keyword.

    Parameters
    ----------
    t : float
        Simulation time.
    system : andes.system.System
        System object supplied by the simulator.
    """
    # NOTE: in ANDES, PQ.p0 is a parameter and its value can be altered as necessary
    #  When they are set as constant load, their values remain unchanged
    # --- random load change ---
    system.dp = np.random.normal(loc=system.loc, scale=system.scale)
    # update the active power of the load
    system.PQ.set(src='Ppf', attr='v', idx='PQ_1',
                  value=system.p0 + system.dp)

    # --- FFR ---
    # different PMU alg. will give us "df" and "enable" signals
    # df -> system.df, enable -> system.ue
    # 1) RoCoF calc.

    # 2) Freq.

    # 3) FFR control
    system.dt = t - system.t0[0]

    # --- THIS PART SHOULD BE SKIPPED IF ACTUAL PMU ALG. IS USED ---
    system.df[:] = (system.BusFreq.get(
        src='f', idx=system.busf_idx) - 1) * system.fn
    if system.df < -system.fdb or system.df > system.fdb:
        system.ue[:] = True
    else:
        system.df[:] = 0

    system.Integral[:] += system.df * system.dt
    system.PIy[:] = system.ue * \
        (system.Kp * system.df + system.Ki * system.Integral)

    system.ESD1.set(src='Pext0', attr='v', idx='ESD1_1', value=system.PIy)

    # --- update time stamp ---
    system.t0[:] = t

    # update POW
    system.omega[:] = system.GENROU.get(src='omega', attr='v',
                                        idx=[system.syn0])

    v_syn = system.GENROU.get(src='v', attr='v', idx=system.syn0)

    # Synthetic Point on Wave (PoW) value
    system.vpow[:] = v_syn * np.sin(system.fb * system.omega * t + system.a0)
