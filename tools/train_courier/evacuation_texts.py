"""Stable bilingual evacuation UI. Rates are formatted from empathy at runtime."""
from xml.sax.saxutils import escape

def rdl(*paragraphs):
    return '<?xml version="1.0" encoding="UTF-16"?><RDL><PUSH/>'+''.join(
        '<TEXT>'+escape(p)+'</TEXT><PARA/><PARA/>' for p in paragraphs)+'<POP/></RDL>'

TEXTS = [
('title','Покинуть локомотив?','Leave the locomotive?'),
('confirm_loaded',rdl(
    'Вы вернётесь на свой корабль. Локомотив и груз останутся здесь.',
    'У вас будет 60 секунд на возвращение. Срок доставки продолжит идти. Если локомотив будет потерян или вы не вернётесь вовремя, миссия завершится провалом, а локомотив и груз станут недоступны.',
    'Работодатель: %F0. За локомотив: %!0. За недоставленный груз: %!1. Всего: %!2. За просрочку отдельно: %!3, один раз. Связанные фракции отреагируют согласно своим отношениям с работодателем.',
    'При критическом повреждении спасение включается автоматически, после чего локомотив самоуничтожается. Вернуться в него уже нельзя.',
    'Точно хотите эвакуироваться?'),rdl(
    'You will return to your own ship. The locomotive and cargo will remain here.',
    'You have 60 seconds to return aboard. The delivery deadline keeps running. If the locomotive is lost or you fail to return in time, the mission fails and the locomotive and cargo become unavailable.',
    'Employer: %F0. Locomotive loss: %!0. Undelivered cargo: %!1. Total: %!2. A separate late-delivery penalty of %!3 applies once. Related factions react according to their ties to your employer.',
    'Critical hull damage triggers automatic evacuation, followed by locomotive self-destruction. There is no return in that case.',
    'Are you sure you want to evacuate?')),
('confirm_empty',rdl(
    'Вы вернётесь на свой корабль. У вас будет 60 секунд на возвращение в локомотив.',
    'Если локомотив будет потерян или вы не вернётесь вовремя, миссия завершится провалом, а локомотив станет недоступен.',
    'Работодатель: %F0. Потеря локомотива: %!0. Недоставленного груза сейчас нет. Связанные фракции также отреагируют.',
    'Критическое повреждение вызывает автоматическое спасение и самоуничтожение локомотива без возможности возвращения.',
    'Точно хотите эвакуироваться?'),rdl(
    'You will return to your own ship. You have 60 seconds to return aboard the locomotive.',
    'If the locomotive is lost or you fail to return in time, the mission fails and the locomotive becomes unavailable.',
    'Employer: %F0. Locomotive loss: %!0. You have no undelivered cargo. Related factions will also react.',
    'Critical hull damage triggers automatic rescue and locomotive self-destruction, with no opportunity to return.',
    'Are you sure you want to evacuate?')),
('return_objective','Вернитесь на локомотив: выберите его и выполните стыковку до истечения минуты.','Return to the locomotive: select it and complete docking before the minute expires.'),
('return_timer','Вернуться на локомотив','Return aboard in'),
('employer','Работодатель: %F0','Employer: %F0'),
('reputation','%F0: %!0 — %s0','%F0: %!0 — %s0'),
('delivered','Груз доставлен.','Cargo delivered.'),
('late','Срок доставки истёк. Груз всё ещё ждут.','The delivery deadline has passed. The cargo is still required.'),
('cargo_lost','Недоставленный груз утрачен.','Undelivered cargo lost.'),
('locomotive_lost','Локомотив потерян.','Locomotive lost.'),
('evacuated','Вы на своём корабле. На возвращение в локомотив — 60 секунд.','You are aboard your own ship. You have 60 seconds to return to the locomotive.'),
('warning30','На возвращение осталось 30 секунд. Завершите стыковку вовремя.','30 seconds to return. Complete docking before time runs out.'),
('warning10','Осталось 10 секунд! После истечения срока доступ к локомотиву закроется.','10 seconds left! Locomotive access closes when time expires.'),
('returned','Управление локомотивом восстановлено. Повреждения сохранены.','Locomotive control restored. Existing damage remains.'),
('timeout_loaded','Время вышло. Локомотив и груз списаны. Доступ закрыт, миссия провалена.','Time expired. Locomotive and cargo written off. Access closed; mission failed.'),
('timeout_empty','Время вышло. Локомотив списан. Доступ закрыт, миссия провалена.','Time expired. Locomotive written off. Access closed; mission failed.'),
('critical','Критическое повреждение корпуса! Автоматическая эвакуация.','Critical hull damage! Automatic evacuation.'),
('battle_loaded','Вы спасены. Локомотив уничтожен, груз утрачен. Миссия провалена.','You are safe. Locomotive destroyed and cargo lost. Mission failed.'),
('battle_empty','Вы спасены. Локомотив уничтожен. Миссия провалена.','You are safe. Locomotive destroyed. Mission failed.'),
('access_denied','Этот локомотив списан. Возвращение невозможно.','This locomotive has been written off. Return is unavailable.'),
('exit_failed','Пересадка не завершена. Вы остаётесь в локомотиве; минута не началась.','Transfer did not complete. You remain aboard the locomotive; the return timer has not started.'),
('waiting','Готовится безопасный выход.','Preparing a safe exit.'),
('late_delivered','Просроченный груз принят и оплачен. Репутационный штраф остаётся.','Late cargo accepted and paid. The reputation penalty remains.'),
('cancel','Эвакуация отменена.','Evacuation cancelled.'),
('return_failed','Возвращение не завершено. Таймер продолжает идти.','Return did not complete. The timer is still running.'),
('rate','%s0%d0.%d1%d2%d3%d4','%s0%d0.%d1%d2%d3%d4'),
('plus','+','+'),('minus','−','−'),
('order_employer','%F0\n\n%!0','%F0\n\n%!0'),
]

def rows():
    from order_texts import summary
    result=[('evac_'+key,239300+i,ru,en) for i,(key,ru,en) in enumerate(TEXTS)]
    descriptions=[]
    for language in ('ru','en'):
        conditions=('Работодатель: %F0. Репутация: просрочка %!1; груз утрачен %!2; локомотив потерян %!3. '
            'Бонуса за доставку нет. Связанные фракции реагируют через отношения с работодателем. '
            'Добровольная эвакуация: 60 секунд на возвращение. Критический корпус: спасение и самоуничтожение.' if language=='ru' else
            'Employer: %F0. Reputation: late delivery %!1; cargo lost %!2; locomotive lost %!3. '
            'No delivery reputation bonus. Related factions react through their ties to your employer. '
            'Voluntary evacuation allows 60 seconds to return. Critical hull damage triggers rescue and self-destruction.')
        descriptions.append(summary(language,True).replace('<PUSH/>','<PUSH/><TEXT>'+escape(conditions)+'</TEXT><PARA/><PARA/>',1))
    result[-1]=('evac_order_employer',239329,*descriptions)
    return result
