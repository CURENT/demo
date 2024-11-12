"""
A pert file template.
"""


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
    # NOTE: in this settings, we emulate that the HVDC line act at 10.0s
    # where the sending end converter withdraw 0.1 pu active power and 0.05 pu reactive power
    # the receiving converter output 0.1 pu active power and terminal voltage is 1.0 pu
    
    if t > 10.0:
        # --- pseudo calculation ---
        pin = 0.1
        qin = 0.05
        vout = 0.1
        vf = 1.0

        # --- set the values ---
        system.PQ.set(src='Ppf', attr='v', idx='CONS', value=pin)
        system.PQ.set(src='Qpf', attr='v', idx='CONS', value=qin)
        system.SynGen.set(src='tm0', attr='v', idx='CONR', value=vout)
        system.SynGen.set(src='vf', attr='v', idx='CONR', value=vf)
