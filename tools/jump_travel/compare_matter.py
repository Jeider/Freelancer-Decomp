"""Compose the preserved matter preview and its faster, higher-contrast variant."""
from pathlib import Path
import json
import subprocess
import sys
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[2]
textured = '--textured' in sys.argv
parallax = '--parallax' in sys.argv
light = '--light' in sys.argv
cloud = '--cloud' in sys.argv
steady_light = '--steady-light' in sys.argv
infinite = '--infinite' in sys.argv
spline = '--spline' in sys.argv
center = '--center' in sys.argv or steady_light or infinite or spline
old = root / ('out/jump_travel/matter' if cloud else 'out/jump_travel/matter_parallax' if light else 'out/jump_travel/matter_textured' if parallax else 'out/jump_travel/matter_fast' if textured else 'out/jump_travel/matter')
new = root / ('out/jump_travel/cloud_reference' if cloud else 'out/jump_travel/matter_light' if light else 'out/jump_travel/matter_parallax' if parallax else 'out/jump_travel/matter_textured' if textured else 'out/jump_travel/matter_fast')
if center:
    old = new = root / 'out/jump_travel/cloud_reference'
ffmpeg = 'C:/ffmpeg/bin/ffmpeg.exe'
ffprobe = 'C:/ffmpeg/bin/ffprobe.exe'
sheet = Image.new('RGB', (1920, 596), (12, 15, 22))
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 24)
for x, folder, label in [(0, old, 'Предыдущая версия: скорость ×1'),
                         (960, new, 'Новая: скорость ×2, усиленный контраст')]:
    if textured:
        label = 'Предыдущая версия: скорость ×2' if x == 0 else 'Новая: скорость ×4, фактура оригинала'
    if parallax:
        label = 'Предыдущая: пролёт ×4' if x == 0 else 'Новая: пролёт ×5,6, параллакс, спокойная камера'
    if light:
        label = 'Предыдущая: без дальнего источника' if x == 0 else 'Новая: свет в глубине туннеля'
    if cloud:
        label = 'Ранняя облачная основа' if x == 0 else 'Новый облачный туннель по референсам'
    if center:
        label = 'До: короткий туннель, резкий просвет' if x == 0 else 'После: глубокий туннель, плавный fade в свет'
    if steady_light:
        label = 'До: меняющаяся фактура в центре' if x == 0 else 'После: спокойный свет, к которому летим'
    if infinite:
        label = 'До: близкий светящийся выход' if x == 0 else 'После: туннель уходит в бесконечность'
    if spline:
        label = 'До: прямой туннель' if x == 0 else 'После: сплайн, обратный pan, ярче свечение'
    filename = ('spline_before.png' if spline else 'infinity_before.png' if infinite else 'light_before.png' if steady_light else 'center_before.png') if center and x == 0 else 'new.png'
    sheet.paste(Image.open(folder / filename).convert('RGB'), (x, 56))
    draw.text((x + 18, 15), label, font=font, fill='white')
sheet.save(new / 'before_after.png')
sheet.crop((0, 0, 1920, 56)).save(new / 'before_after_labels.png')
subprocess.run([ffmpeg, '-y', '-hide_banner', '-loglevel', 'error',
                '-i', str(old / ('spline_before.mp4' if spline else 'infinity_before.mp4' if infinite else 'light_before.mp4' if steady_light else 'center_before.mp4' if center else 'tunnel.mp4')), '-i', str(new / 'tunnel.mp4'),
                '-i', str(new / 'before_after_labels.png'), '-filter_complex',
                '[0:v][1:v]hstack=inputs=2[body];[2:v][body]vstack=inputs=2[v]',
                '-map', '[v]', '-an', '-c:v', 'libx264', '-preset', 'fast',
                '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart',
                str(new / 'before_after.mp4')], check=True)
for filename in ('tunnel.mp4', 'before_after.mp4'):
    info = json.loads(subprocess.check_output([ffprobe, '-v', 'error',
                      '-select_streams', 'v:0', '-show_entries',
                      'stream=width,height,r_frame_rate,nb_frames', '-of', 'json',
                      str(new / filename)]))['streams'][0]
    if info['nb_frames'] != '480' or info['r_frame_rate'] != '60/1':
        raise RuntimeError(f'Unexpected video timing: {filename}: {info}')
    print(filename, info)
