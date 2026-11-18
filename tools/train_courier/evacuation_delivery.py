"""Post-exit dispatcher revisions. No unsolicited evacuation briefing."""

INACTIVE_FAMILIES={
    'te_intro','te_confirm_loaded','te_confirm_empty','te_cancel','te_waiting',
    'te_exit_failed','te_return_failed','te_critical','te_emergency_clear',
    'te_delivered','te_access_denied',
}

# EN | RU. Existing IDs are retained so recordings replace the previous takes.
REVISED={
'te_departed': '''
Trent! Where the hell are you going? Get back in that locomotive. You've got one minute!|Трент! Ты куда, чёрт возьми, собрался? Немедленно возвращайся в локомотив. У тебя минута!
What do you think you're doing? That train is your responsibility! Turn around and get back aboard!|Ты что себе позволяешь? За этот состав отвечаешь ты! Разворачивайся и возвращайся на борт!
Hey! You don't get to leave our locomotive out here. Get back to your post. Sixty seconds!|Эй! Наш локомотив здесь бросать нельзя. Вернись на своё место. Шестьдесят секунд!
Trent, this is a delivery job, not a pleasure cruise! Turn that ship around. Back aboard, now!|Трент, у тебя доставка, а не прогулка! Разворачивай корабль. Немедленно обратно на борт!
Where are you running off to? We hired you to drive that locomotive! Get back in there!|Куда ты сбежал? Мы наняли тебя управлять локомотивом! Живо возвращайся!
''',
'te_return_30': '''
Thirty seconds, Trent! Stop wasting our time and get back aboard!|Тридцать секунд, Трент! Хватит тратить наше время. Возвращайся на борт!
I'm still waiting! You've got half a minute to get back in that locomotive!|Я всё ещё жду! У тебя полминуты, чтобы вернуться в локомотив!
This is your last chance to put things right. Thirty seconds. Get back to work!|Это твой последний шанс всё исправить. Тридцать секунд. Вернись к работе!
Don't make me report this! Thirty seconds to get back aboard!|Не заставляй меня докладывать об этом! Тридцать секунд на возвращение!
Turn around, Trent! Thirty seconds left. We're not letting this slide!|Разворачивайся, Трент! Осталось тридцать секунд. С рук тебе это не сойдёт!
''',
'te_return_10': '''
Ten seconds! Get back aboard, now!|Десять секунд! Немедленно обратно на борт!
Trent! Ten seconds. Move it!|Трент! Десять секунд. Шевелись!
Ten seconds left! This is your final warning!|Осталось десять секунд! Последнее предупреждение!
Dock with the locomotive! You've got ten seconds!|Стыкуйся с локомотивом! У тебя десять секунд!
Get back to your post! Ten seconds, Trent!|Вернись на своё место! Десять секунд, Трент!
''',
'te_return_loaded': '''
About time! Hook up the cargo and get moving.|Давно пора! Подцепляй груз и трогай.
You're back. Good. Now finish the delivery.|Вернулся. Хорошо. А теперь закончи доставку.
Finally! That shipment isn't going to deliver itself.|Наконец-то! Груз сам себя не доставит.
Back at your post. Keep it that way. Get the cargo moving.|Снова на месте. Вот и оставайся там. Вези груз.
All right. Couple the wagons and get back to work.|Ладно. Цепляй вагоны и возвращайся к работе.
''',
'te_return_empty': '''
About time, Trent. Stay at your post.|Давно пора, Трент. Оставайся на своём месте.
You're back. Good. Get on with the job.|Вернулся. Хорошо. Продолжай работу.
Finally. Keep that locomotive under control.|Наконец-то. Держи локомотив под контролем.
All right, you're aboard. No more running off.|Ладно, ты на борту. Больше не сбегай.
Back where you belong. Follow your instructions.|Вернулся на своё место? Тогда слушай мои команды.
''',
'te_timeout_loaded': '''
Too late, Trent! You abandoned our locomotive and the cargo. The contract is cancelled. This goes on your record!|Опоздал, Трент! Ты бросил наш локомотив и груз. Контракт расторгнут. Это пойдёт в твой послужной список!
You idiot! You had a whole minute to get back! The train and cargo are lost. You're done with this job.|Ну ты и дурак! У тебя была целая минута, чтобы вернуться! Состав и груз потеряны. С этим заданием покончено.
Time's up! You walked out on our train and our shipment. Contract cancelled. Don't expect us to forget this!|Время вышло! Ты бросил наш состав и наш груз. Контракт расторгнут. Не жди, что мы это забудем!
That's it, Trent! You missed your chance. We've lost the locomotive and the cargo. I'm reporting both losses.|Всё, Трент! Ты упустил свой шанс. Мы потеряли локомотив и груз. Я доложу об обеих потерях.
Unbelievable! You just threw away a locomotive and a shipment. This contract is over, and your employer will hear about it!|Невероятно! Ты просто бросил локомотив вместе с грузом. Контракт закрыт, и работодатель об этом узнает!
''',
'te_timeout_empty': '''
Too late, Trent! You abandoned our locomotive. The contract is cancelled. This goes on your record!|Опоздал, Трент! Ты бросил наш локомотив. Контракт расторгнут. Это пойдёт в твой послужной список!
You idiot! We gave you a whole minute! The locomotive is written off. You're done with this job.|Ну ты и дурак! У тебя была целая минута! Локомотив списан. С этим заданием покончено.
Time's up! You walked out on our locomotive. Contract cancelled. Don't expect us to forget this!|Время вышло! Ты бросил наш локомотив. Контракт расторгнут. Не жди, что мы это забудем!
That's it, Trent! You missed your chance. The locomotive is lost. I'm reporting this to your employer.|Всё, Трент! Ты упустил свой шанс. Локомотив потерян. Я доложу об этом работодателю.
Unbelievable! You just abandoned company equipment. This contract is over, and the loss is on your record!|Невероятно! Ты просто бросил технику компании. Контракт закрыт, а потеря записана на твой счёт!
''',
'te_battle_loaded': '''
The locomotive is gone, and the cargo with it. Damn it, Trent! This contract is over.|Локомотив потерян, и груз вместе с ним. Чёрт возьми, Трент! Контракт закрыт.
We got you out, but we've lost the whole shipment and the locomotive. Your employer will hear about both losses.|Тебя мы вытащили, но весь груз и локомотив потеряны. Работодатель узнает об обеих потерях.
That's the locomotive and the cargo destroyed! The job is finished, Trent. I'm filing the loss report.|Локомотив и груз уничтожены! С заданием покончено, Трент. Я подаю отчёт о потерях.
You're alive. Good. But the train and shipment are gone. Contract cancelled.|Ты жив. Хорошо. Но состава и груза больше нет. Контракт расторгнут.
Damn it! The locomotive and cargo are lost. You're off this contract. Both losses go on your record.|Проклятье! Локомотив и груз потеряны. Ты отстранён от этого контракта. Обе потери пойдут в отчёт.
''',
'te_battle_empty': '''
The locomotive is gone. Damn it, Trent! This contract is over.|Локомотив потерян. Чёрт возьми, Трент! Контракт закрыт.
We got you out, but we've lost the locomotive. Your employer will hear about this.|Тебя мы вытащили, но локомотив потерян. Работодатель об этом узнает.
That's the locomotive destroyed! The job is finished, Trent. I'm filing the loss report.|Локомотив уничтожен! С заданием покончено, Трент. Я подаю отчёт о потере.
You're alive. Good. But that locomotive is gone. Contract cancelled.|Ты жив. Хорошо. Но локомотива больше нет. Контракт расторгнут.
Damn it! We've lost the locomotive. You're off this contract. The loss goes on your record.|Проклятье! Мы потеряли локомотив. Ты отстранён от этого контракта. Потеря пойдёт в отчёт.
''',
}

def delivery_spec(family):
    if family not in REVISED:return None
    anger=.6 if family.startswith('te_return_') and family not in ('te_return_30','te_return_10') else .9
    return {'code':'courier_angry','engine':'indextts2','emo_vector':[0,anger,0,0,0,0,0,.1],'speed':1.0}
