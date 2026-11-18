"""Re-record confirmed ASR mismatches; retain old metadata, never old binary takes."""
import argparse
import json
import subprocess
import sys
from generate_courier_ru import OUT, ROOT, plan, save
from check_courier_ru import words


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ids',nargs='+')
    parser.add_argument('--attempts',type=int,default=3)
    args=parser.parse_args()
    records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    assert len(records)==len(plan()), 'Let the main generator finish before repairing takes'
    ledger=json.loads((OUT/'transcriptions.json').read_text(encoding='utf-8'))
    history_path=OUT/'repair_history.json'
    history=json.loads(history_path.read_text(encoding='utf-8')) if history_path.exists() else {}
    review_path=OUT/'asr_reviews.json'
    reviews=json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else {}
    selected=[]
    for row in plan():
        code=row['id']
        if args.ids and code not in args.ids:
            continue
        record=records[code]
        if reviews.get(code,{}).get('sha256')==record['sha256'] and reviews[code].get('reason'):
            continue
        asr=record.get('asr') or (ledger.get(code,{}).get('asr') if ledger.get(code,{}).get('sha256')==record['sha256'] else None)
        if asr and words(row['text'])!=words(asr.get('text','')):
            selected.append(code)
    print('Repairing',len(selected),'takes',flush=True)
    for code in selected:
        for attempt in range(args.attempts):
            record=records[code]
            history.setdefault(code,[]).append(dict(sha256=record['sha256'],seed=record['seed'],
                asr=record.get('asr') or ledger.get(code,{}).get('asr'),reason='ASR wording mismatch'))
            save(history_path,history)
            subprocess.run([sys.executable,'-X','utf8','-B',str(ROOT/'tools/train_courier/generate_courier_ru.py'),
                            '--ids',code,'--seed',str(record['seed']+1),'--steps','128','--transcribe'],check=True)
            records=json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
            record=records[code]
            if words(record['text'])==words(record['asr'].get('text','')):
                print('REPAIRED',code,flush=True)
                break
        else:
            print('STILL NEEDS REVIEW',code,record['asr'].get('text',''),flush=True)


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
