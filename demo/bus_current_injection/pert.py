"""
A pert file template.
"""

import numpy as np
from andes.thirdparty.npfunc import safe_div


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
    syg = system.SynGen.find_idx(
        keys='bus', values=system.Bus.idx.v,
        allow_all=True, default=None, allow_none=True)
    reg = system.RenGen.find_idx(
        keys='bus', values=system.Bus.idx.v,
        allow_all=True, default=None, allow_none=True)

    Id_syg = system.SynGen.get(src='Id', attr='v', idx=syg,
                               allow_none=True, default=0)
    Iq_syg = system.SynGen.get(src='Iq', attr='v', idx=syg,
                               allow_none=True, default=0)
    Id_reg = system.RenGen.get(src='Id', attr='v', idx=reg,
                               allow_none=True, default=0)
    Iq_reg = system.RenGen.get(src='Iq', attr='v', idx=reg,
                               allow_none=True, default=0)
    Id = Id_syg + Id_reg
    Iq = Iq_syg + Iq_reg

    system.Igen = np.append(system.Igen,
                            np.reshape(Id + 1j * Iq, (1, system.nb)),
                            axis=0)

    V1v = system.Bus.get(src='v', attr='v', idx=system.Line.bus1.v)
    V1a = system.Bus.get(src='a', attr='v', idx=system.Line.bus1.v)
    V1 = V1v * np.exp(1j * V1a * np.pi / 180)

    V2v = system.Bus.get(src='v', attr='v', idx=system.Line.bus2.v)
    V2a = system.Bus.get(src='a', attr='v', idx=system.Line.bus2.v)
    V2 = V2v * np.exp(1j * V2a * np.pi / 180)

    r = system.Line.r.v
    x = system.Line.x.v

    # Calculate the current flowing through the line
    Iline_through = safe_div(V1 - V2, r + 1j * x)

    Iline = system.Cft @ Iline_through

    system.Iline = np.append(system.Iline,
                            np.reshape(Iline, (1, system.nb)),
                            axis=0)
