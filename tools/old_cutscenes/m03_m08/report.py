"""Summarize scope, unchanged working dialogue, and literal master defects."""
import ast
import json
from inventory import OUT, PL

inventory = json.loads((OUT / 'inventory.json').read_text())
working = {}
for mission in range(3, 9):
    path = PL / f'story/scripts/main/mission{mission}.py'
    tree = ast.parse(path.read_text(encoding='utf-8-sig'))
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef):
            continue
        alias = next((ast.literal_eval(n.value) for n in cls.body if isinstance(n, ast.Assign) and
                      any(isinstance(t, ast.Name) and t.id == 'ALIAS' for t in n.targets)), None)
        if alias is None:
            continue
        lines = {ast.literal_eval(n.args[0]): dict(actor=n.args[1].id,
                 ru=next(ast.literal_eval(k.value) for k in n.keywords if k.arg == 'ru'))
                 for n in ast.walk(cls) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'VoiceLine'}
        working[f'm{mission:02}_{alias}'] = dict(cls=cls.name, path=str(path), lines=lines)

reports, mismatches = {}, {}
for name in inventory['scenes']:
    spec = json.loads((OUT / name / 'spec.json').read_text(encoding='utf-8'))
    check = json.loads((OUT / name / 'check.json').read_text())
    reports[name] = dict(spec=spec, check=check)
    differences = []
    for line in spec['dialogue']:
        current = working.get(line['prefix'], {}).get('lines', {}).get(line['index'])
        if current is None:
            differences.append(dict(prefix=line['prefix'], index=line['index'], reason='missing_working_line',
                                    master_actor=line['actor'], master_ru=line['ru']))
        elif current['actor'] != line['actor'] or current['ru'] != line['ru']:
            differences.append(dict(prefix=line['prefix'], index=line['index'], reason='working_line_changed',
                                    master_actor=line['actor'], working_actor=current['actor'],
                                    master_ru=line['ru'], working_ru=current['ru']))
    if differences:
        mismatches[name] = differences
(OUT / 'working_script_mismatches.json').write_text(json.dumps(mismatches, indent=2, ensure_ascii=False), encoding='utf-8')
total_lines = sum(r['check']['master_lines'] for r in reports.values())
total_actions = sum(r['check']['master_actions_checked'] for r in reports.values())
body = [
    '# M03–M08: RTC из master в native Pythonlancer', '',
    f'Источник: `master` `{inventory["commit"]}`. Выбраны 43 сцены через 37 ссылок `Act_AddRTC` / `rtc.add`.',
    'Отбор подтверждён в [inventory.json](inventory.json). `CallThorn` не участвовал в отборе; его отдельные камеры не переписывались и не дампились.', '',
    f'Перенесены {total_lines} реплик и {total_actions} прочих событий, включая исходный повтор START_SOUND в M03 accept. '
    'Новый код использует Scene, Character, камеры и типизированные события native API. '
    'В этих 43 модулях нет preserve, source_extensions, ReconstructedScene и подмены get_thorn.', '',
    'Для каждой сцены подготовлены свой `.blend` и снятый после повторного открытия `.json`. '
    'Точки перемещения персонажей используют тот же mesh, что и персонаж. '
    'Сохранены master-позиции, ориентации, в том числе отражённые матрицы, масштабы, костюмы и Actor-привязки. '
    'Новые файлы отмечены `export_point_scale`; обычный dumper сохраняет для них масштаб. '
    'Экспорт старых blend без этой отметки работает как прежде.', '',
    'Реплики не сокращались и не сочинялись. Все существующие VOICE_LINES и их параметры оставлены без изменений. '
    'Добавлены шесть отсутствовавших привязок RTC без новых реплик: barman, vendor_hatcher, vendor_alaric, lab_launch, omicron_major, tau_arrival. '
    'Tau arrival использует существующую реплику Omega13; M07 offer также использует существующий диалог M06 Freeport. '
    'Всего 43 прямые привязки и 43 записи реестра.', '',
    '## Проверка', '',
    'Сценарные данные и аудио для проверки взяты из master; только RU. THN рендерился в памяти для сравнения событий, '
    'финальные `.thn` и DATA не записывались. Игру не запускали. '
    'Проверены все события, свойства объектов, камеры, IK, движения, параметры путей и положительные паузы. '
    'Диалоговые сцены используют facial()/append_time; постановочные пролёты и старты — абсолютное время.', '',
    'Проверка совместимости подтвердила неизменный результат существующих M02 offer/accept/Jacobo/done и двух native M08: '
    'PrinceWales и Sprague. Их исходники, blend/dump и привязки защищены хешами при установке. '
    'См. [compatibility_check.json](compatibility_check.json).', '',
    '## Места для ручной правки', '',
    'Это перенос исходной постановки, а не подтверждение её работоспособности в игре. '
    'Следующие проблемы не исправлялись догадками:', '',
]
for name, r in reports.items():
    if r['check']['inherited_unresolved_references']:
        body.append(f'- `{name}`: в master нет определения ' + ', '.join('`' + n + '`' for n in r['check']['inherited_unresolved_references']) + '; ссылки оставлены буквально.')
body += ['', 'В master встречаются перекрывающиеся старые окна lipsync, зеркальные матрицы и несовпадение пола костюма/анимации. '
         'Они не заменялись другими действиями. Старые озвученные facial-клипы заменены native facial(); '
         'неозвученные исходные мимические события оставлены как явно заданные MotionEvent.', '',
         'После перевода диалогов на native clock следующие события начинаются после рассчитанного конца сцены. '
         'Они оставлены в коде для ручной правки:']
for name, r in reports.items():
    check = r['check']
    if check['events_past_scene_end']:
        body.append(f'- `{name}`: конец {check["duration"]:.3f} с; события ' +
                    ', '.join(f'{e[0]:.3f} с ({e[1]})' for e in check['events_past_scene_end']) + '.')
body += ['', 'При абсолютной постановке и аудио без отдельного facial-окна сохранён исходный порядок и интервалы; '
         'перекрытие аудио в M06 briefing и M07 omega13 отражено в покадровых отчётах.', '',
         f'В {len(mismatches)} сценах использованные master-реплики отличаются от текущих списков Pythonlancer. '
         'Подробно: [working_script_mismatches.json](working_script_mismatches.json). '
         'При генерации на текущем сценарии возможны отсутствующие индексы или несовпадение актёров; заглушек и запасных реплик нет.', '',
         '## Сцены', '', '| Сцена | Реплики master | Проверенные события | Native-класс |', '|---|---:|---:|---|']
for name, r in reports.items():
    body.append(f'| [{name}]({name}/{name}.py) | {r["check"]["master_lines"]} | {r["check"]["master_actions_checked"]} | `{r["spec"]["scene_class"]}` |')
body += ['', '## Файлы и воспроизведение проверки', '',
         'Установка authoring-файлов: `Assets/Pythonlancer/story/cutscenes/story_scenes/`, '
         '`Assets/SCENES/`, `Assets/SCENES/DUMPS/`. '
         'Сводный список и контрольные суммы: [install_plan.json](install_plan.json), после установки — `installed.json`.', '',
         'Инструменты: `tools/old_cutscenes/m03_m08/`. '
         'Порядок подготовки: inventory.py, prepare_api.py, build.py, blender.py через tools/blender_workspace.py, '
         'check.py, check_compatibility.py, install.py, verify_bindings.py. '
         'После установки check.py --installed проверяет установленные исходники на master RU fixture. '
         'Проверка не запускает single.py. Финальную генерацию делает пользователь.', '']
(OUT / 'README.md').write_text('\n'.join(body), encoding='utf-8')
print(f'Report: {total_lines} RU lines, {total_actions} actions, {len(mismatches)} scenes with changed working dialogue.')
