"""Сервер Python-MUD."""
from cowsay import cowthink
import shlex
import cmd
import asyncio
from ..common import HOST, PORT, FIELD_SIZE, CUSTOM_MONSTERS

monsters = {}
users = dict()


class Game(cmd.Cmd):
    """
    Основной класс для выполнения команд игры.

    Этот класс отвечает за обработку команд пользователя
    и управление логикой игры.
    """

    def __init__(self, writer, nickname):
        """Инициализация игры."""
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
        """
        Отобразить сообщение абсолютно всем.

        Нужно для сообщений об убийстве моба и его создании.
        """
        for client in users.values():
            client.write(msg)

    def do_sayall(self, message):
        """
        Отобразить сообщение всем, кроме пишущего.

        Нужно для чатика.
        """
        for client in users.values():
            if client != self.writer:
                client.write(f"{self.nickname}: {shlex.split(message)[0]}\n".encode())

    def do_exit(self, arg):
        """Выход из игры."""
        self.writer.write(b"exit...\n")
        return b"exit\n"

    def do_status(self, arg):
        """Отобразить статус сервера для отладки."""
        self.writer.write(b"Server work.\n")

    def encounter(self, x, y):
        """Энкаунтер при встрече с монстром."""
        if (x, y) in monsters:
            name, hello, hp = monsters[(x, y)]
            if name in CUSTOM_MONSTERS:
                self.writer.write((cowthink(hello, cowfile=CUSTOM_MONSTERS[name]) + "\n").encode())
            else:
                self.writer.write((cowthink(hello, cow=name) + "\n").encode())

    def move_player(self, dx, dy, arg):
        """
        Общая функция передвижения игрока по полю.

        Она получает только изменения координат dx, dy от команд
        up, down, left, right.
        """
        self.player_x = (self.player_x + dx) % FIELD_SIZE
        self.player_y = (self.player_y + dy) % FIELD_SIZE
        self.writer.write(f"Moved to ({self.player_x}, {self.player_y})\n".encode())
        self.encounter(self.player_x, self.player_y)

    def do_up(self, arg):
        """Движение вверх."""
        self.move_player(0, -1, arg)

    def do_down(self, arg):
        """Движение вниз."""
        self.move_player(0, 1, arg)

    def do_left(self, arg):
        """Движение влево."""
        self.move_player(-1, 0, arg)

    def do_right(self, arg):
        """Движение вправо."""
        self.move_player(1, 0, arg)

    def do_addmon(self, arg):
        """Добавить монстра на поле."""
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
            self.say_all(f"{self.nickname} replaced the old monster in ({x} {y}) to a monster {name}"
                         f" at ({x}, {y}) saying '{hello}' with {hp} HP \n".encode())

    def do_attack(self, arg):
        """Атаковать монстра с выбором оружия."""
        args = shlex.split(arg)
        name_monster = args[0]
        self.player_weapon = args[2]
        damage = self.weapons[self.player_weapon]

        x, y = self.player_x, self.player_y
        if (x, y) not in monsters:
            self.writer.write(b"No monster here\n")
            return

        if name_monster not in monsters[(x, y)]:
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
    """Сервер."""

    def __init__(self, host=HOST, port=PORT):
        """Инициализация сервера на заданном порте и хосте."""
        self.host = host
        self.port = port
        self.clients = dict()

    async def handle_client(self, reader, writer):
        """При подключении клиента, проверяем ник в системе и запускаем играть."""
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
        """Запуск сервера."""
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
