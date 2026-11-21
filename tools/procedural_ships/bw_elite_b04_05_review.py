"""Validate and present the localized wing restoration."""
import html
import json
from pathlib import Path

import bw_elite_b04_03_review as common

OUT = Path(__file__).resolve().parents[2] / 'out/ship_design/bw_family/elite/prototypes/b04_05'


def main():
    common.OUT = OUT
    report = common.validate()
    views = [('form_top.png', 'Сверху — прежние крылья, широкий нос сохранён'),
             ('form_rear_34.png', 'Сзади 3/4'), ('form_front_34.png', 'Спереди 3/4'),
             ('form_side.png', 'Сбоку'), ('form_upper_rear_34.png', 'Верхний корпус крупно'),
             ('form_rear.png', 'Сзади'), ('form_belly.png', 'Снизу'),
             ('form_hold.png', 'Трюм, створки временно скрыты')]
    cards = '\n'.join(f'<figure><a href="{f}"><img loading="lazy" src="{f}" alt="{html.escape(c)}"></a>'
                      f'<figcaption>{html.escape(c)}</figcaption></figure>' for f, c in views)
    files = '\n'.join(f'<li><a href="{n}">{html.escape((OUT/n).as_posix())}</a></li>'
                      for n in ['bw_pir_elite_b04.blend', 'bw_pir_elite_b04_review_open.cmp', 'README.md'])
    page = '''<!doctype html><html lang="ru"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>B04 ELITE — форма 05</title>
<style>:root{color-scheme:dark}body{margin:0;background:#1b2126;color:#e3e7e9;font:16px/1.5 system-ui,sans-serif}
main{max-width:1480px;margin:auto;padding:26px}h1{font-size:29px;margin:0}h2{font-size:22px;margin:30px 0 12px}
p{max-width:1050px}a{color:#b8d9ec}figure{margin:0;background:#272e34;border:1px solid #414b53;border-radius:6px;overflow:hidden}
img{display:block;width:100%;height:auto}figcaption{padding:9px 14px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:16px}
li{overflow-wrap:anywhere;margin:8px 0}.muted{color:#b2bdc5}.tag{color:#e8bb84}
@media(max-width:800px){main{padding:14px}.grid{grid-template-columns:1fr}}</style><main>
<div class="tag">BW PIRATE ELITE · B04/05 · 19 ноября 2026</div>
<h1>Прежние крылья на корпусе B04/04</h1>
<p>По вашему указанию возвращены обе верхние плоскости из B04/03, включая вырезы и прежние UV.
Выпуклый корпус, широкий нос, двигатели и нижняя стойка полностью сохранены из B04/04.</p>
<p class="muted">Статичный прототип · TRIANGLES треугольников · UV предварительные · анимации отложены.</p>
<div class="grid">CARDS</div>
<h2>Файлы</h2><ul>FILES</ul>
<p><a href="manifest.json">Источники, соль экспорта и проверка точности переноса</a> ·
<a href="review_validation.json">Проверки сохранённого Blender и CMP</a> ·
<a href="../b04_04/index.html">Предыдущая форма 04</a> · <a href="../b04_03/form_top.png">Крылья исходной формы 03</a></p>
<p>Blender использует условные материалы для оценки формы. CMP ссылается на внешние родные BW-материалы.</p>
</main></html>'''
    (OUT / 'index.html').write_text(page.replace('CARDS', cards).replace('FILES', files)
                                  .replace('TRIANGLES', str(report['triangles'])), encoding='utf8')
    print(json.dumps(dict(gallery=(OUT/'index.html').as_posix(), status=report['status'], triangles=report['triangles'])))


if __name__ == '__main__':
    main()
