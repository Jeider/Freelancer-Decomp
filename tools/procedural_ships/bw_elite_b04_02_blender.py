"""Render and save the second B04 form study, using its exported triangle data."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bw_elite_b04_blender as review

review.OUT=HERE.parents[1]/'out/ship_design/bw_family/elite/prototypes/b04_02'
review.FORM_ONLY=True
review.main()
