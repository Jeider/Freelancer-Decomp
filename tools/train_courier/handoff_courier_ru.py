"""Export the user's manual-cutting handoff. No audio generation or game writes."""
import csv
import io
import json
from generate_courier_ru import OUT, ASSETS, plan, save


def main():
    report=json.loads((OUT/'verification.json').read_text(encoding='utf-8'))
    rows={r['id']:r for r in plan()}
    review=[]
    for code in report['unresolved']:
        row=rows[code]
        review.append(dict(id=code,text=row['text'],
            draft=str(OUT/row['bank']/(code+'.wav')),
            target=str(ASSETS/'PILOTS/dispatcher01/default'/(code+'.wav')),
            full_sentence=('Будьте добры, отвезите товар '+row['text']+' в точку Бисмарк.') if row['bank']=='vocabulary' else row['text'],
            keep=row['text'],asr=report['differences'][code]['asr']))
    save(OUT/'manual_review.json',review)
    with (OUT/'manual_review.tsv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['id','text','draft','target','full_sentence','keep','asr'],delimiter='\t')
        writer.writeheader();writer.writerows(review)
    save(OUT/'join_prototypes.json',dict(
        example='Будьте добры, отвезите товар [название товара] в точку [название базы].',
        same_sequence_as_en=['tc_order_NN+','commodity.msg_id_prefix','tc_destination_NN+',
                             'base.voice_name','tc_collect_NN-'],
        names='Именительный падеж; готовые записи вставляются без изменения.',
        manual_prompts=[
            dict(id='tc_order',full_sentence='Будьте добры, отвезите товар Простой сплав в точку Бисмарк.',keep='Будьте добры, отвезите товар'),
            dict(id='tc_destination',full_sentence='Будьте добры, отвезите товар Простой сплав в точку Бисмарк.',keep='в точку'),
        ],note='Текстовые прототипы для ручной нарезки. Это не утверждение о наличии новых дублей этих точных фраз.'))
    installed_path = OUT/'installed.json'
    connected_path = OUT/'scenes/connected.json'
    status = 'Исходники опубликованы; DATA/bin ещё не установлены.'
    bar_status = 'Финальные THN собирает пользователь через `python -B single.py rpg scenes --group rm0001 --language ru`.'
    if installed_path.exists():
        installed = json.loads(installed_path.read_text(encoding='utf-8'))
        status = (f"В игру установлены и проверены {installed['lines']} RU-записей, Content.dll и клиент. "
                  'Выбор PortVoice: RU → dispatcher01, EN → atc_leg_m01_new. '
                  f"Для {len(installed['missing_cargo'])} товаров временно пропускаются название и его вводная часть; "
                  'диспетчер сообщает пункт назначения, а товар виден в тексте. '
                  'После ручной записи положить WAV в указанный target и повторить stage --available / apply: '
                  'установщик возьмёт канонический исходник и уберёт его из unvoiced_cargo. '
                  '`installed.json` содержит точные хеши; установочные копии бинарников удалены.')
    if connected_path.exists():
        bar_status = ('По явному разрешению пользователя «собирай» собраны и установлены 32 RU-сцены бара через single.py. '
                      'Длительности WAV, события мимики и хеши проверены; привязки подключены у 19 торговых управляющих. '
                      'EN-сцены сохранены. Отчёты: `scenes/verified.json`, `scenes/connected.json`. '
                      'Игра агентом не запускалась; проверка восприятия в игре остаётся пользователю.')
    if (OUT/'bank_installed.json').exists():
        status += (' Важное исправление: dispatcher01 использует UTF и игнорирует file= в INI. '
                   '236 новых записей упакованы в dispatcher01.utf; 456 старых записей сохранены. '
                   'Повторная установка теперь также пересобирает UTF. Проверка: `bank_installed.json`.')
    if (OUT/'file_export/published.json').exists():
        status += (' Последующее решение пользователя отменяет сборку UTF: подготовлен экспорт русских диспетчеров в отдельные WAV. '
                   'Скрипты Pythonlancer установлены, но игровые INI и UTF агент не менял. '
                   'Пользователь запускает `python -B single.py compile_dispatchers_audio` '
                   '(предварительная проверка: добавить `--dry-run`). '
                   '`compile_pilots_ini` и `compile_pilots_audio` также используют этот экспорт. '
                   'UTF удаляется только после проверки WAV/INI; исходные записи сохраняются в папках, включая archive/. '
                   'Проверка сбоев/отката и полного набора: `file_export/validation.json`.')
    if (OUT/'file_export/installed.json').exists():
        status = ('По прямому запросу пользователя команда `single.py compile_dispatchers_audio` выполнена агентом. '
                   'Русские dispatcher01/02/03 теперь используют отдельные WAV: 673/437/437 записей. '
                   'Пути в игровых INI обновлены, три одноимённых UTF удалены после проверки. '
                   'Все исходные записи сохранены отдельно; EN и остальные голоса не менялись. '
                   'Проверены все 236 реплик/названий грузовых перевозок и 76 названий баз. '
                   'Обычные compile_pilots_ini и compile_pilots_audio используют ту же схему. '
                   'Итоговая проверка: `file_export/installed.json`.')
    if (OUT/'voice_match/updated.json').exists():
        status += (' После подтверждения пользователем нового тембра заменены все 195 новых космических реплик '
                   '(130 команд и 65 реакций после эвакуации). Использован единый чистый образец dispatcher01 '
                   'длительностью 9,08 с; OmniVoice, 128 шагов, guidance_scale=3.0, скорость 1.0. '
                   'Три одобренных WAV сохранены без повторной генерации. '
                   'Обновлены исходники PILOTS, образец MaleDispatcher и игровые WAV/длительности через Pythonlancer. '
                   'Настройки сохранены в MaleDispatcher.json и используются generate_courier_ru.py. '
                   'Исторический preview_space.wav относится к прежнему голосу; одобренный пример — '
                   '`voice_match/comparison.wav`, точные новые хеши — `voice_match/updated.json`.')
    (OUT/'README.md').write_text(f'''# Русская озвучка грузовых перевозок

Стадия: игровые реплики и исходники для ручной доработки. Автоматическая дорезка остановлена по уточнению пользователя.

- Записано 277 файлов: 32 для бара, 130 команд рейса, 65 реплик эвакуации, 50 названий товаров.
- Первичная публикация в `Assets`: 266 прошедших проверку записей и три RU-образца. При установке добавлены два разговорных прототипа с мелким расхождением ASR; девять неудачных названий товаров остаются вне игрового банка.
- `manual_review.tsv` / `manual_review.json`: точные тексты, спорная расшифровка, черновой WAV, имя итогового файла и полная фраза для ручной нарезки.
- `join_prototypes.json`: простая схема пользователя и примеры полных фраз. Названия товаров и баз не склоняются.
- `preview_bar.wav`: Трент и торговый управляющий. `preview_space.wav`: диспетчер, сборная команда с названием товара и базы, доставка и одна реплика после эвакуации. Оба примера без запечённого радиофильтра.
- `references/manifest.json`: происхождение образцов и хеши. Трент взят из RU-сюжетки M01; диспетчер — из чистых исходников PILOTS. Профили VoiceStudio: `nl-Trent-ru`, `nl-MaleDispatcher-ru`, `nl-RpgTradeDirector-ru`.
- Канонические исходники: `D:/Games/FL_MOD/Assets/AUDIO_CUTSCENE_RU/rm0001`, `PILOTS/dispatcher01/default`, `VOICE_SOURCE_RU`. Английские исходники сохранены.
- Сборка сообщений повторяет EN: вступление → неизменяемое название товара → связка → неизменяемое название базы → инструкция. Уже существующие 76 названий баз остаются из русского архива диспетчера.

{status}

{bar_status}
''',encoding='utf-8')
    print('Manual handoff:',len(review),'takes;',OUT/'manual_review.tsv')


if __name__=='__main__':
    main()
