from io import StringIO
from cowsay import read_dot_cow, list_cows
import shlex
import sys
import cmd
import readline
import asyncio
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit import PromptSession


class Game(cmd.Cmd):
    prompt = ">> "
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    field_size = 10
    custom_monsters = {
        "jgsbat": read_dot_cow(StringIO(r"""
        $the_cow = <<EOC;
            ,_                    _,
            ) '-._  ,_    _,  _.-' (
            )  _.-'.|\\\\--//|.'-._  (
             )'   .'\/o\/o\/'.   `(
              ) .' . \====/ . '. (
               )  / <<    >> \  (
                '-._/``  ``\_.-'
          jgs     __\\\\'--'//__
                 (((""`  `"")))
        EOC
        """))
    }


history = InMemoryHistory()
commands = ["addmon", "attack", "up", "down", "left", "right",
            "exit", "status"]


class DynamicCompleter(Completer):
    def __init__(self):
        self.commands_args = {
            "addmon": ["hello", "hp", "coords"]
        }

    def get_completions(self, document, complete_event):
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
                for monster in list_cows() | Game.custom_monsters.keys():
                        yield Completion(monster, start_position=0)

            case ["attack"]:
                for monster in list_cows() | Game.custom_monsters.keys():
                    yield Completion(monster, start_position=0)

            case[first]:
                for cmd in commands:
                    if cmd.startswith(first) and first != cmd:
                        yield Completion(cmd, start_position=-len(first))

            case ["attack", name_monster]:
                for monster in list_cows() | Game.custom_monsters.keys():
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
                for monster in list_cows() | Game.custom_monsters.keys():
                    if monster.startswith(name):
                        if name != monster:
                            yield Completion(monster, start_position=-len(name))
                        else:
                            yield from self.complete_addmon_arguments(text)

            case ["addmon", name, *_]:
                yield from self.complete_addmon_arguments(text)

    def complete_addmon_arguments(self, text):
        words = shlex.split(text)
        provided_args = set(words[1:])
        last_word = words[-1] if words else ""
        for arg in self.commands_args["addmon"]:
            if arg not in provided_args:
                if text.endswith((" ", "\t")) and last_word not in self.commands_args["addmon"]:
                    yield Completion(arg, start_position=0)
                if arg.startswith(last_word):
                    yield Completion(arg, start_position=-len(last_word))


completer = DynamicCompleter()


class Client:
    def __init__(self, username, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.username = username
        self.history = InMemoryHistory()
        self.completer = DynamicCompleter()
        self.session = PromptSession(history=self.history, completer=self.completer)

    async def run(self):
        await self.connect()
        await asyncio.gather(self.receive_messages(), self.send_messages())

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)
        self.writer.write(self.username.encode() + b"\n")
        await self.writer.drain()
        response = (await self.reader.readline()).decode().strip()
        if response != "SUCCESS":
            self.writer.close()
            await self.writer.wait_closed()
            print("Player with this nickname already exists")
            sys.exit(1)

    async def send_messages(self):
        loop = asyncio.get_running_loop()
        try:
            with patch_stdout():
                while True:
                    command = await loop.run_in_executor(None,
                                lambda: self.session.prompt(">> "))
                    if not command:
                        continue

                    test_command = shlex.split(command)
                    namecommand = test_command[0]
                    field_size = 10

                    if namecommand not in commands:
                        print("Unknown command")
                        continue

                    if command == 'exit':
                        break

                    if namecommand in ["up", "down", "left", "right"] and len(test_command) != 1:
                        print("Invalid arguments")
                        continue

                    if namecommand == "addmon":
                        usage = "Usage: addmon <NAME> hello <MESSAGE> hp <HP> coords <X> <Y>"
                        args = test_command[1:]
                        if not args:
                            print(f"Invalid arguments\n{usage}")
                            continue

                        name = args[0]
                        if name not in list_cows() | Game.custom_monsters.keys():
                            print(f"Unknown monster {name}")
                            continue

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
                                    continue

                            if len(params) != expected_params:
                                print(f"Invalid number of arguments\n{usage}")
                                continue

                            x, y = params['coords']
                            if not (0 <= x < field_size and 0 <= y < field_size):
                                print(f"Invalid coordinates\nField size is {field_size}x{field_size}")
                                continue
                        except (ValueError, IndexError):
                            print(f"Invalid arguments\n{usage}")
                            continue

                    if test_command[0] == "attack":
                        args = test_command[1:]
                        weapons = {"sword", "spear", "axe"}
                        try:
                            if "with" == args[2] and args[3] not in weapons:
                                print("Unknown weapon")
                                continue
                        except IndexError:
                            print("Invalid argument")
                            continue

                    self.writer.write(f"{command}\n".encode())
                    await self.writer.drain()
        except (KeyboardInterrupt, EOFError):
            print("\nClient is shutting down...")
        finally:
            self.writer.close()
            await self.writer.wait_closed()
            print("Disconnected.")

    async def receive_messages(self):
        while True:
            try:
                msg = await self.reader.readline()
                if not msg:
                    break
                print(msg.decode().rstrip('\n'))
            except (KeyboardInterrupt, EOFError):
                print("\nClient is shutting down...")


if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("Usage: python client.py <username>")
        sys.exit(1)

    username = sys.argv[1]

    try:
        asyncio.run(Client(username).run())
    except KeyboardInterrupt:
        print('Client stopped manually.')
