КАТСЦЕНЫ МИССИЙ 2–8 — ПОЛНЫЙ НАБОР ДЕКОМПИЛЯЦИИ

101 использованный THN: Python Scene + отдельный JSON-дамп + отдельный blend.
Также включены 7 копий mission2.py–mission8.py с привязками THORN_CLASS / THORN_ACCEPT_CLASS / THORN_DECISION_CLASS.
Тексты VOICE_LINES сохранены без изменений. Готовые PrinceWalesScene и SpragueScene миссии 8 не изменены.

Содержимое:
  Pythonlancer/story/cutscenes/story_scenes/<source>.py — редактируемая постановка.
  Pythonlancer/story/scripts/main/missionN.py — копии сценариев с привязками.
  Pythonlancer/story/cutscenes/source_extensions.py — поддержка полных параметров THN, которых нет в текущих удобных классах.
  SCENES/<source>.blend — персонажи и точки движения как меши; камеры и пути как маркеры.
  SCENES/DUMPS/<source>.json — экспорт после сохранения и повторного открытия соответствующего blend.
  <source>/source.json — полный разобранный оригинал; report.json — события, реплики, временные окна и происхождение.
  inventory.json — связи mission/AddRTC/rtc.add/CallThorn -> RTC -> THN, с номерами строк.
  script_compatibility.json — несовпадения старой постановки с текущими сценариями.
  room_results.json — прослеженная цепочка Location -> база -> комната -> set_script -> petaldb -> OBJ.

Проверки:
  101/101 классов исполняются с исходными окнами facial; проверены длительность, ссылки и параметры событий.
  3785 действий совпадают с оригиналом по времени, целям и всем исходным параметрам.
  Финальные THN не записывались и не синхронизировались: этот шаг остаётся за single.py.
  Игровая DATA и готовые сцены не менялись. Проверка EN не выполнялась.

Важные результаты анализа:
  m07_offer включает вступительный разговор Msn6Freeport и затем Msn7Offer. Они сохранены в исходной последовательности;
  Msn7Offer привязан к общей постановке, а Msn6Freeport отдельно к ней не привязан, чтобы не воспроизвести её дважды.
  Старые индексы/актёры не подгонялись под нынешние VOICE_LINES. При расхождении facial() намеренно выдаст ошибку:
  такие сцены являются полными исходными постановками для редактирования, а не обещанием немедленной сборки через single.py.
  В m04_offer_accept оригинал ссылается на отсутствующую cam_start (сразу заменяет её другой камерой в тот же момент).
  В m06_lab_launch исходный неиспользуемый Camera_X ссылается на отсутствующий Mrk_CameraInit.
  В m04_hatcher исходный IK ссылается на не объявленный в THN маркер wlkg_trent_front.
  Эти исходные дефекты записаны в check_results.json; выдуманные координаты не добавлялись.
  У исходных facial-клипов без звуковой реплики сохранены время и длительность с заменой на generic facial;
  для настоящих реплик используются facial() и исходное выделенное окно, а не длина WAV.
  Модели комнат включены только при наличии соответствующего OBJ. При отсутствии — точки и персонажи без подмены комнаты.
  Blend предназначен для редактирования постановки и экспорта точек; движковые скелетные анимации исполняются Python/THN,
  не запекаются в Blender. В каждый blend вложены Python, source.json и report.json.

Развёртывание: содержимое Pythonlancer объединяется с Assets/Pythonlancer, SCENES — с Assets/SCENES.
Перед заменой missionN.py сверить текущие правки: это копии на момент формирования набора.
Готовые сцены миссии 8 используют уже существующие файлы m08.py и их blend/дампы, которые в этот набор не копировались.

Набор по миссиям:
Миссия 2: 9 файлов
  m02_bship_bar_accept, m02_bship_bar_decision, m02_bship_bar_offer, m02_explode_camera, m02_jacobo_offer, m02_jacobo_vendor, m02_junkers, m02_reichman, m02_wilham_vendor

Миссия 3: 7 файлов
  m03_fleet_arrive, m03_kgb_death01, m03_kgb_death02, m03_offer, m03_offer_accept, m03_offer_decision, m03_reward

Миссия 4: 12 файлов
  m04_final, m04_friends_arrive_alaric, m04_friends_arrive_hassler, m04_hatcher, m04_jacobo_death, m04_jumphole, m04_offer, m04_offer_accept, m04_offer_decision, m04_officer_scene01, m04_officer_scene02, m04_reactor_fx

Миссия 5: 18 файлов
  m05_arrest_camera01, m05_arrest_camera02, m05_arrest_camera03, m05_arrest_camera04, m05_arrest_camera05, m05_arrest_camera06, m05_arrest_camera07, m05_arrest_camera08, m05_arrest_camera09, m05_barman, m05_detroit, m05_equip, m05_offer, m05_offer_accept, m05_offer_decision, m05_piratebar, m05_research_explode, m05_rheinlanders_camera

Миссия 6: 23 файлов
  m06_briefing, m06_jumpin_camera1, m06_jumpin_camera2, m06_lab_explode_camera, m06_lab_land, m06_lab_launch, m06_lab_room, m06_mount, m06_nomad_area_camera1, m06_nomad_area_camera2, m06_nomad_area_camera3, m06_nomad_area_camera4, m06_offer, m06_offer_accept, m06_offer_decision, m06_omicron_major, m06_order_camera3, m06_order_camera4, m06_order_deck, m06_prison_new, m06_torpedo_alert, m06_vendor_alaric, m06_vendor_hatcher

Миссия 7: 11 файлов
  m01b_armored_trap_camera, m07_battleship, m07_check_artifact, m07_gunners, m07_offer, m07_offer_accept, m07_offer_decision, m07_omega13, m07_reward, m07_tau_arrival, m07_tortuga_wp_camera

Миссия 8: 21 файлов
  m08_core_camera_01, m08_core_camera_02, m08_core_camera_03, m08_core_camera_04, m08_core_camera_06, m08_core_camera_07, m08_core_camera_08, m08_core_camera_09, m08_lair_done_camera_01, m08_lair_done_camera_02, m08_lair_done_camera_03, m08_lair_done_camera_04, m08_lair_enter_door_01, m08_liberty_enter_camera_01, m08_offer, m08_offer_accept, m08_offer_decision, m08_osiris, m08_outside_camera_01, m08_outside_camera_02, m08_wales_init

