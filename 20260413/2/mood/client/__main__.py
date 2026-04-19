"""Модуль клиента с проверкой аргументов команд и их дополнением."""
from cowsay import list_cows
import shlex
import sys
import asyncio
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit import PromptSession
from ..common import HOST, PORT, FIELD_SIZE, INTRO, CUSTOM_MONSTERS


history = InMemoryHistory()
commands = ["addmon", "attack", "up", "down", "left", "right",
            "exit", "status", "sayall", "movemonsters", "locale"]


class DynamicCompleter(Completer):
    """Класс дополнения команд."""

    def get_completions(self, document, complete_event):
        """Дополнение аргументов команд."""
        text = document.text_before_cursor

        if not text:
            for cmd in commands:
                yield Completion(cmd, start_position=0)
            return

        try:
            words = shlex.split(text)
        except ValueError:
            return

        match words:

            case["addmon"]:
                for monster in list_cows() | CUSTOM_MONSTERS.keys():
                    yield Completion(monster, start_position=0)

            case ["attack"]:
                for monster in list_cows() | CUSTOM_MONSTERS.keys():
                    yield Completion(monster, start_position=0)

            case ["movemonsters"]:
                for move_mon_arg in ["on", "off"]:
                    yield Completion(move_mon_arg, start_position=0)

            case ["locale"]:
                for loc in ["ru_RU.UTF8", "en_US.UTF8"]:
                    yield Completion(loc, start_position=0)

            case[first]:
                for cmd in commands:
                    if cmd.startswith(first) and first != cmd:
                        yield Completion(cmd, start_position=-len(first))

            case ["attack", name_monster]:
                for monster in list_cows() | CUSTOM_MONSTERS.keys():
                    if monster.startswith(name_monster):
                        if name_monster == monster:
                            yield Completion("with", start_position=0)
                        else:
                            yield Completion(monster, start_position=-len(name_monster))

            case ["attack", name_monster, with_word]:
                if "with".startswith(with_word):
                    if with_word == "with":
                        for w in ["sword", "axe", "spear"]:
                            yield Completion(w, start_position=0)
                    else:
                        yield Completion("with", start_position=-len(with_word))

            case ["attack", name_monster, "with", weapon]:
                for w in ["sword", "axe", "bow"]:
                    if w.startswith(weapon) and w != weapon:
                        yield Completion(w, start_position=-len(weapon))

            case ["addmon", name]:
                for monster in list_cows() | CUSTOM_MONSTERS.keys():
                    if monster.startswith(name):
                        if name != monster:
                            yield Completion(monster, start_position=-len(name))
                        else:
                            yield from self.complete_addmon_arguments(text)

            case ["addmon", name, *_]:
                yield from self.complete_addmon_arguments(text)

    def complete_addmon_arguments(self, text):
        """
        Дополнение аргументов команды addmon.

        Реализована отдельно, потому что её аргументы могут стоять в разной последовательности.
        """
        addmon_args = ["hello", "hp", "coords"]
        words = shlex.split(text)
        provided_args = set(words[1:])
        last_word = words[-1] if words else ""
        for arg in addmon_args:
            if arg not in provided_args:
                if text.endswith((" ", "\t")) and last_word not in addmon_args:
                    yield Completion(arg, start_position=0)
                if arg.startswith(last_word):
                    yield Completion(arg, start_position=-len(last_word))


completer = DynamicCompleter()


class Client:
    """Класс клиента."""

    def __init__(self, username, file_commands=None, host=HOST, port=PORT):
        """Инициализация клиента."""
        self.host = host
        self.port = port
        self.file_commands = file_commands
        self.username = username
        self.history = InMemoryHistory()
        self.completer = DynamicCompleter()
        self.session = PromptSession(history=self.history, completer=self.completer)

    async def run(self):
        """Запуск клиента."""
        await self.connect()
        await asyncio.gather(self.receive_messages(), self.send_messages())

    async def connect(self):
        """Подключение к серверу."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.writer.write(self.username.encode() + b"\n")
        await self.writer.drain()
        response = (await self.reader.readline()).decode().strip()
        if response != "SUCCESS":
            self.writer.close()
            await self.writer.wait_closed()
            print("Player with this nickname already exists")
            sys.exit(1)
        else:
            print(INTRO)

    async def send_messages(self):
        """Отправка сообщений."""
        loop = asyncio.get_running_loop()
        try:
            with patch_stdout():
                if self.file_commands:
                    with open(self.file_commands, 'r') as file:
                        commands_from_file = [line.rstrip('\n') for line in file.readlines()]
                    for command in commands_from_file:
                        await self.process_command(command)
                        await asyncio.sleep(1)
                else:
                    while True:
                        command = await loop.run_in_executor(None,
                                                             lambda: self.session.prompt(">> "))
                        if not command:
                            continue
                        if command == 'exit':
                            break
                        await self.process_command(command)
        except (KeyboardInterrupt, EOFError):
            print("\nClient is shutting down...")
        finally:
            self.writer.close()
            await self.writer.wait_closed()
            print("Disconnected.")

    async def receive_messages(self):
        """Простое отображение сообщений от сервера."""
        while True:
            try:
                msg = await self.reader.readline()
                if not msg:
                    break
                print(msg.decode().rstrip('\n'))
            except (KeyboardInterrupt, EOFError):
                print("\nClient is shutting down...")

    async def process_command(self, command):
        """Обработка команды."""
        test_command = shlex.split(command)
        namecommand = test_command[0]

        if namecommand not in commands:
            print("Unknown command")
            return

        if command == "sayall":
            if len(test_command) != 2:
                print("Invalid arguments")
                return

        if namecommand == "movemonsters":
            if len(test_command) != 2 or test_command[1] not in ("on", "off"):
                print("Invalid arguments")
                return

        if namecommand == "locale":
            if len(test_command) != 2:
                print("Usage: locale <locale_name>")
                return

        if namecommand in ["up", "down", "left", "right"] and len(test_command) != 1:
            print("Invalid arguments")
            return

        if namecommand == "addmon":
            usage = "Usage: addmon <NAME> hello <MESSAGE> hp <HP> coords <X> <Y>"
            args = test_command[1:]
            if not args:
                print(f"Invalid arguments\n{usage}")
                return

            name = args[0]
            if name not in list_cows() | CUSTOM_MONSTERS.keys():
                print(f"Unknown monster {name}")
                return

            params = {}
            param_names = ["hello", "hp", "coords"]
            expected_params = 3
            i = 1

            try:
                while i < len(args):
                    if args[i] in param_names:
                        param = args[i]
                        if param == "coords":
                            params[param] = (int(args[i + 1]), int(args[i + 2]))
                            i += 3
                        else:
                            params[param] = args[i + 1]
                            i += 2
                    else:
                        print(f"Invalid argument: {args[i]}\n{usage}")
                        return

                if len(params) != expected_params:
                    print(f"Invalid number of arguments\n{usage}")
                    return

                x, y = params['coords']
                if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
                    print(f"Invalid coordinates\nField size is {FIELD_SIZE}x{FIELD_SIZE}")
                    return
            except (ValueError, IndexError):
                print(f"Invalid arguments\n{usage}")
                return

        if test_command[0] == "attack":
            args = test_command[1:]
            weapons = {"sword", "spear", "axe"}
            try:
                if "with" == args[2] and args[3] not in weapons:
                    print("Unknown weapon")
                    return
            except IndexError:
                print("Invalid argument")
                return

        self.writer.write(f"{command}\n".encode())
        await self.writer.drain()


if __name__ == '__main__':
    file_commands = None
    if '--file' in sys.argv:
        file_index = sys.argv.index('--file') + 1
        if file_index < len(sys.argv):
            file_commands = sys.argv[file_index]

    if len(sys.argv) != 2 and file_commands is None:
        print("Usage: python client.py <username>")
        sys.exit(1)
    username = sys.argv[1]

    try:
        asyncio.run(Client(username, file_commands).run())
    except KeyboardInterrupt:
        print('Client stopped manually.')
