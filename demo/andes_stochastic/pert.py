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

    # original value
    p0 = system.PQ.get(src='p0', attr='v', idx='PQ_1')

    # a random perturbation in load active power
    dp = np.random.normal(loc=0, scale=0.02)

    # update the active power of the load
    system.PQ.set(src='Ppf', attr='v', idx='PQ_1', value=p0 + dp)
