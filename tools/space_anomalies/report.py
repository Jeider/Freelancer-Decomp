"""Validate GPU images and assemble an offline visual report. Requires Pillow.

Run build.py for final renders and --checks first; this script never paints effects.
Only contact-sheet layout, labels, image copying and an HTML index happen here.
"""
import hashlib
import html
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import shutil

from PIL import Image, ImageChops, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "src/obj/space_anomalies"
DEST = ROOT / "docs/space_anomalies/previews"
PRESETS = json.loads(Path(__file__).with_name("presets.json").read_text(encoding="utf-8"))


def changed_fraction(a, b):
    diff = ImageChops.difference(a.convert("RGB"), b.convert("RGB"))
    pixels = diff.get_flattened_data() if hasattr(diff, "get_flattened_data") else diff.getdata()
    return sum(max(p) > 3 for p in pixels) / (a.width * a.height)


def font(size):
    path = Path("C:/Windows/Fonts/segoeui.ttf")
    return ImageFont.truetype(str(path), size) if path.exists() else ImageFont.load_default(size=size)


def sheet(items, path, columns=2, tile_width=800, title="Шейдерные этюды"):
    tile_height = tile_width * 9 // 16
    row_height = tile_height + 66
    result = Image.new("RGB", (columns * tile_width + 48, ((len(items) + columns - 1) // columns) * row_height + 124), "#090d17")
    draw = ImageDraw.Draw(result)
    draw.text((24, 22), title, font=font(30), fill="#edf2ff")
    draw.text((24, 66), "Реальный рендер HLSL · автономный D3D9-стенд · без размещения в системах", font=font(16), fill="#9daabd")
    for i, (source, label) in enumerate(items):
        x = 24 + i % columns * tile_width
        y = 112 + i // columns * row_height
        im = Image.open(source).convert("RGB")
        im.thumbnail((tile_width - 12, tile_height - 6), Image.Resampling.LANCZOS)
        result.paste(im, (x, y))
        draw.text((x + 8, y + tile_height + 6), label, font=font(21), fill="#e5ebf7")
    result.save(path)


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    checks_log = (WORK / "checks/render.log").read_text(encoding="utf-8")
    assert "PASS shader compilation" in checks_log and "finite_nonnegative=FAIL" not in checks_log
    checks = {}
    for p in PRESETS:
        name = p["id"]
        base = Image.open(WORK / f"checks/{name}.png")
        motion = changed_fraction(base, Image.open(WORK / f"checks/{name}_time.png"))
        orbit = changed_fraction(base, Image.open(WORK / f"checks/{name}_orbit.png"))
        assert motion > 0.0001, (name, "time does not affect output", motion)
        assert orbit > 0.001, (name, "camera does not affect output", orbit)
        checks[name] = {"changed_pixels_time_fraction": round(motion, 6), "changed_pixels_orbit_fraction": round(orbit, 6)}
    a = Image.open(WORK / "checks/01_monkey.png").convert("RGB")
    b = Image.open(WORK / "checks/01_monkey_repeat.png").convert("RGB")
    assert ImageChops.difference(a, b).getbbox() is None, "Identical constants must reproduce the same frame"
    flare_delta = changed_fraction(Image.open(WORK / "checks/05_magnetar.png"), Image.open(WORK / "checks/05_magnetar_flare.png"))
    assert flare_delta > 0.005, "Magnetar flare control must affect the image"

    items = []
    for p in PRESETS:
        source = WORK / f"final/{p['id']}.png"
        assert Image.open(source).size == (1600, 900), source
        shutil.copy2(source, DEST / source.name)
        items.append((source, p["title"]))
    sheet(items, DEST / "overview.jpg", columns=2, tile_width=800, title="Космическое шапито · 8 шейдерных этюдов")
    phase_items = []
    for name in ("04_pulsar", "05_magnetar", "08_interior"):
        p = next(p for p in PRESETS if p["id"] == name)
        for suffix, label in (("", "исходная фаза"), ("_time", "+1,35 секунды"), ("_orbit", "другой ракурс")):
            phase_items.append((WORK / f"checks/{name}{suffix}.png", p["title"].split(" · ")[0] + " · " + label))
    sheet(phase_items, DEST / "phases.jpg", columns=3, tile_width=480, title="Движение и ракурс")
    sheet([(WORK / "checks/05_magnetar.png", "Спокойное состояние"), (WORK / "checks/05_magnetar_flare.png", "Вспышка · сила 0,9")], DEST / "magnetar_flare.jpg", columns=2, tile_width=640, title="Магнетар · отдельное управление вспышкой")

    source_files = list((ROOT / "DATA_EXTRA/SHADERS/ANOMALIES").glob("*")) + list(Path(__file__).parent.glob("*.cpp")) + [Path(__file__).with_name("presets.json")]
    hashes = {str(p.relative_to(ROOT)).replace("\\", "/"): hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files if p.is_file()}
    slots = {}
    for p in PRESETS:
        assembly = (WORK / f"checks/assembly/{p['shader']}_{p['variant']}_PSMain.asm").read_text()
        match = re.search(r"approximately (\d+) instruction slots used", assembly)
        slots[p["id"]] = int(match.group(1)) if match else None
    manifest = {"generated_utc": datetime.now(timezone.utc).isoformat(), "renderer": "D3D9 HAL; vs_3_0 / ps_3_0; FP16 HDR + bloom + tone mapping", "gpu": re.search(r"GPU (.+)", checks_log).group(1), "size": [1600, 900], "source_sha256": hashes, "static_ps_slots": slots, "checks": checks, "identical_constants_identical_pixels": True, "flare_changed_fraction": flare_delta, "limitation": "Offline fixture. No game scene/depth integration, device-loss recovery or performance acceptance test.", "image_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in DEST.glob("0*.png")}}
    (DEST / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    shutil.copy2(WORK / "checks/render.log", DEST / "validation.txt")
    cards = []
    for p in PRESETS:
        name, title, desc = p["id"], html.escape(p["title"]), html.escape(p["description"])
        reference = '<a href="https://www.youtube.com/watch?v=vm0QkrtOF2Q&amp;t=84s">Промореференс · 1:24</a>' if name == "02_intro" else ""
        cards.append(f'<article id="{name}"><a class="picture" href="{name}.png"><img src="{name}.png" width="1600" height="900" loading="lazy" alt="{title}"></a><div class="caption"><h2>{title}</h2><p>{desc}</p><div class="links"><a href="../../../DATA_EXTRA/SHADERS/ANOMALIES/{p["shader"]}">HLSL</a><a href="{name}.png">1600 × 900</a>{reference}</div></div></article>')
    document = '''<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Космическое шапито · шейдерная лаборатория</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#080b13;color:#e9efff;font:17px/1.65 system-ui,sans-serif}header,main,footer{max-width:1440px;margin:auto;padding:36px}header{padding-top:64px}.eyebrow{color:#7edbdc;letter-spacing:.2em;font-size:13px;text-transform:uppercase}h1{font-size:clamp(38px,6vw,82px);line-height:1.06;letter-spacing:-.045em;max-width:1000px;margin:22px 0}h1 span{color:#ffc46b}header p{max-width:830px;color:#a9b7cc}nav{display:flex;flex-wrap:wrap;gap:12px;margin-top:28px}a{color:#9ddde7;text-underline-offset:4px}nav a{border:1px solid #26364c;padding:7px 16px;border-radius:24px;text-decoration:none}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px}article{background:#101621;border:1px solid #223048;border-radius:12px;overflow:hidden}article:last-child{grid-column:1/-1}.picture{display:block;background:#03050a}.picture img{width:100%;height:auto;display:block}.caption{padding:20px 24px}h2{font-size:24px;line-height:1.25;margin:0 0 12px}.caption p{font-size:15px;color:#aebcd0;margin:0 0 20px}.links{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}.wide{margin-top:42px}.wide img{width:100%;height:auto;border:1px solid #223048;border-radius:12px}.note{max-width:950px;color:#aebcd0}.small{font-size:14px;color:#8e9cb1}footer{border-top:1px solid #223048;margin-top:40px;padding-bottom:60px}@media(max-width:800px){header,main,footer{padding:22px}.grid{grid-template-columns:1fr}h2{font-size:21px}}
</style><header><div class="eyebrow">Freelancer · The Nomad Legacy · shader studies / 01</div><h1>Космическое<br><span>шапито</span></h1><p>Три чёрные дыры, пульсар, магнетар, квазар, микроквазар и бонусный взгляд за горизонт. Яркий цвет, преувеличенный масштаб, живая плазма и намеренно невозможные пространства.</p><p class="small">Все изображения ниже — реальные кадры написанных HLSL-шейдеров. Автономный D3D9-стенд, 1600 × 900. Это базовые художественные прототипы; в игровые системы они не установлены.</p><nav><a href="overview.jpg">Все варианты одним изображением</a><a href="../../ru/space_anomalies/shaders.md">Отчёт и запуск</a><a href="../../ru/space_anomalies/interior.md">Идеи внутреннего пространства</a><a href="manifest.json">Параметры проверки</a></nav></header><main><section class="grid">CARDS</section><section class="wide"><h2>Движение и ракурс</h2><p class="note">Второй столбец: то же положение камеры через 1,35 секунды. Третий: поворот камеры на 0,65 радиана; внутри тоннеля — поворот взгляда вокруг его оси.</p><a href="phases.jpg"><img src="phases.jpg" alt="Сравнение времени и ракурсов"></a></section><section class="wide"><h2>Вспышка магнетара</h2><p class="note">Отдельный параметр усиливает дуги и добавляет расширяющуюся оболочку. В обычном состоянии он равен нулю.</p><a href="magnetar_flare.jpg"><img src="magnetar_flare.jpg" alt="Магнетар до и во время вспышки"></a></section><section class="wide"><h2>Что уже проверено</h2><p class="note">Компиляция Shader Model 3, создание шейдеров на GPU, чтение HDR без NaN/Inf, изменение изображения при смене времени и ракурса, воспроизводимость кадра и управление вспышкой. Это проверка прототипов, а не измерение скорости в игре.</p><p><a href="validation.txt">Журнал GPU-проверки</a> · <a href="../../../tools/space_anomalies/presets.json">Параметры вариантов</a></p></section></main><footer><p>Основной набор готов для визуального обсуждения. Следующий этап — выбирать характер эффекта, затем переносить его в сцену с реальной глубиной, фоном, масштабом и ограничением стоимости.</p><p class="small">Звёздный фон и шум созданы процедурно. Изображения проморолика не используются как текстуры шейдеров. Внутреннее пространство — художественный вымысел.</p></footer></html>'''.replace("CARDS", "\n".join(cards))
    (DEST / "report.html").write_text(document, encoding="utf-8")
    print(json.dumps({"checks": checks, "flare_changed_fraction": flare_delta, "static_ps_slots": slots}, indent=2))
    print(f"PASS. Visual report: {DEST / 'report.html'}")


if __name__ == "__main__":
    main()
