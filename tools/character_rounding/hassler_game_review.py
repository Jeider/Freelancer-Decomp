"""Publish current Hassler shoulder and right-collar evidence for the native DFM."""
import json,re
from pathlib import Path
from hassler_step14_review import ROOT,TOP,record,fig
OUT=TOP/'game'

def main():
    read=lambda n:json.loads((OUT/n).read_text(encoding='utf8'))
    native=read('native_build.json');preview=read('preview_validation.json');plan=read('install_plan.json');side=read('collar_end_validation.json')
    assert native['sha256']==preview['native_dfm_sha256']==plan['native_dfm_sha256']==side['native_dfm_sha256']
    receipt=read('installation.json') if (OUT/'installation.json').exists() else None
    installed=bool(receipt and receipt['verified'] and receipt['native_dfm_sha256']==native['sha256']);status='Установлен в игру' if installed else 'Подготовлен к установке'
    css='<style>body{max-width:1400px;margin:30px auto;padding:0 24px;background:#24282c;color:#eee;font:17px/1.5 system-ui}a{color:#a8d6ff}img{display:block;width:100%;height:auto}figure{margin:0;background:#30353a}figcaption{padding:12px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:20px 0}nav{display:flex;gap:20px;flex-wrap:wrap}h2{margin-top:38px}.muted{color:#b7bfc7}@media(max-width:800px){.pair{grid-template-columns:1fr}}</style>'
    page='<!doctype html><html lang="ru"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Хасслер — плечи и закрытый торец воротника</title>'+css
    page+=f'<h1>rh_hassler_body — {status.lower()}</h1><p>Шаг 27: верх рукавов расширен под наплечниками. Добавлен объём плеча с плавным переходом к локтю, верхняя часть ткани сильнее следует за ключицей при повороте руки. Форма мундира, наплечники, эполеты, воротник, пояс и родные кости сохранены.</p>'
    page+='<nav><a href="step_27/hassler_native_upper.blend">Редактируемый Blender</a><a href="game/rh_hassler_body.blend">Blender из игрового DFM, все LOD</a><a href="step_27/report.json">Объём рукава</a><a href="step_27/validation.json">Стыки и 22 позы</a><a href="step_26/report.json">Предыдущая правка наплечников</a><a href="game/README.txt">Файлы и проверки</a></nav>'
    page+='<p>Опыт и порядок продолжения: <a href="D:/work/Freelancer-Decomp/docs/ru/hassler_character_workflow.md">D:\\work\\Freelancer-Decomp\\docs\\ru\\hassler_character_workflow.md</a>.</p>'
    page+='<h2>Плечо заполняет рукав под наплечником</h2><p>Увеличен наружный и верхний участок рукава; расширение плавно затухает к предплечью и подмышке. Сшитые границы с корпусом и предплечьем сохранены. Новая геометрия не добавлялась.</p><div class="pair">'+fig('step_27/before_idle.png','До: узкое плечо под широкой серой опорой')+fig('game/game_arm_idle.png','После: более полный верх рукава, игровой DFM в той же позе')+'</div>'
    page+='<div class="pair">'+fig('step_27/before_crossed.png','До: рукав сжимается при скрещивании рук')+fig('game/game_arm_crossed.png','После: объём плеча сохраняется при повороте')+'</div>'
    page+='<div class="pair">'+fig('step_27/before_rest.png','До, исходная поза')+fig('game/game_arm_rest.png','После, исходная поза')+'</div><div class="pair">'+fig('game/game_arm_hips.png','Проверка с руками на поясе')+fig('game/game_arm_other.png','Проверка второго плеча при скрещивании рук')+'</div>'
    page+='<h2>Загнутый край и меньший верх наплечника</h2><p>Центральная высота золотой площадки сохранена; внешний край опущен плавной дугой максимум на 2,64 см. У серой опоры изменён только верх и переход к нему: 1286 нижних вершин остались на месте. В исходную сетку не добавлено новых полигонов.</p><div class="pair">'+fig('step_26/before_profile.png','До: плоский золотой выступ и широкий верх серой опоры')+fig('game/game_shoulder_profile.png','После: край огибает опору; офлайн-рендер игрового DFM')+'</div>'
    page+='<div class="pair">'+fig('step_26/before_other_profile.png','До, другое плечо')+fig('game/game_shoulder_other_profile.png','После, тот же ракурс: золотые выступы у воротника заправлены')+'</div>'
    page+='<div class="pair">'+fig('step_26/before_front.png','До, спереди')+fig('game/game_shoulders_front.png','После: опущены края, центральная высота сохранена')+'</div>'
    page+='<h2>Рукав при руках на поясе</h2><p>Исходный переход местами привязывал внутреннюю часть рукава к корпусу: соседние ряды резко меняли влияние плечевой кости. Теперь оно плавно нарастает вдоль шести сшитых сечений. Подмышечный участок подогнан в нескольких позах; топология шва сохранена. Фактура взята из зелёной ткани штатного RH elite, блеск уменьшен.</p><div class="pair">'+fig('step_25/before_hip_3.png','До: выступ и складки у нижнего стыка рукава')+fig('game/game_ru_hands_hips.png','После: исправленный рукав в той же анимации, игровой DFM')+'</div>'
    page+='<div class="pair">'+fig('game/game_ru_hands_hips_other.png','Проверка другого плеча')+fig('game/game_shoulders_front.png','Общий вид: высота эполетов сохранена')+'</div>'
    page+='<h2>Боковая щель у правого плеча</h2><p>Открытый торец между коротким отворотом и внутренней стенкой закрыт шестью треугольниками по существующим граничным вершинам. Золотые участки, пересекавшие новый торец, убраны за серую стенку.</p><div class="pair">'+fig('step_22/before_right_end.png','До: через боковой торец видно правое плечо')+fig('game/game_collar_right_end.png','После: закрытый серый торец в прочитанном игровом DFM')+'</div>'
    page+=f'<p>Ранее исправленный торец сохранён. Серая поверхность перекрывает {side["rays_per_case"]} контрольный луч во всех {side["pose_lod_cases"]} сочетаниях позы и LOD, с отсечением обратных граней. <a href="game/collar_end_validation.json">Отчёт по правому торцу</a>.</p>'
    page+='<div class="pair">'+fig('game/game_collar.png','Общий вид после экспорта')+fig('game/game_ru_crossed.png','Родная анимация скрещивания рук из RU-сцены, офлайн')+'</div>'
    page+='<h2>Дальние модели</h2><p>'+', '.join(f'LOD{i}: {d["triangles"]:,}' for i,d in enumerate(native['lods']))+' треугольников. Закрытый воротник сохранён на всех LOD.</p><div class="pair">'+fig('game/game_collar_right_end_lod4.png','Правый торец на самом дальнем LOD4')+fig('game/game_full.png','Полная модель')+'</div>'
    page+='<nav><a href="game/collar_validation.json">Шов шеи в 27 позах</a><a href="game/neck_regression.json">Крепления головы и шеи</a><a href="game/collar_opacity_validation.json">Внутренняя стенка</a><a href="game/native_build.json">Экспорт и свежий salt</a><a href="game/install_plan.json">Состав установки</a></nav>'
    if installed:page+='<p><a href="game/installation.json">Проверенные файлы установленной модели</a></p>'
    page+='<p class="muted">Изображения — офлайн-рендеры. Игра не запускалась. Проверки используют родные анимации RU-сцены, но не её IK и лицевую анимацию.</p></html>'
    missing=[p for p in re.findall(r'(?:href|src)="([^"]+)"',page) if not (TOP/p).is_file()];assert not missing,missing
    (TOP/'index.html').write_text(page,encoding='utf8')
    description=f'''RH_HASSLER_BODY — {status}
Текущая авторская версия: step_27. Более полный верх рукава, плавный переход к локтю и привязка к ключице.
Игра: D:\\Games\\FL_MOD\\DATA\\CHARACTERS\\BODIES\\rh_hassler_body.dfm
Исходник: {native['source_blend']}
Игровой Blender: {OUT/'rh_hassler_body.blend'}
Галерея: {TOP/'index.html'}
SHA256 DFM: {native['sha256']}
SHA256 исходника: {native['source_blend_sha256']}
Шаг 27: расширена верхняя/наружная часть рукава, максимум движения 35 мм. Обе руки.
Швы с корпусом и предплечьем неизменны; подмышечное расширение затухает, кости не двигались.
Проверены 22 позы; площади верхних сечений больше прежних минимум на 35.7%.
Верх серого наплечника сужен на 28% в плане, 1286 нижних вершин сохранены.
Внешний золотой край опущен дугой максимум на 26.4 мм, центральная высота сохранена.
Золотые возвраты заправлены под серый воротник; закрытые сетки эполетов и опор сохранены.
Рукава: плавные веса вдоль сшитых сечений; локальная правка подмышек в нескольких позах.
Ткань RH elite: непрерывная развёртка рукавов, 85% текстуры, roughness 0.9, specular 0.1.
Стыки рукавов проверены после повторного открытия Blender, исходная топология сохранена.
Кости RH elite, Cons, inverse bind, hp_head/hp_neck, голова и пояс не перемещались.
Правый торец: 6 новых треугольников соединяют отворот с внутренней стенкой;
толщина 2.4 мм. Граничные вершины и веса общие. Сохранён на всех пяти LOD.
LOD: {', '.join(str(x['triangles']) for x in native['lods'])} треугольников.
Проверки: collar_end_validation.json — боковая щель; collar_opacity_validation.json —
внутренняя стенка; collar_validation.json — шейный шов в 27 позах;
neck_regression.json — раздельные hp_head/hp_neck. Отчёты привязаны к хешу DFM.
17 материалов DcDt, DDS/DXT1 с mip-цепочками, максимум 4 веса, индексы <65536.
Свежий salt: {native['private_resource_salt']}; resource mapping в native_build.json.
Костюм и Pythonlancer уже подключены. DATA пишется через tools.data_folder.DataFolder.
После проверки установки удаляются staging DFM/DDS, промежуточные mesh JSON и
временные rollback-копии. Исходники Blender, инструменты, изображения и отчёты сохраняются.
Игра не запускалась; проверки офлайн, без IK и лицевой анимации сцены.
'''
    (OUT/'README.txt').write_text(description,encoding='utf8')
    index=TOP/'README.txt';old=index.read_text(encoding='utf8');intro=f'Текущая версия: rh_hassler_body, шаг 27 — {status.lower()}.\nBlender: step_27/hassler_native_upper.blend; игровой: game/rh_hassler_body.blend.\nГалерея: index.html; описание: game/README.txt.\nОпыт, причины ошибок и пересборка: D:\\work\\Freelancer-Decomp\\docs\\ru\\hassler_character_workflow.md'
    text=re.sub(r'^Текущая версия:.*?\n\n',lambda _:intro+'\n\n',old,count=1,flags=re.S) if old.startswith('Текущая версия:') else intro+'\n\n'+old;index.write_text(text,encoding='utf8')
    index=ROOT/'out/character_rounding/README.txt';lines=index.read_text(encoding='utf8').splitlines()
    for i,line in enumerate(lines):
        if line.startswith('Хасслер, новая штатная основа:'):lines[i]=f'Хасслер, новая штатная основа: hassler/native_upper/index.html — шаг 27, {status.lower()}.'
        if line.startswith('Blender: hassler/native_upper/'):lines[i]='Blender: hassler/native_upper/step_27/hassler_native_upper.blend; игровой: hassler/native_upper/game/rh_hassler_body.blend.'
    index.write_text('\n'.join(lines)+'\n',encoding='utf8')
    images=['game_shoulders_front.png','game_shoulder_depth.png','game_shoulder_profile.png','game_shoulder_other_profile.png','game_ru_hands_hips.png','game_ru_hands_hips_other.png','game_collar_right_end.png','game_collar_right_end_lod4.png','game_collar.png','game_ru_crossed.png','game_full.png']
    images+=['game_arm_'+k+'.png' for k in ('rest','crossed','hips','idle','other')]
    reports=['native_build.json','preview_validation.json','collar_end_validation.json','collar_validation.json','neck_regression.json','collar_opacity_validation.json','install_plan.json','README.txt']
    manifest={'native_dfm_sha256':native['sha256'],'preview_blend':record(OUT/'rh_hassler_body.blend'),'source_blend':record(Path(native['source_blend'])),'previews':[record(OUT/n) for n in images],'reports':[record(OUT/n) for n in reports],'installed':installed}
    manifest['authoring_reports']=[record(TOP/'step_27/report.json'),record(TOP/'step_27/validation.json'),record(TOP/'step_26/report.json'),record(TOP/'step_26/validation.json'),record(TOP/'step_25/report.json'),record(TOP/'step_25/validation.json')]
    (OUT/'review_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(status,TOP/'index.html')

if __name__=='__main__':main()
