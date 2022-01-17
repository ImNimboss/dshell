"""
Copyright (c) 2021 Devon (Gorialis) R

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

NOTE: This whole file is copy pasted code from Jishaku with some alterations.
This file is not for normal use.
This is so that Jishaku itself doesn't need to be a dependency for this package, as only a part of Jishaku is needed.
[Link to Jishaku](https://github.com/Gorialis/jishaku)
"""

import asyncio, discord
from discord.ext import commands
from contextlib import contextmanager
from os import getenv
from sys import platform
from collections import namedtuple, deque
from pathlib import Path
from subprocess import Popen, PIPE, TimeoutExpired
from re import sub
from time import perf_counter
from traceback import format_exception

EmojiSettings = namedtuple('EmojiSettings', 'start back forward end close')

CommandTask = namedtuple('CommandTask', 'index ctx task')
Codeblock = namedtuple('Codeblock', 'language content')
EmojiSettings = namedtuple('EmojiSettings', 'start back forward end close')
EMOJI_DEFAULT = EmojiSettings(
    start = '\N{BLACK LEFT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
    back = '\N{BLACK LEFT-POINTING TRIANGLE}',
    forward = '\N{BLACK RIGHT-POINTING TRIANGLE}',
    end = '\N{BLACK RIGHT-POINTING DOUBLE TRIANGLE WITH VERTICAL BAR}',
    close = '\N{BLACK SQUARE FOR STOP}'
)
SHELL = getenv("SHELL") or "/bin/bash"
WINDOWS = platform == "win32"
tasks = deque()
task_count = 0

def codeblock_converter(argument):
    if not argument.startswith('`'):
        return Codeblock(None, argument)

    # keep a small buffer of the last chars we've seen
    last = deque(maxlen=3)
    backticks = 0
    in_language = False
    in_code = False
    language = []
    code = []

    for char in argument:
        if char == '`' and not in_code and not in_language:
            backticks += 1  # to help keep track of closing backticks
        if last and last[-1] == '`' and char != '`' or in_code and ''.join(last) != '`' * backticks:
            in_code = True
            code.append(char)
        if char == '\n':  # \n delimits language and code
            in_language = False
            in_code = True
        # we're not seeing a newline yet but we also passed the opening ```
        elif ''.join(last) == '`' * 3 and char != '`':
            in_language = True
            language.append(char)
        elif in_language:  # we're in the language after the first non-backtick character
            if char != '\n':
                language.append(char)

        last.append(char)

    if not code and not language:
        code[:] = last

    return Codeblock(''.join(language), ''.join(code[len(language):-backticks]))

@contextmanager
def submit(ctx: commands.Context):
    global task_count
    global tasks
    task_count += 1

    try:
        current_task = asyncio.current_task()  # pylint: disable=no-member
    except RuntimeError:
        # asyncio.current_task doesn't document that it can raise RuntimeError, but it does.
        # It propagates from asyncio.get_running_loop(), so it happens when there is no loop running.
        # It's unclear if this is a regression or an intentional change, since in 3.6,
        #  asyncio.Task.current_task() would have just returned None in this case.
        current_task = None

    cmdtask = CommandTask(task_count, ctx, current_task)

    tasks.append(cmdtask)

    try:
        yield cmdtask
    finally:
        if cmdtask in tasks:
            tasks.remove(cmdtask)

def background_reader(stream, loop: asyncio.AbstractEventLoop, callback):
    for line in iter(stream.readline, b''):
        loop.call_soon_threadsafe(loop.create_task, callback(line))

async def send_traceback(destination, verbosity: int, *exc_info):
    # to make pylint stop moaning
    etype, value, trace = exc_info

    traceback_content = "".join(format_exception(etype, value, trace, verbosity)).replace("``", "`\u200b`")

    paginator = commands.Paginator(prefix='```py')
    for line in traceback_content.split('\n'):
        paginator.add_line(line)

    message = None

    for page in paginator.pages:
        message = await destination.send(page)

    return message

async def attempt_add_reaction(msg, reaction):
    try:
        return await msg.add_reaction(reaction)
    except discord.HTTPException:
        pass

async def do_after_sleep(delay: float, coro, *args, **kwargs):
    await asyncio.sleep(delay)
    return await coro(*args, **kwargs)

class WrappedPaginator(commands.Paginator):
    def __init__(self, *args, wrap_on = ('\n', ' '), include_wrapped=True, force_wrap=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.wrap_on = wrap_on
        self.include_wrapped = include_wrapped
        self.force_wrap = force_wrap

    def add_line(self, line='', *, empty=False):
        true_max_size = self.max_size - self._prefix_len - self._suffix_len - 2
        original_length = len(line)

        while len(line) > true_max_size:
            search_string = line[0:true_max_size - 1]
            wrapped = False

            for delimiter in self.wrap_on:
                position = search_string.rfind(delimiter)

                if position > 0:
                    super().add_line(line[0:position], empty=empty)
                    wrapped = True

                    if self.include_wrapped:
                        line = line[position:]
                    else:
                        line = line[position + len(delimiter):]

                    break

            if not wrapped:
                if self.force_wrap:
                    super().add_line(line[0:true_max_size - 1])
                    line = line[true_max_size - 1:]
                else:
                    raise ValueError(
                        f"Line of length {original_length} had sequence of {len(line)} characters"
                        f" (max is {true_max_size}) that WrappedPaginator could not wrap with"
                        f" delimiters: {self.wrap_on}"
                    )

        super().add_line(line, empty=empty)

class PaginatorInterface:  # pylint: disable=too-many-instance-attributes
    def __init__(self, bot: commands.Bot, paginator: commands.Paginator, **kwargs):
        if not isinstance(paginator, commands.Paginator):
            raise TypeError('paginator must be a commands.Paginator instance')

        self._display_page = 0

        self.bot = bot

        self.message = None
        self.paginator = paginator

        self.owner = kwargs.pop('owner', None)
        self.emojis = kwargs.pop('emoji', EMOJI_DEFAULT)
        self.timeout = kwargs.pop('timeout', 7200)
        self.delete_message = kwargs.pop('delete_message', False)

        self.sent_page_reactions = False

        self.task: asyncio.Task = None
        self.send_lock: asyncio.Event = asyncio.Event()

        self.close_exception: Exception = None

        if self.page_size > self.max_page_size:
            raise ValueError(
                f'Paginator passed has too large of a page size for this interface. '
                f'({self.page_size} > {self.max_page_size})'
            )

    @property
    def pages(self):
        # protected access has to be permitted here to not close the paginator's pages

        # pylint: disable=protected-access
        paginator_pages = list(self.paginator._pages)
        if len(self.paginator._current_page) > 1:
            paginator_pages.append('\n'.join(self.paginator._current_page) + '\n' + (self.paginator.suffix or ''))
        # pylint: enable=protected-access

        return paginator_pages

    @property
    def page_count(self):
        return len(self.pages)

    @property
    def display_page(self):
        self._display_page = max(0, min(self.page_count - 1, self._display_page))
        return self._display_page

    @display_page.setter
    def display_page(self, value):
        self._display_page = max(0, min(self.page_count - 1, value))

    max_page_size = 2000

    @property
    def page_size(self) -> int:
        page_count = self.page_count
        return self.paginator.max_size + len(f'\nPage {page_count}/{page_count}')

    @property
    def send_kwargs(self) -> dict:
        display_page = self.display_page
        page_num = f'\nPage {display_page + 1}/{self.page_count}'
        content = self.pages[display_page] + page_num
        return {'content': content}

    async def add_line(self, *args, **kwargs):
        display_page = self.display_page
        page_count = self.page_count

        self.paginator.add_line(*args, **kwargs)

        new_page_count = self.page_count

        if display_page + 1 == page_count:
            # To keep position fixed on the end, update position to new last page and update message.
            self._display_page = new_page_count

        # Unconditionally set send lock to try and guarantee page updates on unfocused pages
        self.send_lock.set()

    async def send_to(self, destination: discord.abc.Messageable):
        self.message = await destination.send(**self.send_kwargs)

        # add the close reaction
        await self.message.add_reaction(self.emojis.close)

        self.send_lock.set()

        if self.task:
            self.task.cancel()

        self.task = self.bot.loop.create_task(self.wait_loop())

        # if there is more than one page, and the reactions haven't been sent yet, send navigation emotes
        if not self.sent_page_reactions and self.page_count > 1:
            await self.send_all_reactions()

        return self

    async def send_all_reactions(self):
        for emoji in filter(None, self.emojis):
            try:
                await self.message.add_reaction(emoji)
            except discord.NotFound:
                # the paginator has probably already been closed
                break
        self.sent_page_reactions = True

    @property
    def closed(self):
        if not self.task:
            return False
        return self.task.done()

    async def send_lock_delayed(self):
        gathered = await self.send_lock.wait()
        self.send_lock.clear()
        await asyncio.sleep(1)
        return gathered

    async def wait_loop(self):  # pylint: disable=too-many-branches,too-many-statements
        start, back, forward, end, close = self.emojis

        def check(payload: discord.RawReactionActionEvent):
            owner_check = not self.owner or payload.user_id == self.owner.id

            emoji = payload.emoji
            if isinstance(emoji, discord.PartialEmoji) and emoji.is_unicode_emoji():
                emoji = emoji.name

            tests = (
                owner_check,
                payload.message_id == self.message.id,
                emoji,
                emoji in self.emojis,
                payload.user_id != self.bot.user.id
            )

            return all(tests)

        task_list = [
            self.bot.loop.create_task(coro) for coro in {
                self.bot.wait_for('raw_reaction_add', check=check),
                self.bot.wait_for('raw_reaction_remove', check=check),
                self.send_lock_delayed()
            }
        ]

        try:  # pylint: disable=too-many-nested-blocks
            last_kwargs = None

            while not self.bot.is_closed():
                done, _ = await asyncio.wait(task_list, timeout=self.timeout, return_when=asyncio.FIRST_COMPLETED)

                if not done:
                    raise asyncio.TimeoutError

                for task in done:
                    task_list.remove(task)
                    payload = task.result()

                    if isinstance(payload, discord.RawReactionActionEvent):
                        emoji = payload.emoji
                        if isinstance(emoji, discord.PartialEmoji) and emoji.is_unicode_emoji():
                            emoji = emoji.name

                        if emoji == close:
                            await self.message.delete()
                            return

                        if emoji == start:
                            self._display_page = 0
                        elif emoji == end:
                            self._display_page = self.page_count - 1
                        elif emoji == back:
                            self._display_page -= 1
                        elif emoji == forward:
                            self._display_page += 1

                        if payload.event_type == 'REACTION_ADD':
                            task_list.append(self.bot.loop.create_task(
                                self.bot.wait_for('raw_reaction_add', check=check)
                            ))
                        elif payload.event_type == 'REACTION_REMOVE':
                            task_list.append(self.bot.loop.create_task(
                                self.bot.wait_for('raw_reaction_remove', check=check)
                            ))
                    else:
                        # Send lock was released
                        task_list.append(self.bot.loop.create_task(self.send_lock_delayed()))

                if not self.sent_page_reactions and self.page_count > 1:
                    self.bot.loop.create_task(self.send_all_reactions())
                    self.sent_page_reactions = True  # don't spawn any more tasks

                if self.send_kwargs != last_kwargs:
                    try:
                        await self.message.edit(**self.send_kwargs)
                    except discord.NotFound:
                        # something terrible has happened
                        return

                    last_kwargs = self.send_kwargs

        except (asyncio.CancelledError, asyncio.TimeoutError) as exception:
            self.close_exception = exception

            if self.bot.is_closed():
                # Can't do anything about the messages, so just close out to avoid noisy error
                return

            if self.delete_message:
                return await self.message.delete()

            for emoji in filter(None, self.emojis):
                try:
                    await self.message.remove_reaction(emoji, self.bot.user)
                except (discord.Forbidden, discord.NotFound):
                    pass

        finally:
            for task in task_list:
                task.cancel()

async def jsk_shell(ctx, *, argument: codeblock_converter, cwd: str): # ALL the other things in this file are solely for this one function to do its job...
    async with ReplResponseReactor(ctx.message):
        with submit(ctx):
            with ShellReader(argument.content, cwd) as reader:
                prefix = "```" + reader.highlight

                paginator = WrappedPaginator(prefix=prefix, max_size=1975)
                paginator.add_line(f"{reader.ps1} {argument.content}\n")

                interface = PaginatorInterface(ctx.bot, paginator, owner=ctx.author)
                ctx.bot.loop.create_task(interface.send_to(ctx)) # it was originally self.bot.loop.create_task

                async for line in reader:
                    if interface.closed:
                        return
                    await interface.add_line(line)

            await interface.add_line(f"\n[status] Return code {reader.close_code}")

class ShellReader:
    def __init__(self, code: str, cwd: str, timeout: int = 90, loop: asyncio.AbstractEventLoop = None):
        if WINDOWS:
            # Check for powershell
            if Path(r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe").exists():
                sequence = ['powershell', code]
                self.ps1 = "PS >"
                self.highlight = "powershell"
            else:
                sequence = ['cmd', '/c', code]
                self.ps1 = "cmd >"
                self.highlight = "cmd"
        else:
            sequence = [SHELL, '-c', code]
            self.ps1 = "$"
            self.highlight = "sh"

        self.process = Popen(sequence, stdout=PIPE, stderr=PIPE, cwd=cwd)
        self.close_code = None

        self.loop = loop or asyncio.get_event_loop()
        self.timeout = timeout

        self.stdout_task = self.make_reader_task(self.process.stdout, self.stdout_handler)
        self.stderr_task = self.make_reader_task(self.process.stderr, self.stderr_handler)

        self.queue = asyncio.Queue(maxsize = 250)

    @property
    def closed(self):
        return self.stdout_task.done() and self.stderr_task.done()

    async def executor_wrapper(self, *args, **kwargs):
        return await self.loop.run_in_executor(None, *args, **kwargs)

    def make_reader_task(self, stream, callback):
       return self.loop.create_task(self.executor_wrapper(background_reader, stream, self.loop, callback))

    @staticmethod
    def clean_bytes(line):
        text = line.decode('utf-8').replace('\r', '').strip('\n')
        return sub(r'\x1b[^m]*m', '', text).replace("``", "`\u200b`").strip('\n')

    async def stdout_handler(self, line):
        await self.queue.put(self.clean_bytes(line))

    async def stderr_handler(self, line):
        await self.queue.put(self.clean_bytes(b'[stderr] ' + line))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.process.kill()
        self.process.terminate()
        self.close_code = self.process.wait(timeout=0.5)

    def __aiter__(self):
        return self

    async def __anext__(self):
        start_time = perf_counter()

        while not self.closed or not self.queue.empty():
            try:
                return await asyncio.wait_for(self.queue.get(), timeout=1)
            except asyncio.TimeoutError as exception:
                if perf_counter() - start_time >= self.timeout:
                    raise exception

        raise StopAsyncIteration()

class ReactionProcedureTimer:  # pylint: disable=too-few-public-methods
    __slots__ = ('message', 'loop', 'handle', 'raised')

    def __init__(self, message, loop = None):
        self.message = message
        self.loop = loop or asyncio.get_event_loop()
        self.handle = None
        self.raised = False

    async def __aenter__(self):
        self.handle = self.loop.create_task(do_after_sleep(1, attempt_add_reaction, self.message,
                                                           "\N{BLACK RIGHT-POINTING TRIANGLE}"))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.handle:
            self.handle.cancel()

        # no exception, check mark
        if not exc_val:
            await attempt_add_reaction(self.message, "\N{WHITE HEAVY CHECK MARK}")
            return

        self.raised = True

        if isinstance(exc_val, (asyncio.TimeoutError, TimeoutExpired)):
            # timed out, alarm clock
            await attempt_add_reaction(self.message, "\N{ALARM CLOCK}")
        elif isinstance(exc_val, SyntaxError):
            # syntax error, single exclamation mark
            await attempt_add_reaction(self.message, "\N{HEAVY EXCLAMATION MARK SYMBOL}")
        else:
            # other error, double exclamation mark
            await attempt_add_reaction(self.message, "\N{DOUBLE EXCLAMATION MARK}")

class ReplResponseReactor(ReactionProcedureTimer):  # pylint: disable=too-few-public-methods
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await super().__aexit__(exc_type, exc_val, exc_tb)

        # nothing went wrong, who cares lol
        if not exc_val:
            return

        if isinstance(exc_val, (SyntaxError, asyncio.TimeoutError, TimeoutExpired)):
            # short traceback, send to channel
            await send_traceback(self.message.channel, 0, exc_type, exc_val, exc_tb)
        else:
            # this traceback likely needs more info, so increase verbosity, and DM it instead.
            await send_traceback(
                self.message.author, 8, exc_type, exc_val, exc_tb
            )

        return True  # the exception has been handled