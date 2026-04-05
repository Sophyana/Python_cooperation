import sys
from io import StringIO
from cowsay import read_dot_cow, cowthink
import shlex
import cmd
import readline
import asyncio


monsters = {}
users = dict()

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

    def __init__(self, writer, nickname):
        super().__init__()
        self.player_x = 0
        self.player_y = 0
        self.weapons = {
            "sword": 10,
            "spear": 15,
            "axe": 20,
        }
        self.player_weapon = "sword"
        self.writer = writer
        self.nickname = nickname

    def say_all(self, msg):
        for client in users.values():
            client.write(msg)

    def do_sayall(self, message):
        for client in users.values():
            if client != self.writer:
                client.write(f"{self.nickname}: {shlex.split(message)[0]}\n".encode())

    def do_exit(self, arg):
        self.writer.write(b"exit...\n")
        return b"exit\n"

    def do_status(self, arg):
        self.writer.write(b"Server work.\n")

    def encounter(self, x, y):
        if (x, y) in monsters:
            name, hello, hp = monsters[(x, y)]
            if name in self.custom_monsters:
                self.writer.write((cowthink(hello, cowfile=self.custom_monsters[name])+"\n").encode())
            else:
                self.writer.write((cowthink(hello, cow=name)+"\n").encode())

    def move_player(self, dx, dy, arg):
        """Generalized player movement function"""
        self.player_x = (self.player_x + dx) % self.field_size
        self.player_y = (self.player_y + dy) % self.field_size
        self.writer.write(f"Moved to ({self.player_x}, {self.player_y})\n".encode())
        self.encounter(self.player_x, self.player_y)

    def do_up(self, arg):
        """Move the player up."""
        self.move_player(0, -1, arg)

    def do_down(self, arg):
        """Move the player down."""
        self.move_player(0, 1, arg)

    def do_left(self, arg):
        """Move the player left."""
        self.move_player(-1, 0, arg)

    def do_right(self, arg):
        """Move the player right."""
        self.move_player(1, 0, arg)

    def do_addmon(self, arg):
        "Add a monster to the game."
        args = shlex.split(arg)
        name = args[0]
        params = {}
        param_names = ["hello", "hp", "coords"]
        i = 1

        while i < len(args):
            if args[i] in param_names:
                param = args[i]
                if param == "coords":
                    params[param] = (int(args[i + 1]), int(args[i + 2]))
                    i += 3
                else:
                    params[param] = args[i + 1]
                    i += 2

        hello = params['hello']
        hp = int(params['hp'])
        x, y = params['coords']

        replaced = (x, y) in monsters
        monsters[(x, y)] = (name, hello, hp)
        self.say_all(f"{self.nickname} add a monster {name} at ({x}, {y}) saying '{hello}' with {hp} HP\n".encode())
        if replaced:
            self.say_all(f"{self.nickname} replaced the old monster in ({x} {y}) to a monster {name} at ({x}, {y}) saying '{hello}' with {hp} HP \n".encode())


    def do_attack(self, arg):
        """Attack the monster in the current cell."""

        args = shlex.split(arg)
        name_monster = args[0]
        self.player_weapon = args[2]
        damage = self.weapons[self.player_weapon]

        x, y = self.player_x, self.player_y
        if (x, y) not in monsters:
            self.writer.write(b"No monster here\n")
            return

        if name_monster not in monsters[(x,y)]:
            self.writer.write(f"No {name_monster} here\n".encode())
            return

        name, hello, hp = monsters[(x, y)]
        new_hp = hp - damage

        if new_hp <= 0:
            del monsters[(x, y)]
            self.say_all(f"{self.nickname} attacked {name_monster} in ({x}, {y}), damage {damage} hp\n"
                         f"{name_monster} died\n".encode())
        else:
            monsters[(x, y)] = (name_monster, hello, new_hp)
            self.say_all(f"{self.nickname} attacked {name_monster} in ({x}, {y}), damage {damage} hp\n"
                         f"{name_monster} now has {new_hp}\n".encode())


class Server:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.clients = dict()

    async def handle_client(self, reader, writer):
        addr = writer.get_extra_info('peername')
        username = (await reader.readline()).decode().strip()

        if username in users:
            writer.write(b"ERROR\n")
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            print(f"User {username} try to connected from {addr} but can't")
            return
        else:
            users[username] = writer
            print(f"User {username} connected from {addr}")
            writer.write(b"SUCCESS\n")
            await writer.drain()

        game = Game(writer, username)
        try:
            while True:
                msg = await reader.readline()
                if not msg:
                    break

                command = msg.decode().strip()
                print(f'{addr} says: {command}')
                game.onecmd(command)

        except Exception as e:
            print(f'Connection error with {addr}: {e}')
        finally:
            print(f'Closing connection from {addr}')
            users.pop(username)
            writer.close()
            await writer.wait_closed()

    async def run(self):
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Working on {addr}')

        async with server:
            await server.serve_forever()


if __name__ == '__main__':

    try:
        asyncio.run(Server().run())
    except KeyboardInterrupt:
        print('Server stopped successfully.')
