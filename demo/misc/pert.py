
def pert(t, system):
    """
    Demonstration of perturbation function.

    This file should be applied to built-in IEEE 14-bus
    case "ieee14/ieee14_full.xlsx".

    In the given case, `Line` "Line_1" and "Line_2" are
    connected to `Bus` "1" through parameter `bus1`,
    and line injected active power is inspected through
    `Line.a1.e`.
    """
    Pinj_line = system.Line.get(src='a1', attr='e',
                                idx=['Line_1', 'Line_2'])
    print(f"t={t:.5f}, pinj_line={Pinj_line.sum():.5f}")
