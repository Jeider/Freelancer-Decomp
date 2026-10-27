# Cosmic anomaly source register

[English overview](README.md) · [Обзор на русском](../ru/space_anomalies/README.md)

Research/access date: **2026-10-26**. This register is shared by the English and Russian documents. Dates below identify publications or explicitly selected revisions, not a claim that an old article describes the latest record holder or every current game mechanic.

Реестр общий для двух языков. **Primary / первичный** — научная статья, описание наблюдения, материал разработчика или его документация. **Community / сообщество** — руководство или вики; такие источники подтверждают игровые примеры, но не физику и не устройство закрытого рендерера. Параметры будущих шейдеров и бюджеты в проекте — авторские предложения.

## Astrophysics and numerical rendering

| ID | Source | Evidence used / Что подтверждает |
|---|---|---|
| S01 | [NASA Science — Black Holes](https://science.nasa.gov/universe/black-holes/) | Horizon, isolated holes, distinction from wormholes and vacuum-cleaner imagery / Горизонт, отсутствие обязательного диска, отличие от портала и «пылесоса» |
| S02 | [NASA Science — Anatomy](https://science.nasa.gov/universe/black-holes/anatomy/) | Disk, shadow, corona and jet components / Состав окружения чёрной дыры |
| S03 | [NASA — A Black Hole's Warped World](https://www.nasa.gov/universe/nasa-visualization-shows-a-black-holes-warped-world/), 2019-09-25 | Viewing-angle dependence, disk structure and brightness asymmetry / Ракурс, структура и асимметрия яркости |
| S04 | [Eric Bruneton — Real-time High-Quality Rendering of Non-Rotating Black Holes](https://ebruneton.github.io/black_hole_shader/paper.pdf), technical report May 2020; [project and demo](https://ebruneton.github.io/black_hole_shader/); [arXiv record](https://arxiv.org/abs/2010.08735), 2020-10-17 | Schwarzschild ray model, precomputed tracing and star filtering / Численная основа линзирования; these are versions of one work, not independent confirmations |
| S05 | [ESA — Neutron stars, pulsars and magnetars](https://www.esa.int/Science_Exploration/Space_Science/Neutron_stars_pulsars_and_magnetars) | Rotating directional emission and magnetar classification / Пульсации и сильные поля; use detailed measurements for radii rather than its rounded popular description |
| S06 | [Mereghetti, Pons and Melatos — Magnetars: Properties, Origin and Evolution](https://arxiv.org/abs/1503.06313), 2015 | Magnetic energy, sample periods/fields and overlapping pulsar behaviour / Магнитное питание, периоды, поля, пересечение категорий; historical sample, not a current census |
| S07 | [Choudhury et al. — A NICER View of PSR J0437−4715](https://arxiv.org/abs/2407.06789), 2024 | Model-conditional radius and hot-region inference / Радиус конкретной звезды и зависимость вывода от модели |
| S08 | [NASA — Magnetar Eruptions in Nearby Galaxies](https://www.nasa.gov/universe/nasa-missions-unmask-magnetar-eruptions-in-nearby-galaxies/), 2021-01-13 | Short giant flare on 2020-04-15 / Пример короткой гигантской вспышки, не периодический эффект |
| S09 | [NASA Science — Galaxy Types](https://science.nasa.gov/universe/galaxies/types/) | Active nuclei, quasars and blazar orientation / Активные ядра, квазары и ориентация блазара |
| S10 | [ESO — Radio-loud quasar P172+18](https://www.eso.org/public/news/eso2103/), 2021-03-08 | Quasar engine and approximate radio-loud fraction / Питание квазара и приблизительная доля радиогромких объектов; the title's distance record belongs to 2021 |
| S11 | [Macfarlane et al. — Radio loudness of SDSS quasars from LoTSS](https://academic.oup.com/mnras/article/506/4/5888/6321852), 2021 | Radio-loud classification does not imply no weak jets elsewhere / Осторожность с выводом «у радиотихого объекта нет струй» |
| S12 | [NASA — Two Black Holes Teach Astronomers a Lesson](https://www.nasa.gov/universe/two-black-holes-teach-astronomers-a-lesson/), 2008 | Companion-fed microquasar disks and jets / Звёздный масштаб, компаньон, диск и джеты |
| S13 | [NASA Science — Star Types](https://science.nasa.gov/universe/stars/types/) | White dwarfs, neutron stars and stellar remnants / Различие белого карлика, нейтронной звезды и остатков эволюции |
| S14 | [Cerutti and Giacinti — Formation of giant plasmoids at the pulsar wind termination shock](https://www.aanda.org/articles/aa/pdf/2021/12/aa42178-21.pdf), A&A 656 A91, 2021 | Nebular jets, torus, arcs and knots / Морфология пульсарной туманности, отличная от простого луча-маяка |
| S15 | [NASA Hubble — Black Hole Tidal Disruption Event](https://science.nasa.gov/asset/hubble/black-hole-tidal-disruption-event/) | TDE animation and explanation / Разрушение звезды, поток и вспышка; illustration, not footage near a horizon |
| S16 | [NASA Hubble — Neutron Star Collision Creates Kilonova](https://science.nasa.gov/asset/hubble/neutron-star-collision-creates-kilonova/), release 2017-10-16 | Merger, ejecta, later emission and possible remnant / Слияние, выброс и последующее свечение; schematic sequence |
| S17 | [Bochenek et al. — A fast radio burst associated with a Galactic magnetar](https://www.nature.com/articles/s41586-020-2872-x), 2020-11-04 | FRB 200428 association / Связь конкретного FRB с магнетаром; does not establish one origin for all FRBs |
| S18 | [NASA Webb — Wolf–Rayet 140 MIRI](https://science.nasa.gov/asset/webb/wolf-rayet-140-miri/) | Repeated dust shells and assigned infrared colours / Пылевые оболочки и условные цвета инфракрасного изображения |
| S19 | [NASA Hubble — Cataclysmic Variable Star](https://science.nasa.gov/asset/hubble/cataclysmic-variable-star/), original release 1995-05-22 | White-dwarf mass transfer and classical-nova distinction / Перетекание вещества и вспышка новой; illustration |

The solar-mass horizon table, angular-size example, dipole curve construction and GPU memory estimates in these documents are explicit calculations or proposed models. They are not measurements copied from a game or results of a new astrophysical simulation.

## Games and simulator

| ID | Source | Provenance and scope / Происхождение и границы |
|---|---|---|
| G01 | [Deep Space Network — Traveling with neutron stars and white dwarfs](https://ed-dsn.net/en/neutrons-2/) | Community guide; cones and FSD gameplay / Руководство игроков, не физический источник |
| G02 | [Elite Dangerous Wiki — Black Holes](https://elite-dangerous.fandom.com/wiki/Black_Holes) | Community; indexed text available, direct retrieval failed / Использован для наличия объектов, не для обещания текущих точных механик урона |
| G03 | [Hello Games — Endurance update 3.94](https://www.nomanssky.com/endurance-update/) | Primary; black-hole traversal VFX / Официальное описание и видеореференс |
| G04 | [Mobius — Brittle Hollow VFX](https://www.mobiusdigitalgames.com/news/brittle-hollow-visual-effects-vfx), 2018-08-17 | Primary; bending-light shader and consumption feedback / Разработчики описывают эффект и его игровую роль |
| G05 | [ROCKFISH — EVERSPACE version 1.0 changes](https://steamcommunity.com/games/396750/announcements/detail/1252410711759059753), 2017 | Primary developer announcement on Steam; black-hole placement / Первая игра, размещение дыр возле объектов |
| G06 | [ROCKFISH — EVERSPACE patch 1.2.0](https://store.steampowered.com/news/posts/?appids=396750&enddate=1508849080), 2017-10-24 | Primary patch archive; resource spawning / Ресурсы около чёрных дыр; not an EVERSPACE 2 claim |
| G07 | [EVE Developer Documentation — Wormhole Effects](https://developers.eveonline.com/docs/guides/staticdata/#wormhole-effects) | CCP-hosted, explicitly crowdsourced documentation; secondary-sun classes and system effects / Не описание внутреннего шейдера |
| G08 | [Egosoft — X4 Tides of Avarice](https://store.steampowered.com/app/1701060/X4_Tides_of_Avarice/) | Primary store description; stellar phenomena influence play / Официальное описание дополнения |
| G09 | [X Community Wiki — Avarice V](https://wiki.egosoft.com/X4%20Foundations%20Wiki/Manual%20and%20Guides/Objects%20in%20the%20Game%20Universe/Systems%2C%20Sectors%20and%20Zones/Systems%20Database/Avarice/Avarice%20V%3A%20Dead%20End/?rev=7.9), revision 7.9 dated 2023-10-11 | Egosoft-hosted community encyclopaedia; Tide and anomalies / 7.9 is the wiki revision, not the game's version |
| G10 | [SpaceEngine — General Relativity release](https://spaceengine.org/news/blog221216/), 2022-12-16 | Primary; geodesics and volumetric disk/jet features / Подтверждение функций указанного релиза |
| G11 | [SpaceEngine user manual](https://spaceengine.org/manual/user-manual) | Primary; environment-map quality/cost tradeoffs / Настройки внеэкранного фона и частоты обновления |

## Visual reference selection

Use the linked pages' own galleries and media to preserve context and credits. The descriptions below identify what to examine; they do not imply an in-game capture session was performed for this research.

| Reference | Inspect / На что смотреть | Interpretation |
|---|---|---|
| NASA black-hole visualization, S03 | Far disk above/below the shadow, moving disk structure / Изображение дальней стороны и движение диска | Scientific visualization, not an optical photograph |
| Bruneton demo, S04 | Background star images, inclination and camera position / Звёзды, наклон и позиция камеры | Limited mathematical model with published implementation |
| NASA magnetar flare, S08 | Short event and longer surrounding response / Короткая вспышка и последующая эволюция | Animation and observational explanation; colours are presentation |
| Pulsar nebula paper, S14 | Torus versus axial jet / Различать тор и струю | Observation-informed scientific morphology |
| WR 140, S18 | Repeated shells and asymmetric brightness / Оболочки и неравномерная яркость | Infrared channels mapped to visible colours |
| DSN cone guide, G01 | Ship-to-cone scale and approach geometry / Относительный размер и траектория | Gameplay presentation |
| No Man's Sky Endurance, G03 | Separate distant and transit states / Состояния объекта и перехода | Deliberately fictional travel |
| Outer Wilds VFX, G04 | Fragment consumption and local response / Поглощение конкретного обломка | Authored event feedback |
| SpaceEngine release, G10 | Disk thickness, jets and changing viewpoint / Толщина диска, струи и ракурсы | Advanced renderer; not an RP9 performance benchmark |

## Local implementation evidence

The working-tree sources checked were `src/include/render/IRenderPipelineEx.h`, `IRPSceneCapture.h`, `IRenderPipeline.h`, `src/RP9/RP9Ex.cpp`, `src/freelancer/Client/render_ex.cpp`, `space_scene_obj_draw.cpp`, `jumphole_visual.cpp`, `ship_warp_visual.cpp`, and the existing jumphole/solar shaders. Clickable paths and specific functions are in [rendering.md](rendering.md). No new shaders or executable changes accompany this research.

The repository is changing concurrently. Existing capabilities are a dated inspection, not a statement that their line numbers, defaults or ownership will remain fixed. Verify the current implementation before coding the proposed hooks.

## Open questions for follow-up

- Select a target system and encounter scale; decide whether the first prototype is visual only.
- Choose a static distant environment or fully dynamic off-screen geometry for lensing.
- Compare the numerical model against an independent CPU integrator near critical rays.
- Capture actual game reference views before claiming frame-level visual matches.
- Measure the chosen RP9 implementation on the target GPU; none of the proposed step counts has a measured frame time yet.

Источники сохранены как ссылки и краткие выводы. Чужие статьи целиком, изображения, игровые ресурсы и код в репозиторий не копировались. Если позднее переносится внешний код, отдельно проверить его лицензию и происхождение ресурсов; публичная демонстрация не делает всё её содержимое общественным достоянием.
