# AMS Benchmark

## Tools Version

### Python Environment

- **Python**: 3.10.0
- **ltbams**: 0.9.10.post18+g43b7dbe3
- **cvxpy**: 1.5.3
- **pandapower**: 2.14.11
- **PYPOWER**: 5.1.17
- **gurobipy**: 11.0.3
- **mosek**: 10.2.6
- **ecos**: 2.0.14
- **scs**: 3.2.7
- **piqp**: 0.4.2
- **osqp**: 0.6.7.post0
- **numba**: 0.60.0

### MATLAB Environment

- **MATLAB**: Version 24.2.0.2740171 (R2024b) Update 1
- **MATPOWER**: Version 7.1 (08-Oct-2020)

## Scripts Description

### OPF Scripts

- **cases**: Power flow cases in MATPOWER `.m` format.
- **bench_opf.ipynb**: Benchmarking notebook for OPF, using AMS and pandapower.
- **bench_opf_repeat.ipynb**: Benchmarking notebook for OPF with multiple load levels, using AMS and pandapower.
- **bench_opf.m**: Benchmarking script for OPF, using MATPOWER with MATLAB.
- **bench_opf_repeat.m**: Benchmarking script for OPF with multiple load levels, using MATPOWER with MATLAB.
- **bench_educ.ipynb**: Benchmarking notebook for EDUC, using AMS.
- **bench_educ_large.ipynb**: Benchmarking notebook for large-scale EDUC, using AMS.
- **lfs_data.csv**: Load profiles for `bench_opf_repeat.ipynb` and `bench_opf_repeat.m`.

### Unit Commitment Case

- **UCCase**: Large-scale unit commitment case synthesized from the Grid Optimization Competition (GOC) Challenge 2.

### Plotting Scripts

- **bench_plot.ipynb**: Plotting notebook for the benchmarking results.

### Virtual Inertia Case

- **bench_vis.ipynb**: Benchmarking notebook for virtual inertia support, using AMS.