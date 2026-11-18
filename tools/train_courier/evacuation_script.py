"""EN/RU recording script: 65 active radio lines, 55 archived and 8 optional.

No audio or final THN is generated. Each radio family has five interchangeable
complete sentences. Amounts stay in the live UI, so empathy tuning cannot make
recordings lie. Urgent lines must interrupt obsolete return/dispatch speech.
"""
import csv
import hashlib
from evacuation_delivery import INACTIVE_FAMILIES, REVISED, delivery_spec
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/train_courier/evacuation'

# EN | RU. The selected take is a complete line, without concatenated fragments.
FAMILIES={
'te_intro':('First successful boarding; once per shift',10,'''
Your own ship is ready for evacuation. A voluntary exit gives you one minute to return. You are responsible for the locomotive and its cargo.|Ваш корабль готов к эвакуации. После добровольного выхода у вас будет минута на возвращение. За локомотив и груз отвечаете вы.
Emergency evacuation is available beside the coupling control. Read the warning before confirming. An abandoned locomotive will be written off.|Кнопка эвакуации находится рядом со сцепкой. Прочитайте предупреждение перед подтверждением. Брошенный локомотив будет списан.
You may leave the locomotive, but return within a minute. Critical hull damage triggers automatic rescue and the loss of the locomotive.|Вы можете покинуть локомотив, но вернитесь за минуту. Критический урон корпусу запускает автоматическое спасение и означает потерю локомотива.
Keep the delivery deadline in mind. Evacuation does not stop it. Losing the train or its cargo will damage your standing with your employer.|Следите за сроком доставки. Эвакуация его не останавливает. Потеря локомотива или груза ухудшит отношение работодателя.
Your contract includes responsibility for the locomotive. Evacuate if necessary, but complete your return within sixty seconds to retain control.|По контракту вы отвечаете за локомотив. При необходимости эвакуируйтесь, но завершите возвращение за шестьдесят секунд, чтобы сохранить управление.
'''),
'te_confirm_loaded':('Open evacuation confirmation with undelivered order',30,'''
You have undelivered cargo. If you leave, return within one minute or both the locomotive and the order will be written off.|У вас недоставленный груз. Если покинете локомотив, вернитесь за минуту, иначе техника и заказ будут списаны.
Confirm only if you intend to evacuate. The cargo stays here, and the delivery deadline continues.|Подтверждайте, только если хотите эвакуироваться. Груз останется здесь, а срок доставки продолжит идти.
Leaving does not cancel your responsibility for this shipment. You will have sixty seconds to return aboard.|Выход не снимает с вас ответственности за груз. На возвращение у вас будет шестьдесят секунд.
The locomotive and cargo will remain at this position. Missing the return deadline means a failed mission and reputation penalties.|Локомотив и груз останутся на этой позиции. Не успеете вернуться — миссия будет провалена, а репутация снизится.
Check the penalties on your display before confirming. You can still cancel and remain at the controls.|Перед подтверждением проверьте штрафы на экране. Ещё можно отменить выход и остаться за управлением.
'''),
'te_confirm_empty':('Open confirmation without undelivered order',30,'''
There is no undelivered cargo, but you remain responsible for the locomotive. Return within sixty seconds if you leave.|Недоставленного груза нет, но за локомотив вы отвечаете. Если выйдете, вернитесь за шестьдесят секунд.
You may evacuate to your own ship. The locomotive will be written off if you fail to return within a minute.|Вы можете эвакуироваться на свой корабль. Если не вернётесь за минуту, локомотив будет списан.
This exit carries a risk to your standing. The warning shows the locomotive loss penalty. Confirm when ready.|Этот выход связан с риском для репутации. В предупреждении указан штраф за локомотив. Подтверждайте, когда будете готовы.
Your completed deliveries remain settled. You still need to return to this locomotive within one minute after leaving.|Завершённые доставки остаются зачтёнными. После выхода вам всё равно нужно вернуться в локомотив за минуту.
No cargo penalty applies to this exit, but losing the locomotive will still count against you. Read the warning carefully.|Штрафа за груз в этой ситуации нет, но потеря локомотива всё равно будет учтена. Внимательно прочитайте предупреждение.
'''),
'te_cancel':('No, Escape or closing confirmation',20,'''
Evacuation cancelled. You retain control.|Эвакуация отменена. Управление остаётся у вас.
Understood. Staying aboard the locomotive.|Понятно. Вы остаётесь в локомотиве.
Exit cancelled. Continue your assignment.|Выход отменён. Продолжайте задание.
The evacuation request is cancelled. No return countdown has started.|Запрос эвакуации отменён. Отсчёт возвращения не запускался.
Confirmed: you are remaining at the controls.|Принято: вы остаётесь за управлением.
'''),
'te_waiting':('Exit accepted; waiting for safe flight state; once per attempt',40,'''
Evacuation requested. Stand by for a safe transfer.|Эвакуация запрошена. Ожидайте безопасной пересадки.
Preparing your ship. The return countdown has not started yet.|Готовим ваш корабль. Отсчёт возвращения ещё не начался.
Hold position while the transfer is prepared.|Сохраняйте положение, пока готовится пересадка.
The exit is being prepared. You still control the locomotive.|Выход готовится. Вы пока управляете локомотивом.
Stand by. We must complete the current flight transition before transferring control.|Ожидайте. Перед передачей управления нужно завершить текущий переход.
'''),
'te_exit_failed':('Voluntary transfer rolled back',50,'''
Transfer failed. You remain aboard. The return countdown has not started.|Пересадка не удалась. Вы остались на борту. Отсчёт возвращения не начался.
We could not complete the exit. You still have control of the locomotive.|Завершить выход не удалось. Вы по-прежнему управляете локомотивом.
Evacuation did not complete. No abandonment has been recorded.|Эвакуация не завершена. Оставление техники не зафиксировано.
The transfer was cancelled before control changed. You remain in the locomotive.|Пересадка отменена до передачи управления. Вы остаётесь в локомотиве.
Exit unsuccessful. Keep control and request evacuation again when ready.|Выход не состоялся. Сохраняйте управление и повторите запрос, когда будете готовы.
'''),
'te_departed':('Voluntary transfer committed; start 60 seconds',60,'''
You are aboard your own ship. Sixty seconds to return to the locomotive.|Вы на своём корабле. На возвращение в локомотив — шестьдесят секунд.
Evacuation complete. The locomotive is marked. Return within one minute.|Эвакуация завершена. Локомотив отмечен. Вернитесь в течение минуты.
Your ship is under your control. The return countdown has started.|Ваш корабль под вашим управлением. Отсчёт возвращения начался.
You have left the locomotive. Complete docking with it before the minute expires.|Вы покинули локомотив. Завершите стыковку с ним до истечения минуты.
Transfer complete. You have sixty seconds to take the locomotive back.|Пересадка завершена. У вас шестьдесят секунд, чтобы вновь занять локомотив.
'''),
'te_return_30':('Cross 30 seconds remaining; suppress after return or loss',70,'''
Thirty seconds remain. Return to the marked locomotive.|Осталось тридцать секунд. Возвращайтесь к отмеченному локомотиву.
Half a minute to return aboard. Complete docking in time.|Полминуты на возвращение. Завершите стыковку вовремя.
Thirty seconds. Selecting the locomotive alone does not complete your return.|Тридцать секунд. Одного выбора локомотива целью недостаточно для возвращения.
Return warning: thirty seconds remaining.|Предупреждение о возвращении: осталось тридцать секунд.
You have thirty seconds to regain control of the locomotive.|У вас тридцать секунд, чтобы снова принять управление локомотивом.
'''),
'te_return_10':('Cross 10 seconds remaining; supersedes 30 second warning',80,'''
Ten seconds! Complete your return now.|Десять секунд! Завершайте возвращение.
Only ten seconds remain before access closes.|До закрытия доступа осталось десять секунд.
Final warning. Ten seconds to return aboard.|Последнее предупреждение. Десять секунд на возвращение.
Ten seconds left. The return must be completed before time runs out.|Осталось десять секунд. Возвращение нужно завершить до истечения срока.
Return immediately. You have ten seconds.|Возвращайтесь немедленно. У вас десять секунд.
'''),
'te_return_loaded':('Return committed with active order; cancel countdown warnings',60,'''
Control restored. Recover your assigned cargo and continue the delivery.|Управление восстановлено. Заберите назначенный груз и продолжайте доставку.
You are back aboard. The original shipment still needs to reach its destination.|Вы снова на борту. Прежний груз ещё нужно доставить получателю.
Return confirmed. Couple your cargo again and resume the route.|Возвращение подтверждено. Снова подцепите груз и продолжайте маршрут.
You made it back in time. The delivery deadline has continued running.|Вы вернулись вовремя. Срок доставки всё это время продолжал идти.
Locomotive control is yours again. Damage has not been repaired; continue with care.|Вы снова управляете локомотивом. Повреждения не устранены; продолжайте осторожно.
'''),
'te_return_empty':('Return committed without active order',60,'''
You are back aboard. Continue with your current assignment.|Вы снова на борту. Продолжайте текущее назначение.
Control restored. The return countdown is cancelled.|Управление восстановлено. Отсчёт возвращения прекращён.
Return confirmed. The locomotive remains your responsibility.|Возвращение подтверждено. Локомотив по-прежнему под вашей ответственностью.
You returned in time. Follow your existing instructions.|Вы вернулись вовремя. Следуйте действующим указаниям.
Locomotive control restored. Any existing damage remains.|Управление локомотивом восстановлено. Все прежние повреждения сохранены.
'''),
'te_return_failed':('Return attempt rolled back while grace time remains',65,'''
Return incomplete. You are still in your ship, and the countdown continues.|Возвращение не завершено. Вы ещё на своём корабле, отсчёт продолжается.
The transfer back failed. Check the remaining time before another attempt.|Пересадка обратно не удалась. Проверьте оставшееся время перед новой попыткой.
You have not regained control yet. The return deadline still applies.|Вы ещё не восстановили управление. Срок возвращения остаётся в силе.
Docking has not completed the transfer. Your return timer is still running.|Стыковка не завершила пересадку. Таймер возвращения продолжает идти.
Return unsuccessful. The locomotive must still be boarded before time expires.|Вернуться не удалось. Нужно занять локомотив до истечения времени.
'''),
'te_timeout_loaded':('Grace time expired with undelivered order; once',90,'''
Time expired. The locomotive and undelivered cargo are written off. Your mission has failed.|Время вышло. Локомотив и недоставленный груз списаны. Миссия провалена.
You did not return in time. Access is closed, and both losses are entered in your record.|Вы не вернулись вовремя. Доступ закрыт, обе потери внесены в ваш отчёт.
The return deadline has passed. Your employer records the loss of the locomotive and shipment.|Срок возвращения истёк. Работодатель фиксирует потерю локомотива и груза.
The locomotive has been abandoned with an unfinished order. This shift is closed as a failure.|Локомотив оставлен с невыполненным заказом. Эта смена закрыта как неудачная.
One minute has elapsed. The locomotive and cargo are no longer available to you.|Минута истекла. Локомотив и груз больше вам недоступны.
'''),
'te_timeout_empty':('Grace time expired without undelivered order; once',90,'''
Time expired. The locomotive is written off. Your mission has failed.|Время вышло. Локомотив списан. Миссия провалена.
You did not return in time. Locomotive access is closed and its loss is recorded.|Вы не вернулись вовремя. Доступ к локомотиву закрыт, его потеря зафиксирована.
The return deadline has passed. Your employer records a locomotive loss.|Срок возвращения истёк. Работодатель фиксирует потерю локомотива.
The locomotive has been abandoned. This shift is closed as a failure.|Локомотив брошен. Эта смена закрыта как неудачная.
One minute has elapsed. The locomotive is no longer available to you.|Минута истекла. Локомотив больше вам недоступен.
'''),
'te_access_denied':('Docking attempt at a written-off locomotive; throttle repeated requests',50,'''
Access denied. That locomotive has already been written off.|Доступ запрещён. Этот локомотив уже списан.
You cannot return to this locomotive. The shift has ended.|Вернуться в этот локомотив нельзя. Смена завершена.
The return window is closed. Docking authorization has been withdrawn.|Время возвращения истекло. Разрешение на стыковку отозвано.
This locomotive is locked. Your previous assignment is closed.|Этот локомотив заблокирован. Ваше прежнее задание закрыто.
Boarding is unavailable. The loss has already been recorded.|Посадка недоступна. Потеря уже зафиксирована.
'''),
'te_critical':('Hull reaches 5 percent or a lethal hit is intercepted; highest priority',100,'''
Critical hull damage! Automatic evacuation!|Критическое повреждение корпуса! Автоматическая эвакуация!
Hull integrity critical. Emergency transfer now!|Корпус в критическом состоянии. Экстренная пересадка!
The locomotive is failing. Automatic rescue engaged!|Локомотив разрушается. Автоматическое спасение включено!
Emergency! Evacuating the locomotive!|Авария! Эвакуация из локомотива!
Critical hull breach. Transferring you to your ship!|Критическое разрушение корпуса. Переводим вас на ваш корабль!
'''),
'te_emergency_clear':('Emergency transfer committed; destruction proceeds without waiting for speech',95,'''
You are clear. The locomotive is being destroyed. Do not return.|Вы вышли из опасной зоны. Локомотив уничтожается. Не возвращайтесь.
Emergency transfer complete. The locomotive cannot be recovered.|Аварийная пересадка завершена. Вернуть локомотив невозможно.
You are aboard your own ship. The locomotive is lost.|Вы на своём корабле. Локомотив потерян.
Rescue complete. Locomotive self-destruction is proceeding.|Спасение завершено. Идёт самоуничтожение локомотива.
You are clear of the locomotive. There is no return window after this evacuation.|Вы покинули локомотив. После этой эвакуации времени на возвращение нет.
'''),
'te_battle_loaded':('Locomotive destroyed with undelivered cargo; once',90,'''
Locomotive destroyed. The undelivered shipment is also lost. Your employer has recorded both losses.|Локомотив уничтожен. Недоставленный груз также утрачен. Работодатель зафиксировал обе потери.
We have lost the locomotive and its outstanding cargo. This mission is over.|Мы потеряли локомотив и недоставленный груз. Миссия завершена.
The locomotive loss is confirmed. The unfinished delivery is recorded as a cargo loss as well.|Потеря локомотива подтверждена. Незавершённая доставка также учтена как потеря груза.
Your shift has failed. The locomotive and shipment have both been written off.|Смена провалена. Локомотив и груз списаны.
The train is lost and the cargo was not delivered. Your standing has been adjusted under the contract.|Локомотив потерян, груз не доставлен. Ваша репутация изменена по условиям контракта.
'''),
'te_battle_empty':('Locomotive destroyed without undelivered cargo; once',90,'''
Locomotive destroyed. Your employer has recorded the loss. This mission is over.|Локомотив уничтожен. Работодатель зафиксировал потерю. Миссия завершена.
The locomotive is lost. There is no outstanding shipment to write off.|Локомотив потерян. Недоставленного груза для списания нет.
Your shift has failed because the locomotive was destroyed.|Смена провалена из-за уничтожения локомотива.
The equipment loss is confirmed. Completed deliveries remain settled.|Потеря техники подтверждена. Завершённые доставки остаются зачтёнными.
The locomotive has been written off. Your standing reflects the equipment loss.|Локомотив списан. Потеря техники учтена в вашей репутации.
'''),
'te_late':('First crossing of delivery deadline; once per accepted order',55,'''
The delivery deadline has passed. The violation is recorded, but the customer still needs the cargo.|Срок доставки истёк. Нарушение зафиксировано, но заказчику всё ещё нужен груз.
You are late. Your employer has recorded the missed deadline. Continue the delivery.|Вы опаздываете. Работодатель зафиксировал нарушение срока. Продолжайте доставку.
This shipment is overdue. Bring it to the customer; the deadline penalty will remain.|Этот груз просрочен. Доставьте его заказчику; штраф за срок останется.
The receiving crew is still waiting. Your delay has been entered in the report.|Приёмная смена всё ещё ждёт. Ваше опоздание внесено в отчёт.
Delivery time has expired. The order remains active, with the delay recorded.|Время доставки истекло. Заказ остаётся активным, опоздание зафиксировано.
'''),
'te_delivered':('On-time handover; cash only, no reputation reward',30,'''
Cargo accepted. Payment has been transferred. Await your next instructions.|Груз принят. Оплата переведена. Ожидайте дальнейших указаний.
Delivery confirmed. This order is settled.|Доставка подтверждена. Этот заказ закрыт.
The customer has received the shipment. Your delivery payment is complete.|Заказчик получил груз. Оплата доставки выполнена.
The shipment arrived on time and has been accepted.|Груз прибыл вовремя и принят получателем.
Order completed. The receiving crew has taken responsibility for the cargo.|Заказ выполнен. Приёмная смена приняла груз под свою ответственность.
'''),
'te_delivered_late':('Late handover; do not apply a second deadline penalty',30,'''
Late cargo accepted and paid. The missed deadline remains on your record.|Просроченный груз принят и оплачен. Нарушение срока остаётся в отчёте.
Delivery complete. Payment is settled, but the earlier deadline penalty remains.|Доставка завершена. Оплата произведена, но прежний штраф за срок остаётся.
The customer has accepted the overdue shipment. The delay is not erased.|Заказчик принял просроченный груз. Опоздание не аннулируется.
This late order is closed. Your recorded delay remains unchanged.|Этот просроченный заказ закрыт. Запись об опоздании остаётся в силе.
The cargo is delivered. There is no additional deadline penalty for this handover.|Груз доставлен. Дополнительного штрафа за срок при этой сдаче нет.
'''),
'te_order_abandoned':('Explicit abort of an accepted undelivered order',70,'''
The accepted order has been abandoned. Return the locomotive through the normal procedure.|Принятый заказ брошен. Верните локомотив штатным порядком.
Cargo abandonment is recorded. You are still responsible for returning the locomotive.|Отказ от доставки груза зафиксирован. Вы по-прежнему обязаны вернуть локомотив.
You have cancelled an unfinished delivery. The cargo loss penalty applies.|Вы отменили незавершённую доставку. Применяется штраф за груз.
The order is closed as abandoned. Follow the parking instructions for the locomotive.|Заказ закрыт как брошенный. Следуйте указаниям по парковке локомотива.
Your employer has recorded the undelivered shipment. Bring the locomotive back safely.|Работодатель зафиксировал недоставленный груз. Верните локомотив в сохранности.
'''),
'te_cargo_destroyed':('Assigned consist destroyed while locomotive is not lost',75,'''
Assigned cargo destroyed. The delivery has failed. The locomotive must still be returned.|Назначенный груз уничтожен. Доставка провалена. Локомотив ещё нужно вернуть.
The shipment is lost. Your employer has recorded a cargo loss.|Груз утрачен. Работодатель зафиксировал потерю груза.
We have lost the entire assigned consist. Preserve the locomotive and follow the return instructions.|Мы потеряли весь назначенный состав. Сохраните локомотив и следуйте указаниям по возвращению.
Cargo destruction confirmed. This order can no longer be completed.|Уничтожение груза подтверждено. Выполнить этот заказ больше нельзя.
The delivery has failed because the cargo was destroyed. The locomotive has not been written off.|Доставка провалена из-за уничтожения груза. Локомотив не списан.
'''),
}

BAR=[
('ask_exit','player','Can I leave the locomotive in an emergency?','Можно покинуть локомотив в аварийной ситуации?'),
('explain_exit','vendor','Yes. The evacuation button is beside the coupling control. Confirm the warning to return to your own ship. You then have sixty seconds to dock with the locomotive again. The delivery deadline keeps running.','Да. Кнопка эвакуации рядом со сцепкой. Подтвердите предупреждение, чтобы вернуться на свой корабль. Затем у вас будет шестьдесят секунд, чтобы снова состыковаться с локомотивом. Срок доставки продолжит идти.'),
('ask_damage','player','What happens if the locomotive takes critical damage?','Что будет, если локомотив получит критические повреждения?'),
('explain_damage','vendor','At five percent hull integrity, automatic rescue transfers you to your own ship. The locomotive then self-destructs. There is no opportunity to return, and the shift fails.','При пяти процентах прочности корпуса автоматическое спасение переведёт вас на свой корабль. Затем локомотив самоуничтожится. Возможности вернуться уже не будет, а смена завершится провалом.'),
('ask_penalties','player','How do losses affect my standing?','Как потери повлияют на мою репутацию?'),
('explain_penalties','vendor','Your contract shows the employer and penalties. A late delivery, an abandoned shipment and a lost locomotive are recorded separately. Undelivered cargo is also lost when its locomotive is written off. Related factions react through their ties to the employer. Delivery itself carries no reputation bonus.','В наряде указаны работодатель и штрафы. Просрочка, брошенный груз и потеря локомотива учитываются отдельно. При списании локомотива недоставленный груз тоже считается потерянным. Связанные фракции реагируют через отношения с работодателем. Сама доставка репутационного бонуса не даёт.'),
('ask_return','player','What if I leave voluntarily and do not return?','Что, если я выйду добровольно и не вернусь?'),
('explain_return','vendor','Once the minute expires, access closes and the mission fails. The locomotive is written off together with any undelivered cargo. Starting a docking request is not enough: you must complete the return before time runs out.','После истечения минуты доступ закроется, а миссия будет провалена. Локомотив спишут вместе с недоставленным грузом. Одного запроса стыковки недостаточно: нужно завершить возвращение до истечения времени.'),
]

def rows():
    result=[]
    for family,(trigger,priority,source) in FAMILIES.items():
        lines=[s.strip().split('|') for s in REVISED.get(family,source).strip().splitlines()]
        assert len(lines)==5 and all(len(line)==2 for line in lines),family
        for i,(en,ru) in enumerate(lines,1):
            result.append(dict(id=f'{family}_{i:02}-',family=family,variant=i,speaker='dispatcher',
                trigger=trigger,priority=priority,en=en,ru=ru,active=family not in INACTIVE_FAMILIES,
                delivery=delivery_spec(family),
                cancel_when='Condition no longer applies; critical/loss/return supersedes countdown speech'))
    for name,speaker,en,ru in BAR:
        result.append(dict(id='te_bar_'+name,family='bar',variant=1,speaker=speaker,
            trigger='Optional bar briefing: '+name,priority=10,en=en,ru=ru,active=False,
            cancel_when='Conversation closed'))
    assert len(result)==128 and len({r['id'] for r in result})==128
    return result

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    records=rows()
    audio_manifest=OUT/'audio_en/recordings.json'
    recordings=json.loads(audio_manifest.read_text(encoding='utf-8')) if audio_manifest.exists() else {}
    recorded=0
    for row in records:
        audio=OUT/'audio_en'/(row['id']+'.wav');record=recordings.get(row['id'],{})
        if audio.exists() and record.get('text')==row['en'] and hashlib.sha256(audio.read_bytes()).hexdigest()==record.get('sha256'):
            recorded+=1
    status='english_recorded' if recorded==len(records) else 'english_recording_partial' if recorded else 'text_ready_audio_not_generated'
    active=sum(r['active'] for r in records)
    revised=sum(bool(r.get('delivery')) for r in records)
    (OUT/'recording_script.json').write_text(json.dumps(dict(schema=2,status=status,english_recordings=recorded,
        active_radio_lines=active,revised_post_exit_lines=revised,
        english_first=True,dispatcher_voice_en='atc_leg_m01_new',lines=records),ensure_ascii=False,indent=2),encoding='utf-8')
    for language in ('en','ru'):
        with (OUT/f'recording_{language}.csv').open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.writer(stream);writer.writerow(['id','speaker','status','delivery','trigger','priority','text'])
            for row in records:
                usage='active' if row['active'] else 'optional_unconnected' if row['family']=='bar' else 'archived_inactive'
                style=(row.get('delivery') or {}).get('code','neutral')
                writer.writerow([row['id'],row['speaker'],usage,style,row['trigger'],row['priority'],row[language]])
    print(f'Prepared 128 EN + 128 RU texts: {active} active radio lines, {revised} revised post-exit lines; '
          f'{recorded} existing English recordings verified. No THN generated.')

if __name__=='__main__':main()
