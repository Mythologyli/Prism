import asyncio

from loguru import logger
import aiohttp

from prism.event import Event


class Webhook:

    def __init__(self, config: dict) -> None:
        logger.level('WEBHOOK', no=20, color='<cyan>')

        self.webhook_url: str = config['webhook']['url']
        self.webhook_tag: str = config['webhook']['tag']
        self.webhook_event: dict = config['webhook']['event']
        self.allow_event_list = []

        for key in self.webhook_event:
            if self.webhook_event[key] == True:
                self.allow_event_list.append(key)

        self.event = None

    def bind_event(self, event: Event) -> None:
        self.event = event

    def get_tasks(self):
        return asyncio.gather(
            self._handle_event()
        )

    async def _handle_event(self) -> None:
        while True:
            event_obj = await self.event.get_event()

            data = {
                "status": 200,
                "msg": "event",
                "data": {
                    "tag": self.webhook_tag
                }
            }

            data['data'].update(event_obj.to_dict())

            if data['data']['type'] not in self.allow_event_list:
                logger.log('WEBHOOK', f'Webhook for this event is disabled.')
                return

            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(url=self.webhook_url, json=data) as resp:
                        logger.log('WEBHOOK', f'Send: {data}')
            except (ConnectionRefusedError, aiohttp.ClientConnectionError) as e:
                logger.log('WEBHOOK', f'Error: {type(e)}')
