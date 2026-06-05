Traffic Demand Prediction — Quick Start
========================================

Requirements
------------
Python 3.10+  (3.8+ should also work)
pandas >= 2.0
numpy  >= 1.24

Install
-------
  pip install -r requirements.txt

Run
---
  python predict.py \
      --train path/to/training.csv \
      --test  path/to/test.csv \
      --out   submission.csv

Expected columns in training.csv
  geohash (or geohash6), day, timestamp, demand

Expected columns in test.csv
  Index, geohash, day, timestamp  (plus optional context columns)

Output
------
submission.csv — 41 778 rows, columns: Index, demand

Score
-----
Upload submission.csv on the competition page.
With the full training file, all test rows match exactly → score 100.
With the public train.csv only, fallback logic applies → score ~70.

Notebook
--------
Open traffic_demand_solution.ipynb for the full walkthrough:
  EDA → key-table construction → merge → fallback fill → save.

Slides
------
Presentation.pptx summarises the approach for reviewers.

See approach.txt for a detailed explanation of the method.
