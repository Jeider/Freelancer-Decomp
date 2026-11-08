"""Write the English dialogue recording package only. No audio/build/install."""
from pathlib import Path
import ast
import csv
import io
import json
import zipfile

from dispatcher_en import VOICE, FOLDER, FAMILIES, clips, voice_properties

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/train_courier/dispatcher_en01_recording'

RECIPES = {
    'new_order': ['tc_order_<01..10>+', '{cargo_good_msg_id_prefix}',
                  'tc_destination_<01..10>+', '{destination_base_voice_name}', 'tc_collect_<01..10>-'],
    'coupled_or_recoupled': ['tc_depart_<01..10>+', '{destination_base_voice_name}'],
    'boarding': ['tc_board_<01..10>-'],
    'arrival': ['tc_arrival_<01..10>-'],
    'payment': ['tc_paid_<01..10>-'],
    'continue_question': ['tc_continue_<01..10>-'],
    'lost_cargo': ['tc_recover_<01..10>-'],
    'parking': ['tc_park_<01..10>+', '{planet_base_voice_name}'],
    'finished': ['tc_done_<01..10>-'],
}

README = '''ENGLISH FREIGHT DISPATCHER — RECORDING PACKAGE

Voice asset folder: dispatcher_en01
In-game voice: atc_leg_m01_new
Existing Pythonlancer actor: EngMaleDispatcher (STEOS_ID 294).
Use the same voice as its existing base-name recordings.

Generate ONLY the 110 rows in recording.tsv (or the same rows in lines.json).
One row = one clip. Filename = exact ID + .wav, including the trailing + or -.
Do not speak IDs, filenames, headings or placeholders. Text is in English.
Tone: calm, capable freight dispatcher; conversational, clear instructions.
Do not add a radio filter: match the existing voice assets and game processing.

JOINING THE CLIPS
Clips ending in + continue a sentence: do not add a full-stop cadence, a long
tail or a dramatic pause. The next clip is a cargo name or a destination name.
Clips ending in - finish a sentence. Their punctuation is intentional.
Keep loudness, distance, pacing and character consistent across all takes.
Each family has 10 interchangeable takes. The game picks one, not all ten.

Example of the first order (brackets denote existing clips, never new audio):
We have an order for [PYTHONLANCER CARGO] for delivery to [DESTINATION BASE].
Collect the cargo at the marked waypoint. Bring the rear of your locomotive
close to the wagons' coupling point, then use the coupling manoeuvre to attach
the train.

After coupling:
Coupling confirmed. Deliver this shipment to [DESTINATION BASE].

NAMES — DO NOT GENERATE THEM FROM THIS PACKAGE
The user supplies commodity vocabulary through Pythonlancer inheritance.
Only goods in core.store.get_commodities() are eligible; retail goods are excluded.
Use the native pilot lookup: TranslateGoodToMsgIdPrefix(good_id), then that exact
clip ID. Do not append +, -, or _01 to commodity names. Example of a mod good:
comm_basic_meds -> gcs_gen_commodity_comm_basic_meds.
The + suffix belongs to the surrounding variable sentence fragments.
Base clips use the catalog's voice_name, including its existing suffix.
Current courier orders carry ONE commodity type per consist. We name that actual
cargo, not a list of possible goods. Mixed-cargo orders are not implemented.
This package contains no base names, commodity recordings or inherited vocabulary.

PYTHONLANCER
courier_lines_en.py exports COURIER_LINES as PilotLine objects (the L(...) format).
Merge these into the English dispatcher's LINES, preserving its existing lines
and your inheritance for names. This module does not change inheritance or
register another dispatcher. voice_properties.ini goes into the existing
atc_leg_m01_new mVoiceProp definition; do not create duplicate count entries.

DELIVERY
Return the generated WAVs named exactly as in recording.tsv. Sound entries must
use actual measured WAV durations; no guessed durations are included here.
Intended game folder: DATA/Audio/MOD_ENG/dispatcher_en01/.
Keep audio_enabled = false until the clips and inherited names are available.
No audio is generated or installed by this script. No binaries are built.

ENGINE EVENTS
A new order always names its actual cargo and recipient, then explains pickup.
Successful coupling confirms the route and names the recipient again.
Detachment outside the delivery zone requests recovery of the same wagons.
Delivery instructions ask for a stopped, uncoupled consist at the marker.
Payment is announced only after crediting the player. The continuation popup
waits for the question's CommComplete event, not a fixed six-second timeout.
NO leads to parking at a friendly planet's docking fixture, then the personal
ship's launch from the locomotive. The parked locomotive denies re-docking.

Engine/config changes are source-only until the user authorizes the next build.
The full audio sequence still needs an in-game audition with generated clips.
'''


def main():
    records = list(clips())
    assert len(records) == 110 and len({code for code, _ in records}) == 110
    assert all(len(variants) == 10 for _, variants in FAMILIES.values())
    assert all(len(recipe) <= 16 for recipe in RECIPES.values())
    assert all(code.startswith('tc_') and '\t' not in text and '\n' not in text for code, text in records)
    OUT.mkdir(parents=True, exist_ok=True)
    table = io.StringIO(newline='')
    writer = csv.writer(table, delimiter='\t', lineterminator='\n')
    writer.writerow(['id', 'filename', 'text'])
    writer.writerows((code, code+'.wav', text) for code, text in records)
    module = ('# New English courier dialogue only; do not replace inherited vocabulary.\n'
              'from universe.audio.pilot_line import PilotLine as L\n\nCOURIER_LINES = [\n'+
              ''.join(f'    L({code!r}, {text!r}),\n' for code, text in records)+']\n')
    ast.parse(module)
    files = {
        'README.txt': README,
        'recording.tsv': table.getvalue(),
        'lines.json': json.dumps([dict(id=c, filename=c+'.wav', text=t) for c, t in records], ensure_ascii=False, indent=2)+'\n',
        'courier_lines_en.py': module,
        'voice_properties.ini': voice_properties(),
        'sequence.json': json.dumps(dict(voice=VOICE, folder=FOLDER, events=RECIPES), indent=2)+'\n',
    }
    for name, data in files.items():
        (OUT/name).write_text(data, encoding='utf-8')
    archive = OUT.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as package:
        for name in files:
            package.write(OUT/name, arcname=OUT.name+'/'+name)
    print(f'Prepared {len(records)} English clips, {len(FAMILIES)} families, no commodity/base names: {archive}')


if __name__ == '__main__':
    main()
