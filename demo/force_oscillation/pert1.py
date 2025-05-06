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

    t_start = 1
    t_end = 10

    if t > t_start and t < t_end:
        # Let's add a 15 Hz voltage disturbance to the voltage reference of the
        # exciter.
        vd = 0.1 * np.sin(2 * np.pi * 0.6 * t + 0.5 * np.pi)
        system.EXDC2.set(src='vref0', attr='v', idx=2, value=system.vref0+vd)
    elif t >= t_end:
        # Let's remove the disturbance.
        system.EXDC2.set(src='vref0', attr='v', idx=2, value=system.vref0)
