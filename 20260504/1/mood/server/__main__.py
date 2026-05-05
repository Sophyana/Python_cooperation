"""Сервер Python-MUD с поддержкой локализации."""
from cowsay import cowthink
import shlex
import cmd
import asyncio
import gettext
import os
from ..common import HOST, PORT, FIELD_SIZE, CUSTOM_MONSTERS
import random

LOCALE_DIR = os.path.join(os.path.dirname(__file__), "locales")
DEFAULT_LOCALE = "en_US.UTF8"

monsters = {}
users = dict()
DIRECTIONS = {
    "right": (1, 0),
    "left": (-1, 0),
    "up": (0, -1),
    "down": (0, 1)
}


def get_translator(locale_str):
    """
    Вернуть пару (gettext, ngettext) для заданной локали.

    При отсутствии каталога — возвращает no-op функции.
    """
    try:
        translator = gettext.translation(
            'messages', LOCALE_DIR, languages=[locale_str])
        return translator.gettext, translator.ngettext
    except FileNotFoundError:
        null = gettext.NullTranslations()
        return null.gettext, null.ngettext


def broadcast(msg, *args):
    """Широковещательное сообщение с локализацией у каждого получателя."""
    for client in users.values():
        game = getattr(client, 'game', None)
        if game is None:
            continue
        gettext_, _ngettext = get_translator(game.locale)
        client.write(gettext_(msg).format(*args).encode())


def broadcast_plural(singular, plural, n, *args):
    """Широковещательное сообщение с учётом множественного числа."""
    for client in users.values():
        game = getattr(client, 'game', None)
        if game is None:
            continue
        _gettext, ngettext_ = get_translator(game.locale)
        client.write(ngettext_(singular, plural, n).format(*args).encode())


class Game(cmd.Cmd):
    """
    Основной класс для выполнения команд игры.

    Этот класс отвечает за обработку команд пользователя
    и управление логикой игры.
    """

    def __init__(self, server, writer, nickname):
        """Инициализация игры."""
        super().__init__()
        self.server = server
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
        self.locale = DEFAULT_LOCALE
        self._, self.ngettext = get_translator(self.locale)

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
        self.writer.write(self._("exit...\n").encode())
        return b"exit\n"

    def do_status(self, arg):
        """Отобразить статус сервера для отладки."""
        self.writer.write(self._("Server work.\n").encode())

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
        self.writer.write(self._("Moved to ({}, {})\n").format(
            self.player_x, self.player_y).encode())
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
        if replaced:
            broadcast_plural(
                "{} replaced the old monster at ({}, {}) with a monster {} saying '{}' with {} health point\n",
                "{} replaced the old monster at ({}, {}) with a monster {} saying '{}' with {} health points\n",
                hp,
                self.nickname, x, y, name, hello, hp,
            )
        else:
            broadcast_plural(
                "{} added a monster {} at ({}, {}) saying '{}' with {} health point\n",
                "{} added a monster {} at ({}, {}) saying '{}' with {} health points\n",
                hp,
                self.nickname, name, x, y, hello, hp,
            )

    def do_attack(self, arg):
        """Атаковать монстра с выбором оружия."""
        args = shlex.split(arg)
        name_monster = args[0]
        self.player_weapon = args[2]
        damage = self.weapons[self.player_weapon]

        x, y = self.player_x, self.player_y
        if (x, y) not in monsters:
            self.writer.write(self._("No monster here\n").encode())
            return

        if name_monster not in monsters[(x, y)]:
            self.writer.write(self._("No {} here\n").format(name_monster).encode())
            return

        name, hello, hp = monsters[(x, y)]
        new_hp = hp - damage

        broadcast(
            "{} attacked {} at ({}, {}), damage {} hp\n",
            self.nickname, name_monster, x, y, damage,
        )
        if new_hp <= 0:
            del monsters[(x, y)]
            broadcast("{} died\n", name_monster)
        else:
            monsters[(x, y)] = (name_monster, hello, new_hp)
            broadcast_plural(
                "{} now has {} health point\n",
                "{} now has {} health points\n",
                new_hp,
                name_monster, new_hp,
            )

    def do_locale(self, arg):
        """
        Установить локаль клиента.

        Использование: locale <имя_локали> (например, ru_RU.UTF8).
        """
        args = shlex.split(arg)
        locale_str = args[0] if args else DEFAULT_LOCALE
        self.locale = locale_str
        self._, self.ngettext = get_translator(self.locale)
        self.writer.write(
            self._("Set up locale: {}\n").format(self.locale).encode())

    def do_movemonsters(self, arg):
        """
        Включить или выключить режим бродячих монстров.

        Использование: movemonsters on / movemonsters off
        """
        if arg == "on":
            task = self.server.monsters_task
            if self.server.monsters_enabled and task and not task.done():
                self.writer.write(self._("Moving monsters: on\n").encode())
            else:
                self.server.monsters_enabled = True
                self.server.monsters_task = asyncio.create_task(move_monsters_loop())
                broadcast("Moving monsters: on\n")
        elif arg == "off":
            if self.server.monsters_task and not self.server.monsters_task.done():
                self.server.monsters_task.cancel()
            self.server.monsters_enabled = False
            broadcast("Moving monsters: off\n")


async def move_monsters_loop():
    """Циклическое перемещение монстров каждые 30 секунд."""
    while True:
        await asyncio.sleep(30)
        success = False
        coords_of_monsters = list(monsters.keys())
        while not success:
            if not coords_of_monsters:
                break
            old_x, old_y = random.choice(coords_of_monsters)
            name, hello, hp = monsters[(old_x, old_y)]
            direction = random.choice(list(DIRECTIONS.keys()))
            dx, dy = DIRECTIONS[direction]
            new_x = (old_x + dx) % FIELD_SIZE
            new_y = (old_y + dy) % FIELD_SIZE
            if (new_x, new_y) in monsters:
                continue
            del monsters[(old_x, old_y)]
            monsters[(new_x, new_y)] = (name, hello, hp)
            broadcast("{} moved one cell {}\n", name, direction)
            for client in users.values():
                player = getattr(client, 'game', None)
                if player and player.player_x == new_x and player.player_y == new_y:
                    if name in CUSTOM_MONSTERS:
                        client.write((cowthink(hello, cowfile=CUSTOM_MONSTERS[name]) + "\n").encode())
                    else:
                        client.write((cowthink(hello, cow=name) + "\n").encode())
            success = True


class Server:
    """Сервер."""

    def __init__(self, host=HOST, port=PORT):
        """Инициализация сервера на заданном порте и хосте."""
        self.host = host
        self.port = port
        self.clients = dict()
        self.monsters_task = None
        self.monsters_enabled = True

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

        game = Game(self, writer, username)
        writer.game = game
        broadcast("{} joined the game\n", username)
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
            broadcast("{} left the game\n", username)

    async def run(self):
        """Запуск сервера."""
        server = await asyncio.start_server(self.handle_client, self.host, self.port)
        addr = ', '.join(str(sock.getsockname()) for sock in server.sockets)
        print(f'Working on {addr}')

        self.monsters_task = asyncio.create_task(move_monsters_loop())

        async with server:
            await server.serve_forever()


def run_server(host=HOST, port=PORT):
    """
    Запустить сервер в синхронном контексте.

    Используется в качестве target для multiprocessing.Process.
    """
    try:
        asyncio.run(Server(host=host, port=port).run())
    except KeyboardInterrupt:
        print('Server stopped successfully.')


if __name__ == '__main__':
    run_server()
