"""
MIT License

Copyright (c) 2017 verixx / king1600

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import inspect
import time
import traceback

import asks
import multio
import trio

from .api import HttpClient, ShardConnection
from .models import Channel, Guild, Message, User
from .utils import Collection
from .utils import Emitter
from .utils.commands import Command, CommandCollection, Context

multio.init("trio")
asks.init("trio")


class Client(Emitter):
    def __init__(self, shard_count=-1, prefixes='py.'):
        super().__init__()
        self.token = ''
        self.is_bot = True
        self._boot_up_time = None
        self.running = trio.Event()
        self.api = HttpClient()
        self.shards = [] if shard_count < 1 else list(range(shard_count))
        self.users = Collection(User)
        self.guilds = Collection(Guild)
        self.channels = Collection(Channel)
        self.messages = Collection(Message, maxlen=2500)
        self.commands = CommandCollection(self)
        self.prefixes = prefixes if isinstance(prefixes, list) else [prefixes]
        self.session = asks.Session()  # public session

    def __del__(self):
        if self.is_bot:
            self.close()

    async def _close(self):
        for shard in self.shards:
            await shard.close()
        self.running.set()

    def close(self):
        trio.run(self._close)

    async def start(self, token, bot):
        self.is_bot = bot
        self.token = self.api.token = token

        # get gateway info
        endpoint = '/gateway'
        if self.is_bot:
            endpoint += '/bot'
        info = await self.api.get(endpoint)
        url = info.get('url')

        # get amouont of shards
        shard_count = info.get('shards', 1)
        if len(self.shards) < 1:
            self.shards = list(range(shard_count))
        else:
            shard_count = len(self.shards)

        # spawn shard connections
        async with trio.open_nursery() as nursery:
            for shard_id in range(shard_count):
                shard = ShardConnection(self, shard_id, shard_count)
                self.shards[shard_id] = shard
                nursery.start_soon(shard.start, url)

        # wait for client to stop running
        await self.running.wait()

    def login(self, token, bot=True):
        self._boot_up_time = time.time()
        try:
            trio.run(self.start, token, bot)
        except KeyboardInterrupt:
            pass
        except Exception:
            traceback.print_exc()
        finally:
            self.close()

    async def on_error(self, error):
        """Default error handler for events"""
        traceback.print_exc()  # This actually just prints None...
        # error.__traceback__ can be printed however

    async def on_command_error(self, error):
        traceback.print_exc()

    async def on_message(self, message):
        await self.process_commands(message)

    async def process_commands(self, msg):
        context = Context(self, msg)
        await context.invoke()

    def command(self, callback=None, *, name=None, aliases=None):
        if aliases is None:
            aliases = []
        if inspect.iscoroutinefunction(callback):
            name = name or callback.__name__
            cmd = Command(self, name=name, callback=callback, aliases=aliases)
            self.commands.add(cmd)
        else:
            def wrapper(coro):
                if not inspect.iscoroutinefunction(coro):
                    raise RuntimeWarning(f'Callback is not a coroutine!')
                cmd = Command(self, name=name or coro.__name__, callback=coro, aliases=aliases)
                self.commands.add(cmd)
                return cmd

            return wrapper
