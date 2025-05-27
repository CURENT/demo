# Frequency Control Deadband

## Test Cases

``IL200_opf.xlsx`` and ``IL200_dyn.xlsx`` are revised from reference [1].

Illinois 200-Bus System: ACTIVSg200

URL: <https://electricgrids.engr.tamu.edu/electric-grid-test-cases/activsg200/>

References:

1. A.B. Birchfield, T. Xu, K.M. Gegner, K.S. Shetye, and T.J. Overbye, “Grid Structural
   Characteristics as Validation Criteria for Synthetic Networks,” IEEE Transactions on
   Power Systems, vol. 32, no. 4, pp. 3258-3265, July 2017.

Below list some changes to the case files:
1. ``IL200_opf2.xlsx``: based on ``IL200_opf.xlsx``, revise generator cost data
1. ``IL200_dyn_new.xlsx``: based on ``IL200_dyn.xlsx``, replace model TGOV1 with TGOV1NDB; add model ACEc
1. ``IL200_dyn_db.xlsx``: based on ``IL200_dyn_new.xlsx``, replace some GENROU with Wind, PV,
   and Energy Storage
1. ``IL200_dyn_db2.xlsx``: based on ``IL200_dyn_db.xlsx``, offline devices in GENROU, TGOV1NDB, and SEXS
   are removed

## Data

Data files are synthsized by Zelei Han: ``DataLoad.xlsx``, ``DataPV.xlsx``, and ``DataWind.xlsx``.

The individual datasets are merged into a single file, ``Curve.csv``, which contains load, PV, and
wind data combined at a one-minute resolution, for one day, as scaled factor.

Then, the data is interpolated to a one-second resolution, plus normal distribution noise, for one day, and saved as ``CurveInterp.csv``.

## Assumptions

In this study, following assumptions are made:
1. Each bus hosts at most one static generator and one dynamic generator
1. Regulation capacity is not optimized in the RTED process
1. Area Control Error (ACE) is assumed to be fully regulated

## Results

The results in ``./demo/deadband/results/`` are not guranteed to be up-to-date

## LICENSE

The code within this subdirectory (`./demo/deadband`) is proprietary and all rights are reserved by Jinning Wang.
