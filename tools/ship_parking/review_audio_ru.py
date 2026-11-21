"""Explicit, hash-bound review of spelling ambiguities and named prototypes."""
import csv
from audio_ru import OUT, ASSETS, read, save, check

# These decisions concern the recorded proper names, not generic message words.
# No entry claims an independent human audition of the WAV.
NOTES = {
    'rm0122_frag0020': (False, 'Дуарте/Дуарти: запись безударного конечного гласного; остальная фраза совпадает.'),
    'rm0117_frag0020': (False, 'Хейз/Хейс: оглушение конечного з; остальные слова совпадают.'),
    'rm0124_frag0001': (False, 'Питсбург/Питтсбург: вариант написания удвоенной согласной в названии.'),
    'rm0124_frag0005': (False, 'Питсбург/Питтсбург: вариант написания удвоенной согласной в названии.'),
    'rm0124_frag0011': (False, 'Питсбург/Питтсбург: вариант написания удвоенной согласной в названии.'),
    'rm0140_frag0001': (False, 'Маркграф/Марк Граф: ASR разделил одно название на два слова.'),
    'rm0140_frag0005': (True, 'Маркграф/Марграф: согласный стык кг не подтверждён распознаванием; нужна прослушка названия.'),
    'rm0140_frag0011': (True, 'Маркграф/Марграф: согласный стык кг не подтверждён распознаванием; нужна прослушка названия.'),
    'rm0107_frag0020': (False, 'Крус/Круз: совпадающее звучание из-за оглушения конечного з.'),
    'rm0114_frag0020': (False, 'Като/Ката: безударное конечное о распознано как а; остальные слова совпадают.'),
    'rm0122_frag0011': (True, 'Монтгомери/Монтгомерии: ASR неоднозначно передаёт окончание; оставлен прототип для прослушки.'),
    'rm0110_frag0020': (False, 'Серрано/Серано: ASR не удвоил согласную фамилии; остальные слова совпадают.'),
    'rm0123_frag0011': (False, 'Манхеттен/Манхэттен: орфографический вариант заимствованного названия.'),
    'rm0106_frag0011': (False, 'Лион/Леон: неоднозначное написание безударного первого гласного в названии.'),
    'rm0108_frag0020': (False, 'Наварро/Навара: ASR передал безударное о как а и не удвоил р.'),
    'rm0115_frag0020': (False, 'Абэ/А.Б.: короткое имя распознано как инициалы; дополнительный дубль дал написание Абе.'),
    'rm0153_frag0020': (False, 'Окада/Акада: безударное начальное о распознано как а.'),
    'rm0103_frag0020': (True, 'Хоторн/Хоттерн: редкая фамилия остаётся неоднозначной после повторов; прототип для прослушки.'),
    'rm0100_frag0001': (True, 'Очо-Риос: ASR передаёт название неоднозначно; варианты с ударениями не приняты. Сохранён исходный прототип.'),
    'rm0100_frag0005': (True, 'Очо-Риос: ASR передаёт название неоднозначно; варианты с ударениями не приняты. Сохранён исходный прототип.'),
    'rm0100_frag0011': (True, 'Очо-Риос: ASR передаёт название неоднозначно; варианты с ударениями не приняты. Сохранён исходный прототип.'),
    'rm0109_frag0001': (True, 'Очо-Риос: ASR передаёт название неоднозначно; варианты с ударениями не приняты. Сохранён исходный прототип.'),
    'rm0110_frag0001': (True, 'Очо-Риос: ASR передаёт название неоднозначно; варианты с ударениями не приняты. Сохранён исходный прототип.'),
}


def main():
    plan, records = check()
    verified = read(OUT / 'verification.json')
    names = read(OUT / 'name_recognition.json')
    reviews, manual = {}, []
    for key, row in verified['differences'].items():
        first = row['uses'][0]
        assert first in NOTES, 'Review new difference explicitly: ' + first
        listen, reason = NOTES[first]
        reviews[key] = {'sha256': row['sha256'], 'reason': reason, 'needs_listening': listen,
                        'kind': 'pronunciation_prototype' if listen else 'spelling_review'}
        if listen:
            for fragment in row['uses']:
                group = fragment.split('_frag')[0]
                manual.append({'id': fragment, 'text': row['text'], 'note': reason,
                    'asr': names.get(key, {}).get('asr', {}).get('text', row['asr']),
                    'source': str(OUT / 'recordings' / (key + '.wav')),
                    'target': str(ASSETS / 'AUDIO_CUTSCENE_RU' / group / (fragment + '_l001_vendor.wav'))})
    save(OUT / 'asr_reviews.json', reviews)
    save(OUT / 'manual_review.json', manual)
    with (OUT / 'manual_review.tsv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id','text','note','asr','source','target'], delimiter='\t')
        writer.writeheader()
        writer.writerows(manual)
    check(complete=True)
    print('Reviewed', len(reviews), 'ASR differences;', sum(r['needs_listening'] for r in reviews.values()),
          'unique name prototypes for audition;', len(manual), 'per-group files')


if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
