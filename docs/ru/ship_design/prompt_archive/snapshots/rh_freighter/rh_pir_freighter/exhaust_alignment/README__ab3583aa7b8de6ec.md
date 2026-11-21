# rh_pir_freighter: точки выхлопа у сопел

Только три HP: HpEngine01, HpEngine02 и общая HpEngineGlow. Зазор до решётки — 0,005.
Взяты текущие принятые игровые CMP; все остальные HP сохранены побайтно.
Геометрия, UV, LOD, анимация и вайрфрейм идентичны. Для экспортов создана новая соль.
SUR сохраняется: у этих трёх точек нет встроенных коллизионных оболочек.

| HP | Было X/Y/Z | Стало X/Y/Z |
|---|---|---|
| hpengine01 | -1.848702, -0.449315, 11.400277 | -1.800000, -0.280000, 11.155000 |
| hpengine02 | 1.836763, -0.449315, 11.400274 | 1.800000, -0.280000, 11.155000 |
| hpengineglow | 0.031026, -0.449315, 16.838787 | -0.000000, -0.280000, 11.155000 |

## Файлы

- [D:/games/FL_MOD/DATA/SHIPS/RHEINLAND/RH_PIR_FREIGHTER/rh_pir_freighter.cmp](D:/games/FL_MOD/DATA/SHIPS/RHEINLAND/RH_PIR_FREIGHTER/rh_pir_freighter.cmp)
- [D:/work/Freelancer-Decomp/out/ship_design/rh_freighter/rh_pir_freighter/exhaust_alignment/rh_pir_freighter_review_open.cmp](D:/work/Freelancer-Decomp/out/ship_design/rh_freighter/rh_pir_freighter/exhaust_alignment/rh_pir_freighter_review_open.cmp)

Установлено по прямому запросу пользователя. Хеш CMP проверен. Конфиги и материалы не менялись.
При следующей полной сборке использовать обновлённый review_open как источник HP.
Для freighter также обновлены канонический CMP и его manifest в Pythonlancer.

Установочный CMP удалён после проверки; редактируемый review_open сохранён. Отчёт: installation.json.
