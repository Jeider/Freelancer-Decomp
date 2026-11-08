# Реплики диспетчера курьерских поездов

Актуальный английский пакет: [dispatcher_en01_recording.zip](../../../out/train_courier/dispatcher_en01_recording.zip), исходник — [dispatcher_en.py](../../../tools/train_courier/dispatcher_en.py). Он заменяет английскую часть черновика ниже: **110 новых фрагментов**, 11 семейств по 10 вариантов, без названий баз и товаров. Для генерации использовать `recording.tsv` или `lines.json` из архива; `courier_lines_en.py` содержит те же строки в формате `PilotLine`. Наследование словаря диспетчера пользователь добавляет сам. Русская часть пока остаётся черновиком.

Точная схема нового заказа: `tc_order_NN+` → фактический товар → `tc_destination_NN+` → база получателя → `tc_collect_NN-`. Последний фрагмент каждый раз объясняет подход кормой к точке сцепки и использование манёвра сцепки. Подтверждение после подцепления: `tc_depart_NN+` → база получателя. Эти же сведения звучат для следующего заказа после YES; общая реплика `tc_next` их больше не заменяет. В текущей реализации состав содержит один тип товара; перечень всех возможных товаров вместо реального груза не читается.

Для товара используется штатная схема обычных пилотов из `Gcs.cpp`: `TranslateGoodToMsgIdPrefix(good_id)` → точный ID клипа, без добавления символов. Пример Pythonlancer: `comm_basic_meds` → `gcs_gen_commodity_comm_basic_meds`. `+` относится к вводным вариантам фраз, а не к товарному префиксу. Имена баз берутся из `voice_name` каталога вместе с уже существующим суффиксом. Допустимые товары ограничены `core.store.get_commodities()`; ритейловый ассортимент не экспортируется и новые записи названий не создаются.

Дополнены события прибытия и потери сцепки. Перед YES_NO контроллер ждёт `CommComplete` выбранной реплики `tc_continue`, вместо предположения о шести секундах. Конфиг и исходники подготовлены, но сборка и включение аудио отложены; после генерации нужны фактические длительности WAV и прослушивание стыков фрагментов в игре.

Текстовая основа озвучки к [дизайну динамических перевозок](train_courier_design.md), 6 ноября 2026 года. Десять событий имеют по десять вариантов на русском и английском: 100 реплик для каждого языка. Варианты внутри семейства выполняют одно действие и не меняют условия заказа.

Это черновик текстов для записи. Аудио не генерируется и игровые конфиги этим документом не меняются. Основной тон — спокойный деловой диспетчер, доброжелательный, без постоянного восторга. Обращение «мистер Трент» используется в части вариантов. Технические термины Solar, кэш, скрытая база и сервер в эфире не произносятся.

## Голоса и существующий механизм вариантов

Требование пользователя: русский голос `dispatcher01`, английские записи `dispatcher_en01`.

В действующей интеграции Pythonlancer это два уровня имени:

| Язык | Голос игры | Источник записей |
|---|---|---|
| Русский | `dispatcher01` | `StationDispatcher` / `MaleDispatcher`, папка `dispatcher01` |
| Английский | `atc_leg_m01_new` | `EngMaleDispatcher`, папка `dispatcher_en01` |

Соответствие подтверждают `universe/audio/space_voice.py`, `universe/audio/manager.py` и начало установленного `DATA/AUDIO/voices_space_male.ini`. В английском классе `MVOICE_AUDIO_PROP` и `MVOICE_MISSION_PROP` пустые; менеджер встраивает файловые Sound-записи в существующий голос. При реализации требуется дополнить свойства реального Voice ID, а не просто объявить каталог аудио новым голосом. Переименование не является требованием дизайна.

### Формат mVoiceProp

Штатный пример из `DATA/MISSIONS/voice_properties.ini`:

```ini
[mVoiceProp]
voice = mc_leg_m02
permutation_count = rmb_gotowaypoint, 2
permutation_count = rmb_success_ships, 2
permutation_count = rmb_success_ass, 4
```

Для новой миссии предлагаются собственные семейства. Пример будущего конфига для одного семейства:

```ini
[mVoiceProp]
voice = dispatcher01
permutation_count = tc_continue, 10

[mVoiceProp]
voice = atc_leg_m01_new
permutation_count = tc_continue, 10
```

Имена Sound-записей: `tc_continue_01-` … `tc_continue_10-`. В `permutation_count` записывается основа без номера и суффикса. Все номера от 01 до объявленного количества должны существовать у соответствующего голоса; селектор не проверяет наличие звукового файла. Объявить count недостаточно: требуются Sound-записи, аудио и корректные длительности.

Путь в движке:

1. `LoadContentGameTables()` в `src/Content/Encounters.cpp` загружает `audio/voices_space_male.ini`, `voices_space_female.ini`, `voices_recognizable.ini`, затем `missions/voice_properties.ini`.
2. `LoadVoiceProperties()` в `src/Content/RandomMissionGen.cpp` читает `[mVoiceProp]`, связывает свойства по Voice ID и кладёт `permutation_count` в таблицу по ID основы фразы.
3. `PickVoiceLine()` в `src/Content/Gcs.cpp` получает количество и строит `<основа>_%02d<суффикс>`. `MakeVoiceLineName()` вызывает эту же функцию.
4. `FRmOfferComponent::PrepareConversation()` в `src/Content/RandomMissionMachine.cpp` выбирает конкретный вариант через `MakeVoiceLineName(Line->Text, "-", VoiceId)` и кладёт его ID в список фрагментов сообщения.

При повторной записи одного ключа для того же голоса загрузчик использует `map::insert`: остаётся первое значение. Поэтому нельзя рассчитывать, что поздний блок переопределит count с 2 на 10; нужно править исходную декларацию. Новые семейства `tc_*` не должны дублироваться с разными значениями.

### Как выбирается вариант и что считается повторением

Для количества `N` штатная функция использует:

```text
index = floor(N - cos(rand() / 32768 × pi/2) × (N - 1) + 0.5)
```

Это случайный выбор из 1…N с уклоном к младшим номерам, не равномерный выбор и не обход по кругу. При `N = 1` всегда выбирается 01. Предыдущий индекс не хранится: один и тот же вариант может выпасть подряд. У GCS отдельно существуют история сообщений, интервалы и вероятности категорий; они не превращают `permutation_count` в гарантию отсутствия повторов вариантов.

Для курьерских реплик использовать штатные семейства и выбор через mVoiceProp. Если понадобится строгий запрет немедленного повторения, это отдельное дополнение контроллера, а не свойство текущего конфига. Его не следует добавлять ко всем разговорам игры ради этой миссии.

Отсутствующий голос даёт `PickVoiceLine` код -2, отсутствующий или неположительный count — -3; выходное имя остаётся пустым. Будущий контроллер должен проверять результат до отправки comm.

## События и порядок воспроизведения

| Семейство | Когда звучит | Что происходит после |
|---|---|---|
| `tc_board` | Локомотив доступен после вылета | Маркер стыковки, ожидание посадки |
| `tc_pickup` | Выдан заказ и доступны назначенные вагоны | Поиск точки погрузки и сцепка |
| `tc_depart` | Получение состава подтверждено | Маркер точки доставки |
| `tc_arrival` | Прибытие в зону получателя | Манёвр сдачи по правилам миссии |
| `tc_paid` | Доставка подтверждена, деньги уже начислены | Переход к предложению продолжить |
| `tc_continue` | После оплаты предыдущего заказа | По завершении реплики окно YES_NO |
| `tc_next` | Получен YES и следующий заказ успешно сформирован | Новый заказ с ростом состава и дальности |
| `tc_finish_delivery` | После NO выбран финал с доставкой к планете | Финальный маршрут без предложения продолжить |
| `tc_park` | После NO выбран финал с парковкой | Маркер парковки локомотива |
| `tc_done` | Личный корабль восстановлен, смена завершена | Завершение связи |

Не проигрывать все варианты: выбрать одну реплику из нужного семейства. Для `tc_next` условием является реально сформированный более дальний заказ с дополнительным вагоном. Не озвучивать оплату до подтверждения выплаты. Ветка `tc_finish_delivery` не должна автоматически возвращать игрока в цикл YES_NO.

Пример разговора: `tc_paid` → `tc_continue` → YES_NO → YES → `tc_next` → сведения о грузе и получателе → `tc_pickup`. При NO вместо `tc_next` звучит один из двух вариантов завершения. Сообщения ставятся в очередь, чтобы окно и следующая реплика не перекрывали предыдущую.

## Подстановка баз и товаров

Штатный выбор варианта выбирает имя клипа; он сам не подставляет текстовые `{BASE}` или `{CARGO}`. Для составной реплики контроллер собирает последовательность существующих ID звуковых фрагментов. В `FGcsLine` есть список `TextIds`; путь `FGcsPlayerListLine::Play` использует локальный массив из 16 элементов. Для предложенных коротких сообщений достаточно нескольких фрагментов; длинные объявления нужно разделять, не переполняя этот путь.

Предлагаемые дополнительные связки для записи:

| ID клипа | Русский | English | Следующий фрагмент |
|---|---|---|---|
| `tc_pickup_name_01+` | Точка погрузки: | Pickup location: | Название базы отправителя |
| `tc_destination_name_01+` | Получатель: | Destination: | Название базы получателя |
| `tc_cargo_name_01+` | Груз: | Cargo: | Название товара |
| `tc_final_name_01+` | Конечный пункт: | Final destination: | Название дружелюбной планеты |
| `tc_marker_hint_01-` | Нужная торговая точка отмечена на карте. | The trading point is marked on your map. | Конец сообщения |

Это пять дополнительных пар текстов сверх 100 основных вариантов. В таком объявлении: выбранная основная фраза → «Получатель:» → название → при необходимости подсказка маркера. Суффиксы `+` и `-` передаются в имени выбранного фрагмента; конкретная обработка интонации задаётся правилами аудиогенератора, а не числом вариантов.

Названия можно использовать после двоеточия как самостоятельное объявление: «Получатель: станция Лидс». Это позволяет не требовать форму «на станции Лидс» для каждого варианта. Нужно сопоставить реальную запись с подходящим падежом. В `BaseIdentifiedVoice` генерация названий баз подтверждена; товары добавляются в другом уровне наследования `SystemIdentifiedVoice`. Полноту уже установленных товарных записей именно у двух выбранных голосов нужно проверить перед записью недостающего материала. Требование пользователя — переиспользовать имеющиеся записи.

Шаблон для Pythonlancer по образцу `universe/audio/mission_comission.py`:

```python
L('tc_continue_01-', 'Отлично, мистер Трент. Готовы к следующему заданию?')
L('tc_continue_02-', 'Есть ещё один заказ. Продолжим работу?')
```

Это образец будущего включения в нужные голоса, не готовый генератор. Класс `MCVoice` служит образцом структуры вариантов; его голос `mc_leg_m01` не подменяет dispatcher. Сначала утвердить тексты и границы фрагментов, затем подготовить ударения, длительности и интонации с `PilotLine`/`parse_rule` и проверить склейку на слух.

## Посадка в локомотив

Основа `tc_board`, count 10, клипы `tc_board_01-` … `tc_board_10-`.

| № | Русский | English |
|---|---|---|
| 01 | Здравствуйте, мистер Трент. Чтобы приступить к работе, состыкуйтесь с локомотивом у причала. | Hello, Mr. Trent. To begin your shift, dock with the locomotive by the mooring fixture. |
| 02 | Мистер Трент, ваш локомотив готов. Он стоит у причала и отмечен на карте. Стыкуйтесь. | Mr. Trent, your locomotive is ready by the mooring fixture. It is marked on your map. Dock with it. |
| 03 | Диспетчер на связи. Локомотив ожидает у причала. Для пересадки выполните стыковку. | Dispatch here. The locomotive is waiting by the mooring fixture. Dock with it to take over. |
| 04 | Добро пожаловать на смену, Трент. Сначала состыкуйтесь с отмеченным локомотивом. | Welcome to your shift, Trent. First, dock with the marked locomotive. |
| 05 | Ваше назначение подтверждено. Локомотив у причала, можете приступать к стыковке. | Your assignment is confirmed. The locomotive is by the mooring fixture. You may dock with it. |
| 06 | Трент, начинаем с пересадки. Подойдите к локомотиву и запросите стыковку. | Trent, we will start with the transfer. Approach the locomotive and request docking. |
| 07 | Рад вас слышать, мистер Трент. Для начала работы займите локомотив через стыковку. | Good to hear from you, Mr. Trent. Dock with the locomotive to begin work. |
| 08 | Локомотив подготовлен к рейсу. Его положение отмечено. Стыкуйтесь, когда будете готовы. | The locomotive is prepared for the run. Its position is marked. Dock when you are ready. |
| 09 | На связи диспетчер перевозок. Ваш локомотив у причала. Подтвердите стыковку с ним. | Freight dispatch calling. Your locomotive is by the mooring fixture. Request docking with it. |
| 10 | Мистер Трент, пора принимать локомотив. Найдите отмеченный объект и выполните стыковку. | Mr. Trent, it is time to take over the locomotive. Find the marked vessel and dock with it. |

## Получение вагонов

Основа `tc_pickup`, count 10. Названия погрузки, товара и получателя сообщаются отдельными фрагментами.

| № | Русский | English |
|---|---|---|
| 01 | Подцепите назначенные вагоны. Точка погрузки отмечена на карте. | Couple to the assigned wagons. The pickup point is marked on your map. |
| 02 | Груз готов к отправке, мистер Трент. Заберите вагоны у отмеченной торговой точки. | The cargo is ready, Mr. Trent. Collect the wagons at the marked trading point. |
| 03 | Ваши вагоны ожидают погрузочного манёвра. Следуйте к указателю и выполните сцепку. | Your wagons are waiting. Follow the marker and couple to them. |
| 04 | Трент, начинайте сбор состава. Нужные вагоны отмечены. | Trent, begin assembling your train. The assigned wagons are marked. |
| 05 | На торговой стоянке подготовлены вагоны для вашего заказа. Подцепите их. | The wagons for your order are ready at the trading berth. Couple to them. |
| 06 | Перед отправлением заберите назначенные вагоны. Ориентируйтесь по миссионному указателю. | Collect the assigned wagons before departure. Follow the mission marker. |
| 07 | Отправитель подготовил груз. Подведите локомотив к отмеченным вагонам и сцепитесь. | The shipper has prepared the cargo. Bring the locomotive to the marked wagons and couple up. |
| 08 | Мистер Трент, приступайте к сцепке. Вагоны этого заказа находятся у торговой точки. | Mr. Trent, proceed with coupling. The wagons for this order are at the trading point. |
| 09 | Следующая задача — получить вагоны. Их положение передано на вашу карту. | Your next task is to collect the wagons. Their position has been sent to your map. |
| 10 | Всё готово к погрузке состава. Подцепите отмеченные вагоны, Трент. | Everything is ready for collection. Couple to the marked wagons, Trent. |

## Отправление с грузом

Основа `tc_depart`, count 10. После реплики можно добавить название получателя.

| № | Русский | English |
|---|---|---|
| 01 | Состав принят. Следуйте к отмеченной точке доставки. | Train confirmed. Proceed to the marked delivery point. |
| 02 | Вагоны на месте, мистер Трент. Можно отправляться к получателю. | The wagons are accounted for, Mr. Trent. You may depart for the destination. |
| 03 | Сцепку подтверждаю. Точка назначения загружена в навигацию. | Coupling confirmed. The destination is now in your navigation display. |
| 04 | Груз у вас. Доставьте состав к указанной торговой точке. | You have the cargo. Deliver the train to the designated trading point. |
| 05 | Можно начинать рейс, Трент. Следуйте по указателю доставки. | You may begin the run, Trent. Follow the delivery marker. |
| 06 | Получение вагонов подтверждено. Берите курс на точку назначения. | Collection confirmed. Set course for the destination. |
| 07 | Состав готов к перевозке. Получатель ждёт вас в отмеченной точке. | The train is ready to move. The recipient is waiting at the marked location. |
| 08 | Хорошо, мистер Трент. Теперь доставьте эти вагоны по назначению. | Good, Mr. Trent. Now deliver these wagons to their destination. |
| 09 | Все назначенные вагоны получены. Следующий указатель ведёт к получателю. | All assigned wagons have been collected. The next marker leads to the recipient. |
| 10 | Отправление разрешаю. Держите курс на отмеченную точку сдачи. | You are clear to depart. Head for the marked delivery point. |

## Прибытие к получателю

Основа `tc_arrival`, count 10. Формулировки не фиксируют ещё не выбранный способ сдачи вагонов.

| № | Русский | English |
|---|---|---|
| 01 | Вы у получателя. Подведите состав к отмеченной точке сдачи. | You have reached the recipient. Bring the train to the marked delivery position. |
| 02 | Мистер Трент, место разгрузки впереди. Завершите подход к указателю. | Mr. Trent, the unloading position is ahead. Complete your approach to the marker. |
| 03 | Прибытие вижу. Займите указанную позицию для сдачи груза. | I have you on arrival. Take the indicated position for delivery. |
| 04 | Точка доставки рядом. Подведите вагоны к месту приёмки. | The delivery point is nearby. Bring the wagons to the receiving position. |
| 05 | Получатель готов принять состав. Следуйте к точному указателю сдачи. | The recipient is ready to receive the train. Follow the delivery position marker. |
| 06 | Вы в районе назначения, Трент. Осталось занять место сдачи. | You are in the destination area, Trent. Move into the delivery position. |
| 07 | Подход подтверждаю. Проведите состав к отмеченной позиции. | Approach confirmed. Bring the train to the marked position. |
| 08 | Мистер Трент, начинайте манёвр сдачи. Нужная точка отмечена. | Mr. Trent, begin your delivery approach. The required position is marked. |
| 09 | Доставка почти завершена. Подведите назначенные вагоны к указателю. | The delivery is nearly complete. Bring the assigned wagons to the marker. |
| 10 | Приёмная точка впереди. Займите её составом для завершения доставки. | The receiving position is ahead. Bring the train into it to complete delivery. |

## Подтверждение оплаты

Основа `tc_paid`, count 10. Звучит только после успешной выплаты за доставку.

| № | Русский | English |
|---|---|---|
| 01 | Груз принят, мистер Трент. Оплата за доставку переведена. | Cargo accepted, Mr. Trent. Payment for the delivery has been transferred. |
| 02 | Доставка подтверждена. Вознаграждение уже на вашем счёте. | Delivery confirmed. Your payment is now in your account. |
| 03 | Заказ выполнен, Трент. Деньги перечислены. | Order complete, Trent. The funds have been transferred. |
| 04 | Получатель подтвердил приёмку. Ваша работа оплачена. | The recipient has confirmed receipt. You have been paid. |
| 05 | Всё принято. Платёж за этот рейс проведён. | Everything has been accepted. Payment for this run is complete. |
| 06 | Мистер Трент, доставка засчитана. Вознаграждение начислено. | Mr. Trent, the delivery is recorded. Your payment has been credited. |
| 07 | Груз сдан. На ваш счёт поступила оплата заказа. | Cargo delivered. Payment for the order has reached your account. |
| 08 | Благодарю, Трент. Доставка завершена и оплачена. | Thank you, Trent. The delivery is complete and paid. |
| 09 | Приёмка завершена. Перевод вознаграждения подтверждаю. | Receipt is complete. I confirm that your payment has been transferred. |
| 10 | Этот заказ закрыт, мистер Трент. Оплата отправлена на ваш счёт. | This order is closed, Mr. Trent. Payment has been sent to your account. |

## Предложение продолжить

Основа `tc_continue`, count 10. После реплики появляется YES_NO; до YES новый заказ не считается принятым.

| № | Русский | English |
|---|---|---|
| 01 | Отлично, мистер Трент. Готовы к следующему заданию? | Excellent, Mr. Trent. Ready for another assignment? |
| 02 | Есть ещё один заказ. Продолжим работу? | There is another order available. Shall we continue? |
| 03 | Трент, возьмёте следующую перевозку? | Trent, will you take the next delivery? |
| 04 | Могу предложить вам ещё один рейс. Согласны? | I can offer you another run. Interested? |
| 05 | Мистер Трент, остаётесь на смене? Есть следующая доставка. | Mr. Trent, are you staying on shift? There is another delivery available. |
| 06 | Работа для вас ещё найдётся. Готовы продолжать? | There is more work available. Ready to continue? |
| 07 | Следующий заказ ждёт решения. Берётесь, Трент? | The next order is waiting for your answer. Will you take it, Trent? |
| 08 | Хотите выполнить ещё одну перевозку, мистер Трент? | Would you like to make another delivery, Mr. Trent? |
| 09 | Можем продолжить рейсы. Подтвердите, готовы ли взять новый заказ. | We can keep the runs going. Please confirm whether you want another order. |
| 10 | На сегодня закончим или берём следующее задание, Трент? | Shall we finish for today, or take the next assignment, Trent? |

## Следующий заказ принят

Основа `tc_next`, count 10. Только после YES и успешного формирования следующего заказа. Затем отдельно сообщаются груз, получатель и указание погрузки.

| № | Русский | English |
|---|---|---|
| 01 | Принято. Следующий маршрут дальше, и к составу добавится ещё один вагон. | Understood. The next route is longer, and your train will gain one wagon. |
| 02 | Хорошо, Трент. Новый заказ потребует ещё одного вагона и более дальнего рейса. | Good, Trent. The new order calls for one more wagon and a longer run. |
| 03 | Продолжаем. В этот раз состав будет длиннее на один вагон, а путь — дальше. | We will continue. This time the train will be one wagon longer, and the route will take you farther. |
| 04 | Ваше согласие принято. Для следующей перевозки добавляем один вагон и увеличиваем дальность. | Your acceptance is confirmed. The next delivery adds one wagon and increases the distance. |
| 05 | Тогда готовьтесь к более длинному маршруту. Состав увеличится на один вагон. | Then prepare for a longer route. The train will grow by one wagon. |
| 06 | Новый заказ за вами, мистер Трент. Ещё один вагон и следующий, более дальний пункт. | The new order is yours, Mr. Trent. One more wagon, and a destination farther away. |
| 07 | Записываю вас на следующий рейс. Он дальше предыдущего, вагонов будет на один больше. | I am assigning you the next run. It is farther than the last, with one additional wagon. |
| 08 | Решено, работаем дальше. Следующий состав на вагон длиннее, маршрут тоже увеличен. | Settled. We will keep working. The next train is one wagon longer, with an extended route. |
| 09 | Подтверждаю новый заказ. Добавится один вагон, и идти придётся дальше. | New order confirmed. There will be one additional wagon, and farther to travel. |
| 10 | Спасибо, мистер Трент. Следующая доставка дальше, подготовим для вас ещё один вагон. | Thank you, Mr. Trent. The next delivery is farther away. We will prepare one additional wagon for you. |

## Завершение через доставку к планете

Основа `tc_finish_delivery`, count 10. Только ветка завершения с последним грузом. Название планеты добавляется отдельно.

| № | Русский | English |
|---|---|---|
| 01 | Принято, завершаем смену. Доставьте последний груз к отмеченной дружественной планете. | Understood, we are ending your shift. Deliver the final cargo to the marked friendly planet. |
| 02 | Хорошо, Трент. Осталась заключительная доставка к ближайшей дружественной планете. | All right, Trent. One final delivery remains, to the nearest friendly planet. |
| 03 | Новых рейсов не назначаю. Отвезите завершающий груз к указанной планете. | I will assign no further runs. Take the final cargo to the indicated planet. |
| 04 | Мистер Трент, заканчиваем работу последней доставкой. Планета назначения отмечена. | Mr. Trent, we will finish with one last delivery. The destination planet is marked. |
| 05 | Ваше решение принято. Перед сдачей локомотива доставьте груз к указанной планете. | Your decision is confirmed. Before returning the locomotive, deliver the cargo to the indicated planet. |
| 06 | Переходим к завершению смены. Финальный груз ждут у отмеченной дружественной планеты. | We are closing out your shift. The final cargo is expected at the marked friendly planet. |
| 07 | Тогда последний рейс, Трент. Доставьте груз к ближайшей подходящей дружественной планете. | One last run, then, Trent. Deliver the cargo to the nearest suitable friendly planet. |
| 08 | Продолжения цепочки не будет. Выполните заключительную доставку к отмеченной планете. | The chain of orders ends here. Complete the final delivery to the marked planet. |
| 09 | Закрываем смену, мистер Трент. Сначала отвезите оставшийся для сдачи груз к указанной планете. | We are closing your shift, Mr. Trent. First, take the remaining delivery cargo to the indicated planet. |
| 10 | Понял вас. Следуйте с финальным грузом к дружественной планете по указателю. | Understood. Follow the marker to the friendly planet with the final cargo. |

## Завершение через парковку

Основа `tc_park`, count 10. Только ветка завершения с парковкой локомотива.

| № | Русский | English |
|---|---|---|
| 01 | Принято. Припаркуйте локомотив в отмеченной точке, и завершим смену. | Understood. Park the locomotive at the marked position, and we will close your shift. |
| 02 | На сегодня достаточно, Трент. Подведите локомотив к месту стоянки на карте. | That is enough for today, Trent. Bring the locomotive to the parking position on your map. |
| 03 | Новых заказов не выдаю. Доставьте локомотив на указанную стоянку. | No further orders will be assigned. Return the locomotive to the indicated parking position. |
| 04 | Хорошо, мистер Трент. Осталось припарковать локомотив по указателю. | All right, Mr. Trent. All that remains is to park the locomotive at the marker. |
| 05 | Завершаем работу. Место сдачи локомотива отмечено в навигации. | We are finishing work. The locomotive return position is marked in navigation. |
| 06 | Ваш отказ от продолжения принят. Следуйте к отмеченному месту парковки. | Your decision to stop is confirmed. Proceed to the marked parking position. |
| 07 | Трент, возвращайте локомотив на стоянку. Нужную точку я отметил. | Trent, return the locomotive to its parking position. I have marked it for you. |
| 08 | Переходим к сдаче локомотива. Займите указанную парковочную позицию. | We are ready for the locomotive handover. Take the indicated parking position. |
| 09 | До конца смены один манёвр. Припаркуйте локомотив в отмеченном месте. | One manoeuvre remains before your shift ends. Park the locomotive at the marked location. |
| 10 | Мистер Трент, работа на маршруте закончена. Отведите локомотив к указателю стоянки. | Mr. Trent, your route work is finished. Bring the locomotive to the parking marker. |

## Возвращение на личный корабль

Основа `tc_done`, count 10. Звучит после фактического восстановления личного корабля.

| № | Русский | English |
|---|---|---|
| 01 | Смена завершена, мистер Трент. Вы снова на своём корабле. Спасибо за работу. | Your shift is complete, Mr. Trent. You are back aboard your own ship. Thank you for your work. |
| 02 | Локомотив сдан, Трент. Ваш корабль возвращён. До следующей встречи. | The locomotive has been returned, Trent. You have your ship back. Until next time. |
| 03 | Работа закончена. Вы снова управляете своим кораблём. Всего доброго. | The job is complete. You are back in command of your own ship. All the best. |
| 04 | Благодарю за перевозки, мистер Трент. Пересадка завершена, смена закрыта. | Thank you for the deliveries, Mr. Trent. The transfer is complete, and your shift is closed. |
| 05 | Всё оформлено, Трент. Вы на своём корабле и свободны. Конец связи. | Everything is settled, Trent. You are aboard your own ship and free to go. Dispatch out. |
| 06 | Возвращение на ваш корабль подтверждаю. Спасибо за сегодняшнюю работу. | I confirm your return to your own ship. Thank you for your work today. |
| 07 | Мистер Трент, смена закрыта. Ваш корабль снова в вашем распоряжении. | Mr. Trent, your shift is closed. Your ship is yours again. |
| 08 | На этом всё. Вы вернулись на свой корабль. Будем рады снова поработать с вами. | That is everything. You are back aboard your ship. We look forward to working with you again. |
| 09 | Передача завершена, Трент. Личный корабль возвращён, работа выполнена. | Handover complete, Trent. Your own ship has been returned, and the job is done. |
| 10 | Спасибо, мистер Трент. Вы снова на своём корабле. До следующего рейса, конец связи. | Thank you, Mr. Trent. You are back aboard your ship. Until the next run. Dispatch out. |

## Дальнейшая подготовка записи

После выбора правил сдачи можно добавить отдельные семейства для расцепки, неполного состава, потери груза и невозможного маршрута. Эти ситуации пока не имеют утверждённых игровых правил; текущая сотня реплик не задаёт штрафы или условия провала.

Перед включением в игру: проверить 10 клипов на каждое семейство и язык, соответствие count, Voice ID, фактические длительности и воспроизведение в comm-window. Проверить склейку названий баз и товаров на нескольких примерах, постановку YES_NO после реплики и отсутствие повторной оплаты при повторном событии. Для английского сохраняется связь `atc_leg_m01_new` → файлы `dispatcher_en01`, если отдельно не будет принято решение сменить регистрацию голоса.
