"""Stable ship-design topic, shared references, and the RH elite workspace."""
from pathlib import Path

TOPIC = Path(__file__).resolve().parents[2] / 'out/ship_design'
WORK = TOPIC / 'rh_elite'
ANALYSIS = TOPIC / 'analysis'
REFERENCES = TOPIC / 'references'
CONCEPTS = WORK / 'concepts'
PROTOTYPE_V1 = WORK / 'prototypes/v1'
PROTOTYPE_V2 = WORK / 'prototypes/v2'
CONCEPT_B_MODEL = WORK / 'prototypes/concept_b'
CONCEPT_B_DETAIL = CONCEPT_B_MODEL / 'revision_02'
CONCEPT_B_FORM = CONCEPT_B_MODEL / 'revision_03'
CONCEPT_B_PROFILE = CONCEPT_B_MODEL / 'revision_04'
CONCEPT_B_VOLUME = CONCEPT_B_MODEL / 'revision_05'
CONCEPT_B_ATTACHMENTS = CONCEPT_B_MODEL / 'revision_06'
CONCEPT_B_COMPACT = CONCEPT_B_MODEL / 'revision_07'
CONCEPT_B_SOCKETS = CONCEPT_B_MODEL / 'revision_08'
