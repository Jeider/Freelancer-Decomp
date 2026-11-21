# rh_pir_fighter: точки выхлопа у сопел

Только три HP: HpEngine01, HpEngine02 и общая HpEngineGlow. Зазор до решётки — 0,005.
Взяты текущие принятые игровые CMP; все остальные HP сохранены побайтно.
Геометрия, UV, LOD, анимация и вайрфрейм идентичны. Для экспортов создана новая соль.
SUR сохраняется: у этих трёх точек нет встроенных коллизионных оболочек.

| HP | Было X/Y/Z | Стало X/Y/Z |
|---|---|---|
| hpengine01 | -1.813985, -1.444458, 5.115000 | -1.813986, -1.444458, 4.590000 |
| hpengine02 | 1.813985, -1.444458, 5.115000 | 1.813986, -1.444458, 4.590000 |
| hpengineglow | 0.000000, -1.444458, 5.115000 | -0.000000, -1.444458, 4.590000 |

## Файлы

- [D:/games/FL_MOD/DATA/SHIPS/RHEINLAND/RH_PIR_FIGHTER/rh_pir_fighter.cmp](D:/games/FL_MOD/DATA/SHIPS/RHEINLAND/RH_PIR_FIGHTER/rh_pir_fighter.cmp)
- [D:/work/Freelancer-Decomp/out/ship_design/rh_fighter/rh_pir_fighter/exhaust_alignment/rh_pir_fighter_review_open.cmp](D:/work/Freelancer-Decomp/out/ship_design/rh_fighter/rh_pir_fighter/exhaust_alignment/rh_pir_fighter_review_open.cmp)

Установлено по прямому запросу пользователя. Хеш CMP проверен. Конфиги и материалы не менялись.
При следующей полной сборке использовать обновлённый review_open как источник HP.
Для freighter также обновлены канонический CMP и его manifest в Pythonlancer.

Установочный CMP удалён после проверки; редактируемый review_open сохранён. Отчёт: installation.json.
