"""Check ready RU recordings while the generator runs; separate hash-bound ledger."""
import argparse
import json
import time
from generate_courier_ru import OUT, plan, sha, save, transcribe
from check_courier_ru import words


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--merge', action='store_true', help='Only after generation is finished')
    args = parser.parse_args()
    ledger_path = OUT/'transcriptions.json'
    ledger = json.loads(ledger_path.read_text(encoding='utf-8')) if ledger_path.exists() else {}
    rows = plan()
    if args.merge:
        records = json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
        for row in rows:
            record = records[row['id']]
            if record.get('asr'):
                # A later repaired take was transcribed by the generator itself.
                continue
            entry = ledger[row['id']]
            assert entry['sha256'] == record['sha256']
            record['asr'] = entry['asr']
        save(OUT/'recordings.json', records)
        print('Merged', len(rows), 'hash-matched transcriptions')
        return
    last_progress = time.monotonic()
    while True:
        records = json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
        missing = []
        for row in rows:
            code = row['id']
            record = records.get(code)
            if not record:
                missing.append(code)
                continue
            if ledger.get(code, {}).get('sha256') == record['sha256']:
                continue
            path = OUT/row['bank']/(code+'.wav')
            if sha(path) != record['sha256']:
                missing.append(code)
                continue
            result = record.get('asr') or transcribe(path)
            if sha(path) != record['sha256']:
                missing.append(code)
                continue
            ledger[code] = dict(sha256=record['sha256'], asr=result)
            save(ledger_path, ledger)
            last_progress = time.monotonic()
            differs = words(row['text']) != words(result.get('text', ''))
            print(f'[{len(ledger)}/{len(rows)}] {code}' + (' REVIEW: ' + result.get('text', '') if differs else ' OK'), flush=True)
        if not missing:
            break
        assert time.monotonic() - last_progress < 180, 'No new recordings for three minutes: '+str(missing[:5])
        time.sleep(3)
    print('Transcription ledger complete. Merge after generation stops.', flush=True)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
