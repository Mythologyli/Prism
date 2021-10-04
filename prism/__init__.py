import sys
import asyncio

from loguru import logger

from .shell import Shell
from .api import API
from .event import Event
from .webhook import Webhook


class Prism:

    def __init__(self, config: dict) -> None:
        logger.remove()

        if config['level'] == 'DEBUG':
            logger.add(
                sys.stdout,
                level="DEBUG",
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <9}</level> | <level>{message}</level>"
            )
            logger.add(
                "prism.log",
                level="DEBUG",
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <9}</level> | <level>{message}</level>",
                rotation="10 MB"
            )
        else:
            logger.add(
                sys.stdout,
                level="INFO",
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <9}</level> | <level>{message}</level>"
            )
            logger.add(
                "prism.log",
                level="INFO",
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <9}</level> | <level>{message}</level>",
                rotation="10 MB"
            )

        logger.level('DEBUG', color='<yellow>')
        logger.level('INFO', color='<magenta>')

        logger.debug('Log level set to DEBUG.')
        logger.debug('Config:')
        logger.debug(config)

        self.shell = Shell(config)
        self.api = API(config)
        self.event = Event(config)
        self.webhook = Webhook(config)

        self.shell.add_line_handler(self.event.line_to_event)
        self.api.bind_shell(self.shell)
        self.webhook.bind_event(self.event)

    def run(self) -> None:
        '''
        Run Prism console.
        '''

        logger.info('Welcome to Prism console.\n')

        loop = asyncio.get_event_loop()

        tasks = asyncio.gather(
            self.shell.get_tasks(),
            self.api.get_tasks(),
            self.webhook.get_tasks()
        )

        try:
            loop.run_until_complete(tasks)
        except KeyboardInterrupt:
            self.shell.kill_game()
            logger.info('Keyboard interrupt. Goodbye.')
