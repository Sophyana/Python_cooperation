import asyncio
import shlex

FIELD_SIZE = 10


class GameState:
    def __init__(self):
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}  # (x, y) -> (name, hello, hp)

    def move(self, dx, dy):
        self.player_x = (self.player_x + dx) % FIELD_SIZE
        self.player_y = (self.player_y + dy) % FIELD_SIZE
        x, y = self.player_x, self.player_y
        if (x, y) in self.monsters:
            name, hello, hp = self.monsters[(x, y)]
            return f"encounter {x} {y} {shlex.quote(name)} {shlex.quote(hello)}"
        return f"ok {x} {y}"

    def addmon(self, name, x, y, hp, hello):
        replaced = (x, y) in self.monsters
        self.monsters[(x, y)] = (name, hello, hp)
        return "replaced" if replaced else "added"

    def attack(self, monster_name, damage):
        x, y = self.player_x, self.player_y
        if (x, y) not in self.monsters:
            return "no_monster"
        name, hello, hp = self.monsters[(x, y)]
        if name != monster_name:
            return "wrong_monster"
        new_hp = hp - damage
        if new_hp <= 0:
            del self.monsters[(x, y)]
            return f"killed {damage}"
        self.monsters[(x, y)] = (name, hello, new_hp)
        return f"damaged {damage} {new_hp}"


async def handle_client(reader, writer):
    state = GameState()
    while True:
        line = await reader.readline()
        if not line:
            break
        command = line.decode().strip()
        if not command:
            continue
        parts = shlex.split(command)
        cmd = parts[0]
        if cmd == "exit":
            break
        elif cmd == "move":
            response = state.move(int(parts[1]), int(parts[2]))
        elif cmd == "addmon":
            # addmon <name> <x> <y> <hp> <hello>
            name, x, y, hp, hello = parts[1], int(parts[2]), int(parts[3]), int(parts[4]), parts[5]
            response = state.addmon(name, x, y, hp, hello)
        elif cmd == "attack":
            # attack <monster_name> <damage>
            response = state.attack(parts[1], int(parts[2]))
        else:
            response = "unknown_command"
        writer.write((response + "\n").encode())
        await writer.drain()
    writer.close()
    await writer.wait_closed()


async def main():
    server = await asyncio.start_server(handle_client, "127.0.0.1", 1337)
    async with server:
        await server.serve_forever()


asyncio.run(main())
