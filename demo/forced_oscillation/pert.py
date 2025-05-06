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

    if t > system.t1 and t < system.t2:
        v = system.vd * np.sin(2 * np.pi * system.fd * t)
        system.EXDC2.set(src='vref0', attr='v',
                         idx=system.exc,
                         value=system.vref0+v)
    elif t >= system.t2:
        # Let's remove the disturbance.
        system.EXDC2.set(src='vref0', attr='v',
                         idx=system.exc,
                         value=system.vref0)
