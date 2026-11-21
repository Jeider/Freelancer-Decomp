"""B04/04 static volume review, using the actual exported surface geometry."""
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import bw_elite_b04_blender as review
review.OUT=HERE.parents[1]/'out/ship_design/bw_family/elite/prototypes/b04_04'
review.FORM_ONLY=True
review.REAR_PRIORITY=True
review.main()
