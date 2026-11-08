"""English recording script. Only new courier dialogue, no base/commodity names.

Each family has ten interchangeable takes. '+' clips continue into another
fragment; '-' clips finish a sentence. Names come from Pythonlancer voices.
"""
VOICE = 'atc_leg_m01_new'
FOLDER = 'dispatcher_en01'
FAMILIES = {
    'tc_board': ('-', [
        'Hello, Mr. Trent. Your locomotive is waiting by the docking fixture. Dock with it to begin your shift.',
        'Freight dispatch here. Your locomotive is ready. Follow the marker and dock with it to take over.',
        'Welcome aboard, Trent. First, dock with the locomotive waiting beside the docking fixture.',
        'Mr. Trent, your locomotive is marked on the navigation display. Approach it and request docking.',
        'Dispatch to Trent. The locomotive is ready for you. Dock with it, and I will send you your first order.',
        'Your shift is confirmed. Head for the marked locomotive and dock with it to take the controls.',
        'Good to hear from you, Mr. Trent. The locomotive is waiting at the fixture. Dock with it when you are ready.',
        'We have a locomotive ready for you, Trent. Its position is marked. Dock with it to start work.',
        'Freight control calling. Take over the locomotive at the marked position by docking with it.',
        'Mr. Trent, everything is ready for your shift. Dock with the locomotive beside the docking fixture.',
    ]),
    'tc_order': ('+', [
        'We have an order for',
        'Mr. Trent, your assignment is a shipment of',
        'Dispatch has a delivery order for',
        'Your cargo for this run is',
        'Trent, we need you to transport',
        'The shipment assigned to you contains',
        'Here are your instructions. You will be carrying',
        'I have a freight order for you. The cargo is',
        'Mr. Trent, we have a shipment ready. You will be delivering',
        'This run is a delivery of',
    ]),
    'tc_destination': ('+', [
        'for delivery to',
        'bound for',
        'to be delivered to',
        'consigned to',
        'for transport to',
        'destined for',
        'for shipment to',
        'with delivery requested at',
        'with the delivery point at',
        'with the receiving depot at',
    ]),
    'tc_collect': ('-', [
        'Collect the cargo at the marked waypoint. Bring the rear of your locomotive close to the wagons\' coupling point, then use the coupling manoeuvre to attach the train.',
        'The loaded wagons are waiting at the marked waypoint. Approach their coupling point with the rear of your locomotive and use the coupling manoeuvre to connect them.',
        'Pick up the shipment at the indicated waypoint. Line up the rear of your locomotive with the wagons\' coupling point, move close, and activate the coupling manoeuvre.',
        'Your wagons are marked on the navigation display. Back the locomotive towards their coupling point, then use the coupling manoeuvre to attach them.',
        'Go to the marked pickup point. Bring the back of your locomotive up to the coupling point on the wagons and engage the coupling manoeuvre.',
        'The cargo is ready at the waypoint. Approach the wagons stern first, line up with their coupling point, and use the coupling manoeuvre to secure the train.',
        'Follow the waypoint to your loaded wagons. Move the rear of the locomotive close to their coupling point, then activate the coupling manoeuvre.',
        'Collect the assigned wagons at the marked location. Back towards their coupling point and use the coupling manoeuvre once your locomotive is close.',
        'The pickup location is marked. Align the rear of your locomotive with the wagons\' coupling point, approach carefully, and engage the coupling manoeuvre.',
        'Proceed to the pickup waypoint. Bring your locomotive into position with its rear near the wagons\' coupling point, then use the coupling manoeuvre to attach the train.',
    ]),
    'tc_depart': ('+', [
        'Coupling confirmed. Deliver this shipment to',
        'The wagons are attached, Mr. Trent. Take the cargo to',
        'Your train is connected. Proceed with the delivery to',
        'Cargo secured. Your delivery point is at',
        'You are ready to depart, Trent. Deliver the cargo to',
        'The coupling is secure. Head for the receiving depot at',
        'Train connection confirmed. Transport the shipment to',
        'All set, Mr. Trent. Follow the route and deliver the shipment to',
        'The wagons are connected. Take this load to',
        'Dispatch confirms the coupling. Your destination is',
    ]),
    'tc_arrival': ('-', [
        'You have reached the delivery area. Bring the wagons to a stop at the marker, then uncouple them.',
        'This is the receiving point, Trent. Stop the loaded wagons inside the marked area and release the coupling.',
        'You are at the depot. Position the wagons at the delivery marker, come to a halt, and uncouple.',
        'The delivery area is ahead. Bring the train to a stop with the wagons at the marker, then detach them.',
        'Mr. Trent, leave the loaded wagons in the marked delivery area. Stop first, then uncouple the train.',
        'Your receiving point is marked. Move the wagons into position, bring them to a halt, and release the coupling.',
        'You are close enough to make the delivery. Stop the wagons at the marker and uncouple them.',
        'Dispatch to Trent. Park the loaded wagons within the delivery area, then uncouple once they have stopped.',
        'This is where the shipment is due. Leave the wagons stationary at the marker and detach the locomotive.',
        'Approach the delivery marker carefully. Stop the loaded wagons inside the marked area, then release them.',
    ]),
    'tc_paid': ('-', [
        'Delivery confirmed. Your payment has been transferred.',
        'The shipment is received, Mr. Trent. Payment is in your account.',
        'Cargo accepted. You have been paid for this delivery.',
        'That delivery is complete, Trent. Your payment has been credited.',
        'The wagons have been received. Payment for the run has been transferred.',
        'Dispatch confirms receipt of the shipment. Your account has been credited.',
        'The delivery is recorded, Mr. Trent. Your payment is through.',
        'Shipment accepted and payment transferred. Thank you, Trent.',
        'The receiving depot has the cargo. You have been paid.',
        'This order is complete. Payment has been sent to your account.',
    ]),
    'tc_continue': ('-', [
        'Ready for another delivery, Mr. Trent?',
        'Would you like to take another order?',
        'Shall I assign you another run, Trent?',
        'Do you want to continue your shift?',
        'Are you available for another shipment?',
        'Mr. Trent, would you like another delivery assignment?',
        'Shall we keep you on freight duty for another run?',
        'Would you like to stay on for another order, Trent?',
        'Are you ready to take on another delivery?',
        'Let me know, Mr. Trent. Shall we continue?',
    ]),
    'tc_recover': ('-', [
        'Trent, your cargo has detached. Return to the marked wagons and couple to them again.',
        'The train is no longer connected, Mr. Trent. Your wagons are marked. Go back and recover them.',
        'Dispatch to Trent. You have lost the coupling. Return to the cargo marker and reconnect the train.',
        'Your wagons have come loose. Follow the marker back to them and use the coupling manoeuvre again.',
        'Cargo connection lost. Bring the rear of your locomotive back to the marked wagons and recouple.',
        'Mr. Trent, the shipment is still behind you. Return to the marked wagons and restore the coupling.',
        'The cargo is detached, Trent. I have marked its position. Go back and couple to the wagons.',
        'You are travelling without the shipment. Return to the cargo waypoint and reconnect your train.',
        'The coupling has been released away from the delivery point. Recover the marked wagons before continuing.',
        'Dispatch confirms a detached load. Find your wagons at the marker, approach their coupling point stern first, and recouple.',
    ]),
    'tc_park': ('+', [
        'Understood. To finish your shift, park the locomotive at the marked docking fixture serving',
        'We will close your shift, Trent. Return the locomotive to the marked parking position at',
        'No further orders. Park the locomotive beside the marked docking fixture at',
        'All right, Mr. Trent. Bring the locomotive to the marked parking berth at',
        'Your shift is ending. Follow the route and park the locomotive at the docking fixture serving',
        'Dispatch confirms the end of your shift. Return the locomotive to the marked berth at',
        'Time to return the locomotive, Trent. The parking position is by the docking fixture at',
        'We are ready for the handover. Park your locomotive at the marked fixture serving',
        'Mr. Trent, your return route is set. Park the locomotive in the marked position at',
        'That will be all for this shift. Bring the locomotive to the marked docking fixture at',
    ]),
    'tc_done': ('-', [
        'The locomotive is parked, and you are back aboard your own ship. Thank you for your work, Mr. Trent.',
        'Handover complete, Trent. Your shift is finished. Safe flying.',
        'Your own ship is clear of the locomotive. The shift is closed. Thank you, Mr. Trent.',
        'The locomotive has been returned. You are free to go, Trent. Dispatch out.',
        'Your shift is complete, Mr. Trent. Thank you for the deliveries. Safe travels.',
        'We have the locomotive, and you have your ship back. Thank you for your work.',
        'Handover confirmed. Your freight duty is complete, Trent. Until next time.',
        'You are back on your own ship, Mr. Trent. The shift is closed. Have a good flight.',
        'The locomotive is secured. Thank you for your service today, Trent. Dispatch out.',
        'That completes the handover. You are free to depart in your own ship. Until the next run, Mr. Trent.',
    ]),
}


REPOSITION_FAMILIES = {
    'tc_reposition': ('+', [
        'There is no suitable outbound load here, Mr. Trent. Your next train is waiting at',
        'Nothing here matches the next delivery. Take the locomotive to collect a new train at',
        'Dispatch has found your next load at another depot. Head for',
        'This depot has no suitable shipment for your next run. The pickup point is at',
        'Your next assignment starts elsewhere, Trent. Go to the loading point at',
        'We need to move the locomotive before loading again. Your next train is at',
        'There is no matching freight order at this depot. I have arranged a pickup at',
        'The next loaded train is at a different base. Proceed to',
        'You will need to travel empty for the next pickup, Mr. Trent. Head to',
        'This delivery is complete, but the next cargo is waiting elsewhere. Your pickup base is',
    ]),
    'tc_reposition_empty': ('-', [
        'Leave the delivered wagons here and take only the locomotive. The marker leads to your next pickup. Here are the new delivery details.',
        'Travel there without the old train. Your next loaded wagons are marked at the pickup base. I will give you the shipment details now.',
        'Keep the delivered train parked here. Follow the route with the locomotive alone to collect the next load. These are your new instructions.',
        'The old wagons stay with their receiver. Proceed empty to the marked pickup point for your next train. Here is the new order.',
        'Take just the locomotive to that base. A different train is waiting at the marker. Listen carefully to the next shipment details.',
        'Do not collect the delivered wagons again. Travel empty to the new pickup marker. Dispatch will now confirm the cargo and its destination.',
        'Leave this train behind and move the locomotive to the new pickup point. The next load is already assigned. Here are its delivery instructions.',
        'Follow the marked route without any wagons attached. You will collect a new train there. I will now confirm what it carries and where it is going.',
        'This is a move to the next loading point. Take the locomotive alone and leave the completed delivery here. The next order is as follows.',
        'The receiving crew will handle the train you delivered. Head to the new marker with the locomotive only. Here are the details of the next load.',
    ]),
}


def clips(families=None):
    for family, (suffix, variants) in (FAMILIES if families is None else families).items():
        for index, text in enumerate(variants, 1):
            yield f'{family}_{index:02}{suffix}', text


def voice_properties():
    return '[mVoiceProp]\nvoice = '+VOICE+'\n'+''.join(
        f'permutation_count = {family}, {len(variants)}\n'
        for family, (_, variants) in FAMILIES.items())
