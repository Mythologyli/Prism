import asyncio
import re
import json

from loguru import logger
from aiohttp import web

from prism.shell import Shell


class API:

    def __init__(self, config: dict) -> None:
        logger.level('API', no=20, color='<blue>')

        self.api_address: str = config['api']['address']
        self.api_port: int = config['api']['port']
        self.api_tag: str = config['api']['tag']

        self.shell = None

    def bind_shell(self, shell: Shell) -> None:
        self.shell = shell

    def get_tasks(self):
        return asyncio.gather(
            self._start_api()
        )

    async def _start_api(self) -> None:
        app = web.Application()
        app.add_routes(
            [
                web.get('/', self._api_get_root_handler),
                web.post('/cmd', self._api_post_cmd_handler),
                web.get('/list', self._api_get_list_handler),
                web.post('/tellraw', self._api_post_tellraw_handler),
                web.get('/usercache', self._api_get_usercache_handler)
            ]
        )

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self.api_address, self.api_port)
        await site.start()

        logger.log(
            'API',
            f'Start API Server on http://{self.api_address}:{self.api_port}'
        )

    async def _api_get_root_handler(self, request: web.Request) -> web.Response:
        logger.log('API', 'GET: /')

        data = {
            "status": 200,
            "msg": "success",
            "data": {
                "tag": self.api_tag
            }
        }

        logger.log('API', f'RETURN: {data}')
        return web.json_response(data)

    async def _api_post_cmd_handler(self, request: web.Request) -> web.Response:
        req = await request.json()

        logger.log('API', 'POST: /cmd    ' + str(dict(req)))

        if 'cmd' in req.keys():
            cmd = str(req['cmd'])
        else:
            data = {
                "status": 400,
                "msg": "no cmd",
                "data": {
                    "tag": self.api_tag
                }
            }

            logger.log('API', f'RETURN: {data}')
            return web.json_response(data)

        if 'num' in req.keys():
            num = int(req['num'])

            if num < 1:
                num = 1
        else:
            num = 1

        if 'wait_time' in req.keys():
            wait_time = int(req['wait_time'])

            if wait_time < 1:
                wait_time = 0
        else:
            wait_time = 1

        if self.shell.run_flag.is_set():
            async with self.shell.line_queue_get_lock:
                self.shell.send_game_cmd(cmd)
                await asyncio.sleep(wait_time)
                ret_list = await self.shell.temp_get_lines(num)

            data = {
                "status": 200,
                "msg": "success",
                "data": {
                    "tag": self.api_tag,
                    "list": ret_list
                }
            }
        else:
            data = {
                "status": 406,
                "msg": "game stop",
                "data": {
                    "tag": self.api_tag,
                }
            }

        logger.log('API', f'RETURN: {data}')
        return web.json_response(data)

    async def _api_get_list_handler(self, request: web.Request) -> web.Response:
        logger.log('API', 'GET: /list')

        if self.shell.run_flag.is_set():
            async with self.shell.line_queue_get_lock:
                self.shell.send_game_cmd('list')
                await asyncio.sleep(1)
                ret_list = await self.shell.temp_get_lines(1)

                player_str: str = re.findall("online:(.*?)$", ret_list[0])[0]
                player_str = player_str.strip()

                if player_str == '':
                    player_list = []
                else:
                    player_list = player_str.split(', ')

            data = {
                "status": 200,
                "msg": "success",
                "data": {
                    "tag": self.api_tag,
                    "num": len(player_list),
                    "player_list": player_list
                }
            }
        else:
            data = {
                "status": 406,
                "msg": "game stop",
                "data": {
                    "tag": self.api_tag,
                }
            }

        logger.log('API', f'RETURN: {data}')
        return web.json_response(data)

    async def _api_post_tellraw_handler(self, request: web.Request) -> web.Response:
        req = await request.json()

        logger.log('API', 'POST: /tellraw    ' + str(dict(req)))

        if 'message' in req.keys():
            message = str(req['message'])
        else:
            data = {
                "status": 400,
                "msg": "no message",
                "data": {
                    "tag": self.api_tag
                }
            }

            logger.log('API', f'RETURN: {data}')
            return web.json_response(data)

        if 'selector' in req.keys():
            selector = str(req['selector'])
        else:
            selector = '@a'

        if self.shell.run_flag.is_set():
            cmd = 'tellraw ' + selector + ' {"text": "' + message + '\"}'
            cmd = cmd.replace('\n', '\\n')
            logger.debug(cmd)
            self.shell.send_game_cmd(
                cmd
            )

            data = {
                "status": 200,
                "msg": "success",
                "data": {
                    "tag": self.api_tag
                }
            }
        else:
            data = {
                "status": 406,
                "msg": "game stop",
                "data": {
                    "tag": self.api_tag,
                }
            }

        logger.log('API', f'RETURN: {data}')
        return web.json_response(data)

    async def _api_get_usercache_handler(self, request: web.Request) -> web.Response:
        logger.log('API', 'GET: /usercache')
        user_cache_list = json.load(open('./usercache.json', 'r'))

        data = {
            "status": 200,
            "msg": "success",
            "data": {
                "tag": self.api_tag,
                "usercache": user_cache_list
            }
        }

        logger.log('API', f'RETURN: {data}')
        return web.json_response(data)
