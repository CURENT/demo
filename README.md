# CURENT LTB Usage Examples

A collection of examples for using CURENT LTB.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/CURENT/demo/blob/master/LICENSE)
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active)
[![GitHub last commit (master)](https://img.shields.io/github/last-commit/CURENT/demo/master?label=last%20commit%20to%20master)](https://github.com/CURENT/demo/commits/master/)

# Examples

## Advanced Usage

- [ANEDS: Stochastic Disturbance](./demo/andes_stochastic/andes_stochastic.ipynb)
- [ANDES: Interface Using Pertubation File](./demo/interface_andes/interface_andes.ipynb)
- [ANDES-AMS: Detailed Secondary Frequency Reulation](https://ltb.readthedocs.io/projects/ams/en/stable/_examples/demo/demo_AGC.html)
- [ANDES-AMS: Frequency Response](./demo/freq_response/freq_response.ipynb): Do a transient stability simulation at a given operation point.

## Simulations

- [AMS: Texas 7k Bus Case](./demo/texas7k/): Run a series of DCOPF using an external synthetic case.
- [ANDES: Forced Oscillation](./demo/forced_oscillation/forced_oscillation.ipynb): Use ANDES to simulate a forced oscillation in Kundur 4-machine 2-area system.
- [ANDES: TurbineGov's Response](./demo/TurbineGov_response/TurbineGov_reponse.ipynb)
- [ANDES: Debug of TurbineGov's Response](./demo/TurbineGov_response/debug.ipynb)
- [ANDES: Damped Oscillation](./demo/oscillation/oscillation.ipynb)
- [ANDES: Equivalent Inertia](./demo/equivalent_inertia/equivalent_inertia.ipynb)
- [ANDES: Voltage Sag](./demo/misc/voltage_sag.ipynb)
- [ANDES: Comparison of TGOV1 Variants](./demo/TGOV1/TGOV1_variants.ipynb)
- [ANDES: Imapcts of BusFreq Parameters](./demo/misc/busfreq.ipynb)
- [ANDES: Alter Load](./demo/misc/alter_load.ipynb)
- [ANDES: Use Output Select to Save Memory](./demo/misc/output_select.ipynb)
- [ANDES: Inspect Bus Injection Power](./demo/misc/andes_bus_injection.ipynb)
- [ANDES: Bus Admittance Matrix](./demo/misc/bus_admittance.ipynb)

## Benchmark

- [AMS Benchmark](./demo/ams_benchmark/plot/bench_plot.ipynb)
- [Power Flow Benchmark](demo/pflow_benchmark/bench_pflow.ipynb)

## Debug

- [ANDES: WTDTA1 Debug](./demo/misc/WTDTA1.ipynb)
- [ANDES: Comparison of TGOV1 Variants](./demo/TGOV1/TGOV1_variants.ipynb)
- [ANDES: Fix TDS Initialization Error](./demo/misc/andes_tds_init.ipynb)
- [ANDES: Ineffectiveness of ``REGCA1.u``](./demo/misc/REGCA1_u.ipynb)

# Installation

A conda environment is provided for easy installation. To create the environment named "ltb", run:

```bash
conda env create -f environment.yml -n ltb
```

To activate the environment, run:

```bash
conda activate ltb
```

# License
This repository is licensed under the [MIT License](./LICENSE), unless specified otherwise in subdirectories.
