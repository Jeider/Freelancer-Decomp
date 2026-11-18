"""PCM/content checks for every RU line, with explicit hash-bound ASR reviews."""
import argparse
import difflib
import json
import re
from generate_courier_ru import OUT, ROOT, plan, sha, save, inspect


def words(text):
    text = text.lower().replace('ё', 'е')
    # Only orthographic ASR variants; preserve actual omissions/word changes.
    text = re.sub(r'\b(?:тренд|трэнт|трэнд)\b', 'трент', text)
    text = text.replace('груженн', 'гружен')
    for spelling, number in {'двумя': '2', 'двух': '2', 'двум': '2', 'пятью': '5',
                             'десятью': '10', 'десяти': '10', 'десять': '10',
                             'пятнадцати': '15', 'двадцатью': '20',
                             'тридцать': '30', 'шестьдесят': '60'}.items():
        text = re.sub(r'\b'+spelling+r'\b', number, text)
    return re.findall(r'[а-яa-z0-9]+', text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--partial', action='store_true')
    args = parser.parse_args()
    records = json.loads((OUT/'recordings.json').read_text(encoding='utf-8'))
    transcript_path = OUT/'transcriptions.json'
    ledger = json.loads(transcript_path.read_text(encoding='utf-8')) if transcript_path.exists() else {}
    review_path = OUT/'asr_reviews.json'
    reviews = json.loads(review_path.read_text(encoding='utf-8')) if review_path.exists() else {}
    report = dict(recordings_sha256=sha(OUT/'recordings.json'), unresolved=[], differences={}, count=0,
                  seconds=0, bar=0, radio=0, vocabulary=0, evacuation=0,
                  validation='PCM/hash/level/duration and Russian ASR content comparison; no in-game audition or THN build')
    for row in plan():
        record = records.get(row['id'])
        if record and not record.get('asr') and ledger.get(row['id'],{}).get('sha256')==record['sha256']:
            record = {**record, 'asr':ledger[row['id']]['asr']}
        if record is None or 'asr' not in record:
            if not args.partial:
                report['unresolved'].append(row['id']+':missing_audio_or_asr')
            continue
        assert record['text'] == row['text']
        path = OUT/row['bank']/(row['id']+'.wav')
        if args.partial and sha(path) != record['sha256']:
            continue  # The repair worker is replacing this take right now.
        assert sha(path) == record['sha256'], row['id']
        info = inspect(path)
        assert abs(info['duration']-record['duration']) < .000001
        if row['id'].startswith('te_return_10_'):
            assert info['duration'] < 8
        report['count'] += 1
        report[row['bank']] += 1
        report['seconds'] += info['duration']
        expected, heard = words(row['text']), words(record['asr'].get('text',''))
        if expected != heard:
            review = reviews.get(row['id'], {})
            accepted = review.get('sha256') == record['sha256'] and bool(review.get('reason'))
            report['differences'][row['id']] = dict(expected=row['text'], asr=record['asr'].get('text'),
                changes=[word for word in difflib.ndiff(expected,heard) if not word.startswith('  ')], reviewed=accepted)
            if not accepted:
                report['unresolved'].append(row['id'])
    source = '\n'.join((ROOT/name).read_text(encoding='utf-8') for name in
        ('src/Content/TrainCourier.cpp', 'src/Content/TrainCourierEvacuation.inl'))
    hooks = set(re.findall(r'"(te_[a-z0-9_]+)"', source))
    families = {r['id'].rsplit('_',1)[0] for r in plan() if r['bank']=='evacuation'}
    assert hooks == families, (hooks-families, families-hooks)
    save(OUT/('verification_partial.json' if args.partial else 'verification.json'), report)
    print('Checked',report['count'],'clips;',round(report['seconds'],1),'seconds; unresolved:',len(report['unresolved']))
    for code in report['unresolved']:
        print(code, report['differences'].get(code, {}).get('changes', ''))
    if report['unresolved'] and not args.partial:
        raise SystemExit(1)


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
