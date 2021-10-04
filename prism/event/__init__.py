import time
import asyncio
import re

from loguru import logger


class BaseEvent:

    def to_dict(self) -> dict:
        return vars(self)


class ServerStartEvent(BaseEvent):

    def __init__(self) -> None:
        self.time = int(time.time())
        self.type: str = 'ServerStart'
        self.start_use_time: float


class ServerStopEvent(BaseEvent):

    def __init__(self) -> None:
        self.time = int(time.time())
        self.type: str = 'ServerStop'


class PlayerJoinEvent(BaseEvent):

    def __init__(self) -> None:
        self.time = int(time.time())
        self.type: str = 'PlayerJoin'
        self.player: str


class PlayerQuitEvent(BaseEvent):

    def __init__(self) -> None:
        self.time = int(time.time())
        self.type: str = 'PlayerQuit'
        self.player: str


class PlayerChatEvent(BaseEvent):

    def __init__(self) -> None:
        self.time = int(time.time())
        self.type: str = 'PlayerChat'
        self.player: str
        self.message: str


class PlayerAdvancementEvent(BaseEvent):

    def __init__(self) -> None:
        self.time = int(time.time())
        self.type: str = 'PlayerAdvancement'
        self.player: str
        self.advancement: str


class Event:

    def __init__(self, config: dict) -> None:
        logger.level('EVENT', no=20, color='<cyan>')

        self.event_queue = asyncio.Queue()

    def line_to_event(self, line: str) -> None:
        res = re.findall(
            "]: Done \((.*?)s\)! For help, type \"help\"", line)
        if res:
            event = ServerStartEvent()
            event.start_use_time = float(res[0])
            self._save_event(event)
            return

        if line.find('PRISM CLOSE SINGAL') != -1:
            event = ServerStopEvent()
            self._save_event(event)
            return

        res = re.findall("]: (.*?) joined the game", line)
        if res:
            event = PlayerJoinEvent()
            event.player = res[0]
            self._save_event(event)
            return

        res = re.findall("]: (.*?) left the game", line)
        if res:
            event = PlayerQuitEvent()
            event.player = res[0]
            self._save_event(event)
            return

        res = re.findall("]: <(.*?)> ", line)
        if res:
            event = PlayerChatEvent()
            event.player = res[0]
            res = re.findall("<[\s\S]*> (.*?)$", line)
            event.message = res[0]
            self._save_event(event)
            return

        res = re.findall("]: (.*?) has[\s\S]*\[[\s\S]*]", line)
        if res:
            event = PlayerAdvancementEvent()
            event.player = res[0]
            res = re.findall("has[\s\S]*\[(.*?)]", line)
            event.advancement = res[0]
            self._save_event(event)
            return

    def _save_event(self, event) -> None:
        logger.log('EVENT', f'Event: {event.to_dict()}')
        self.event_queue.put_nowait(event)

    async def get_event(self):
        res = await self.event_queue.get()
        return res
