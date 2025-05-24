# Frequency Control Deadband

## Test Cases

``IL200_opf_db.xlsx`` and ``IL200_dyn_db.xlsx`` are revised from below reference.

Illinois 200-Bus System: ACTIVSg200

URL: <https://electricgrids.engr.tamu.edu/electric-grid-test-cases/activsg200/>

References:

1. A.B. Birchfield, T. Xu, K.M. Gegner, K.S. Shetye, and T.J. Overbye, “Grid Structural
   Characteristics as Validation Criteria for Synthetic Networks,” IEEE Transactions on
   Power Systems, vol. 32, no. 4, pp. 3258-3265, July 2017.

## Data

Data files are synthsized by Zelei Han: ``DataLoad.xlsx``, ``DataPV.xlsx``, and ``DataWind.xlsx``.

The individual datasets are merged into a single file, ``Curve.csv``, which contains load, PV, and
wind data combined at a one-minute resolution.

## LICENSE

The code within this subdirectory (`./demo/deadband`) is proprietary and all rights are reserved by Jinning Wang.
