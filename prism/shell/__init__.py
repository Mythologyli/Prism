import asyncio

from loguru import logger
import aioconsole


class Shell:

    def __init__(self, config: dict) -> None:
        logger.level('MINECRAFT', no=20, color='<white>')

        self.shell_start_cmd: str = config['shell']['start_cmd']
        self.shell_stop_cmd: str = config['shell']['stop_cmd']
        self.shell_read_encoding: str = config['shell']['read_encoding']
        self.shell_write_encoding: str = config['shell']['write_encoding']

        self.proc = None
        self.run_flag: asyncio.Event = asyncio.Event()
        self.run_flag.clear()

        self.line_queue = asyncio.Queue()
        self.line_queue_get_lock = asyncio.Lock()

        self.line_handler: list = []

        self.add_line_handler(self._game_stop_handler)

    def get_tasks(self):
        return asyncio.gather(
            self.start_game(),
            self._receiver(),
            self._console_input(),
            self._call_line_handler()
        )

    def add_line_handler(self, func) -> None:
        self.line_handler.append(func)

    async def start_game(self) -> None:
        self.proc = await asyncio.create_subprocess_shell(
            self.shell_start_cmd + " && echo PRISM CLOSE SINGAL",
            stdout=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        self.run_flag.set()

        logger.info('Game Start..')

    def stop_game(self) -> None:
        self.send_game_cmd('stop')

    def kill_game(self) -> None:
        try:
            self.proc.kill()
        except ProcessLookupError:
            pass

    async def _receiver(self) -> None:
        while True:
            await self.run_flag.wait()

            data = await self.proc.stdout.readline()
            line = data.decode(self.shell_read_encoding).rstrip()

            # Display the line.
            if line.strip() != '':
                logger.log('MINECRAFT', line)

            # Put the line into queue.
            await self.line_queue.put(line)

    def send_game_cmd(self, cmd: str) -> None:
        if self.run_flag.is_set():
            self.proc.stdin.write(
                (cmd + '\n').encode(self.shell_write_encoding))

    async def _console_input(self) -> None:
        while True:
            cmd = await aioconsole.ainput()

            if self.run_flag.is_set():
                self.send_game_cmd(cmd)
            else:
                await self.issue_prism_cmd(cmd)

    async def _call_line_handler(self) -> None:
        while True:
            await self.run_flag.wait()
            await asyncio.sleep(0)

            line = await self.line_queue.get()
            self.line_queue.put_nowait(line)

            async with self.line_queue_get_lock:
                try:
                    line = self.line_queue.get_nowait()
                except asyncio.QueueEmpty:
                    await asyncio.sleep(0)
                    continue

            for func in self.line_handler:
                func(line)

    async def temp_get_lines(self, num: int = 1) -> list:
        '''
        Get and put back lines to the line_queue.
        Before call this method, make sure the line_queue's get method is locked.

        Example:

        async with handler.queue_get_lock:
            ret_list = await handler.temp_get_lines()

        '''

        line_list = []

        for i in range(num):
            try:
                line_list.append(self.line_queue.get_nowait())
            except asyncio.QueueEmpty:
                pass

        # Put back to queue.
        for line in line_list:
            await self.line_queue.put(line)

        return line_list

    def _game_stop_handler(self, line: str):
        if line.find('PRISM CLOSE SINGAL') != -1:
            self.kill_game()
            self.run_flag.clear()

            logger.info('Server closed. Type start to start the server.')
