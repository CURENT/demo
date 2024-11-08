# AMS Benchmark Study

This folder contains benchmarking tools and scripts for various power system optimization tasks using different software environments.

<details>
<summary><strong>Table of Contents</strong></summary>

<details>
<summary><strong>opf</strong></summary>

**[cases](./opf/cases/):** Power flow cases in MATPOWER .m format, and some EDUC cases in AMS .xlsx format.
**[bench_opf.ipynb](./opf/bench_opf.ipynb):** Benchmarking notebook for OPF, using AMS and pandapower.
**[bench_opf_repeat.ipynb](./opf/bench_opf_repeat.ipynb):** Benchmarking notebook for OPF with multiple load levels, using AMS and pandapower.
**[bench_opf.m](./opf/bench_opf.m):** Benchmarking script for OPF, using MATPOWER with MATLAB.
**[bench_opf_repeat.m](./opf/bench_opf_repeat.m):** Benchmarking script for OPF with multiple load levels, using MATPOWER with MATLAB.
**[lfs_data.csv](./opf/lfs_data.csv):** Load profiles for `bench_opf_repeat.ipynb` and `bench_opf_repeat.m`.
**[bench_educ.ipynb](./opf/bench_educ.ipynb):** Benchmarking notebook for EDUC, using AMS.
**[bench_educ_large.ipynb](./opf/bench_educ_large.ipynb):** Benchmarking notebook for large-scale EDUC, using AMS.

</details>

<details>
<summary><strong>UCCase</strong></summary>

Large-scale unit commitment case synthesized from the Grid Optimization Competition (GOC) Challenge 2.

> S. Elbert et al., “ARPA-E Grid Optimization (GO) Competition Challenge 2.” DOE Open Energy Data Initiative (OEDI); Pacific Northwest National Laboratory, p. 29 files, 2024. doi: 10.25984/2448433.

</details>

<details>
<summary><strong>vis</strong></summary>

**[bench_vis.ipynb](./vis/bench_vis.ipynb):** Benchmarking notebook for virtual inertia support.

</details>

<details>
<summary><strong>results</strong></summary>

The generated benchmarking results.

</details>

<details>
<summary><strong>plot</strong></summary>

Scripts to plot and generated figures.
</details>

</details>

## Software Environment

To recreate the conda environment used for the benchmark, follow these steps:

1. **Ensure you have Conda installed**: If you don't have Conda installed, you can download and install it from the official Conda website.
1. **Create the environment**: Use the `environment.yml` file to create the environment by running the following command in your terminal:

    ```bash
    conda env create -f environment.yml
    ```
1. **Activate the environment**: Once the environment is created, activate it with:

    ```bash
    conda activate ams
    ```
1. **Verify the installation**: Ensure all packages are installed correctly by listing the installed packages:

    ```bash
    conda list
    ```

1. **Install the latest AMS**: If you want to use the latest version of AMS, you can install it from the source. 
    
    ```bash
    pip install git+https://github.com/CURENT/ams.git
    ```

<details>
<summary><strong>Tools version</strong></summary>

- **Python**: 3.10.0
- **ltbams**: 0.9.10.post153.dev0+gc73b7f8a
- **andes**: 1.9.1.post100+g2b17faac
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
- **MATLAB**: Version 24.2.0.2740171 (R2024b) Update 1
- **MATPOWER**: Version 7.1 (08-Oct-2020)

</details>

## Contributors

[Jinning Wang](https://github.com/jinningwang)
