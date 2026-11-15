"""Stable layout and historical audit mapping for relocated station assets."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FOLDERS=('valensia_opt','valensia_mega','terraform_mega','potsdam_mega','ulster_megabase',
 'ulster_shortbase','ulster_shortsplit','stuttgart_mega','forbes_mega','cambridge_shipping_core',
 'corsair_four_docks','losangeles_two_docks','nansei_panel_rotor','odissey_eight_docks','odissey_five_docks')
def audit_paths(hashes):
    """Keep original validation manifests immutable; apply the verified relocation journal."""
    journal=ROOT/'out/optimized_stations/installed.json'
    if not journal.exists():return hashes
    data=json.loads(journal.read_text())
    result={data['moves'].get(n,n):h for n,h in hashes.items()}
    for n,change in data['configs'].items():
        if result.get(n)==change['before']:result[n]=change['after']
    return result
