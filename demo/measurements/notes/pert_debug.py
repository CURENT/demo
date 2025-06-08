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
    vout = system.ESD1.get(src='v', attr='v', idx=system.esd1)
    Iout = system.ESD1.get(src='Ipcmd_y', attr='v', idx=system.esd1)
    system.Pout[:] = vout * Iout
    # record output data
    system.out[system.i, :] = np.concatenate(
        (system.t0, system.df, system.f, system.rocof, system.vpow,
         system.ue, system.Pin, system.Pout,
         system.df2, system.f2, system.rocof2,),
        axis=0)
    system.i += 1

    # NOTE: in ANDES, PQ.p0 is a parameter and its value can be altered as necessary
    #  When they are set as constant load, their values remain unchanged
    # --- random load change ---
    system.dp = np.random.normal(loc=system.loc, scale=system.scale)
    # update the active power of the load
    system.PQ.set(src='Ppf', attr='v', idx='PQ_1',
                  value=system.p0 + system.dp)

    # --- signal measurement ---
    system.dt = t - system.t0[0]
    system.df[:], system.f[:], system.rocof[:], system.df2[:], system.f2[:], system.rocof2[:] = measure(
        system, method=system.m)

    # --- FFR control ---
    # TODO: Improve FFR trigger
    if system.df < -system.fdb or system.df > system.fdb:
        system.ue[:] = 1
    else:
        system.ue[:] = 0

    system.Integral[:] += system.ue * system.df / system.fn * system.dt
    system.Pin[:] = system.ue * \
        (system.Kp * system.df / system.fn + system.Ki * system.Integral)

    system.ESD1.set(src='Pext0', attr='v', idx='ESD1_1', value=system.Pin)

    # --- update time stamp ---
    system.t0[:] = t

    # update POW
    system.omega[:] = system.GENROU.get(src='omega', attr='v',
                                        idx=[system.syn0])

    v_syn = system.GENROU.get(src='v', attr='v', idx=system.syn0)

    # Synthetic Point on Wave (PoW) value
    system.vpow[:] = v_syn * np.sin(system.fb * system.omega * t + system.a0)


def measure(system, method=0):
    """
    Measure frequency deviation, frequency, and rate of change of frequency.
    When method is not supported, m0 is used.

    Parameters
    ----------
    system : andes.system.System
        System object supplied by the simulator.
    method : int, optional
        Method to use.
        0 : Baseline, dynamic models in simulation.
        1 : TBD.
    
    Returns
    -------
    df : float
        Frequency deviation, Hz.
    f : float
        Frequency, Hz.
    rocof : float
        Rate of change of frequency, Hz/s.
    df2 : float
        Frequency deviation, Hz (alternative method).
    f2 : float
        Frequency, Hz (alternative method).
    rocof2 : float
        Rate of change of frequency, Hz/s (alternative method).
    """
    # --- update buffer ---
    system.buf[system.nbuf] = system.omega * system.config.freq
    system.nbuf += 1

    if system.nbuf >= system.buf.shape[0]:
        # when the buffer is full, use np.roll for efficient shifting
        system.buf = np.roll(system.buf, -1)
        system.buf[-1] = system.omega * system.config.freq
        system.nbuf = system.buf.shape[0] - 1

    df, f, rocof = m0(system)
    df2, f2, rocof2 = m1(system)

    return df, f, rocof, df2, f2, rocof2


def m0(system):
    """
    Measure frequency deviation, frequency, and rate of change of frequency.

    Parameters
    ----------
    system : andes.system.System
        System object supplied by the simulator.
    
    Returns
    -------
    df : float
        Frequency deviation, Hz.
    f : float
        Frequency, Hz.
    rocof : float
        Rate of change of frequency, Hz/s.
    """
    f = system.fn * system.BusFreq.get(src='f', idx=system.busf_idx)
    df = f - system.fn
    rocof = system.df * system.fn
    return df, f, rocof


def m1(system):
    """
    Measure frequency deviation, frequency, and rate of change of frequency
    using an alternative method.

    Parameters
    ----------
    system : andes.system.System
        System object supplied by the simulator.
    
    Returns
    -------
    df2 : float
        Frequency deviation, Hz (alternative method).
    f2 : float
        Frequency, Hz (alternative method).
    rocof2 : float
        Rate of change of frequency, Hz/s (alternative method).
    """
    # TODO: implement other methods here
    f2 = 0
    df2 = 0
    rocof2 = 0
    return df2, f2, rocof2
