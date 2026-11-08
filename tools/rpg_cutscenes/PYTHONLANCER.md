# RPG-катсцены в Pythonlancer

Набор `story/rpg/rm0001.json`: глава торгового управления предлагает Тренту
работу машиниста. 21 отдельная реплика на язык, варианты 2/5/10/20 вагонов,
отказ по репутации, вопросы и прощание. Каждая произносимая реплика Трента
компилируется в отдельный THN. Каталог редактируется здесь, в Pythonlancer.

Из корня Pythonlancer:

```powershell
.venv/Scripts/python.exe -B single.py rpg prepare
.venv/Scripts/python.exe -B single.py rpg preview --language both
```

`prepare` экспортирует RU/EN CSV с точными именами записей.
`preview` генерирует 42 THN с приблизительной длиной и без запуска звука.
Результаты находятся в `results/rpg/rm0001/prepare/both` и
`results/rpg/rm0001/preview/both`. Каталог скопирован в каждый результат
как `dialogue.design.json`, источник правок — `story/rpg/rm0001.json`.

## Озвучка существующим backend

Трент использует класс `Trent`. Для торговца явно указывается male-класс
из `story/actors.py`. Например, `Hassler` — только пример выбора голоса,
а не закреплённый голос этого NPC.

```powershell
# Только проверить тексты, выбранных актёров и пути; backend не вызывается.
.venv/Scripts/python.exe -B single.py rpg voices --language both --vendor-actor Hassler --dry-run

# Пользователь запускает, когда выбран голос и готов голосовой backend.
.venv/Scripts/python.exe -B single.py rpg voices --language ru --vendor-actor Hassler
.venv/Scripts/python.exe -B single.py rpg voices --language en --vendor-actor Hassler
```

Команда вызывает штатный `AudioFolder.generate_cutscene_sounds`, поэтому
использует текущую настройку `VOICE_BACKEND` и пропускает уже существующие
MP3/WAV. Настройки backend и голоса сюжетных персонажей не меняются.
Чтобы перезаписать изменённую реплику, сначала вручную уберите именно её старую
запись. Простая смена класса торговца не перезапишет существующие файлы.

Все фрагменты группы складываются вместе:

```text
Assets/AUDIO_CUTSCENE_RU/rm0001/*.mp3  (или WAV от backend)
Assets/AUDIO_CUTSCENE_EN/rm0001/*.mp3
```

План находится в `results/rpg/rm0001/voices/<language>/voice_plan.json`.
Сохраняйте имена вида `rm0001_frag0001_l001_vendor.wav` и
`rm0001_frag0004_l001_player.wav`. Идентификаторы не зависят от голоса.

## Сборка после озвучки

Конвертируйте/обработайте записи до финальных PCM WAV и установите их в:

```text
DATA/AUDIO/MOD/rm0001/*.wav
DATA/AUDIO/MOD_ENG/rm0001/*.wav
```

Затем из Pythonlancer:

```powershell
.venv/Scripts/python.exe -B single.py rpg compile --language both
```

Или соберите до установки аудио, передав отдельную папку:

```powershell
.venv/Scripts/python.exe -B single.py rpg compile --audio-root D:/work/Freelancer-Decomp/out/rpg_cutscenes/audio --language both
```

В этом варианте входы — `<audio-root>/rm0001/ru/*.wav` и
`<audio-root>/rm0001/en/*.wav`. Отсутствующий или нечитаемый WAV останавливает
сборку до записи результата. RU и EN измеряются независимо, включая все жесты
и мимику, зависящие от длительности реплики.

Результаты в `results/rpg/rm0001/compile/both`:

```text
DATA/SCRIPTS/RPG/rm0001/ru/rm0001_frag0001.thn
DATA/SCRIPTS/RPG/rm0001/en/rm0001_frag0001.thn
DATA/AUDIO/rpg_rm0001_ru.ini
DATA/AUDIO/rpg_rm0001_en.ini
subtitles/rm0001_ru.xml
subtitles/rm0001_en.xml
manifest.json
```

`--language ru` и `en` позволяют пересобрать один язык. `--group rm0002`
выберет `story/rpg/rm0002.json`. `--spec` и `--output` задают другие явные
пути; внутри Pythonlancer выход должен находиться в `results/rpg`.
При удалении фрагментов используйте новую выходную папку: старые файлы
автоматически не удаляются, актуальный состав определяется manifest.

## Граница готовности

Подготовлен именно контентный workflow Pythonlancer. Генератор использует
существующие `Autoplay`, facial/body-события и шаблоны, но не инициализирует
LancerCore, кампанию, интерьер и Blender dump для каждой реплики.
Вход `single.py rpg` обрабатывается до тяжёлых импортов обычного single.py.
Остальные действия single.py продолжают работать прежним способом.

Игровая сессия фрагментов, привязка существующего NPC, ротация, проверка
репутации и локальный пропуск одной реплики по Esc ещё требуют реализации
в движке. Эти THN не следует подставлять непосредственно вместо сегодняшнего
`click_script`: им нужен контроллер с привязками актёров и проверенными
камерами комнаты. Manifest пока содержит `installable=false`.
Команды не устанавливают игровые сцены, INI, субтитры или бинарники.
