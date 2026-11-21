"""Pin native references for the new, hand-authored Hassler upper costume."""
import json,hashlib,sys
from pathlib import Path
import hassler_prepare as old

OUT=old.OUT/'native_upper'
def main():
    previous=json.loads((old.OUT/'source_audit.json').read_text())
    for name,entry in previous['native'].items():
        assert hashlib.sha256(Path(entry['path']).read_bytes()).hexdigest()==entry['sha256'],name
    old.OUT=OUT;old.ASSETS={'wilham':'BODIES/rh_wilham_body.dfm'};old.main()
    current=json.loads((OUT/'source_audit.json').read_text());current['native'].update(previous['native'])
    current['approach']='Native rh_male_elite body, Reichman epaulettes, hand-authored Hassler art panels; Meshy geometry is not imported'
    current['step']='01 upper costume visual prototype; no installation'
    old.dump(OUT/'source_audit.json',current)

if __name__=='__main__':main()
