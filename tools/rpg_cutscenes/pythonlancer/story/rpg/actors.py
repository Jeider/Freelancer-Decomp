"""Voice actors belonging to RPG base dialogue, separate from campaign characters."""
from audio.delivery import NEUTRAL
from story.actors import Actor, ACTOR_MALE
from text.strings import MultiString as MS


class RpgTradeDirector(Actor):
    NAME = 'rpg_trade_director'
    TYPE = ACTOR_MALE
    RU_NAME = MS('Глава торгового управления', 'Trade Authority Director')
    VOICE_DELIVERY = NEUTRAL
    STEOS_SPEED = 1
    # VoiceStudio uses this class name for its own RU/EN reference recordings.
    # No fallback to Hassler or another campaign actor.
