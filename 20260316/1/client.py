import socket
import shlex
from io import StringIO
from cowsay import cowthink, list_cows, read_dot_cow

HOST = "127.0.0.1"
PORT = 1337

FIELD_SIZE = 10

CUSTOM_MONSTERS = {
    "jgsbat": read_dot_cow(StringIO(r"""
        $the_cow = <<EOC;
            ,_                    _,
            ) '-._  ,_    _,  _.-' (
            )  _.-'.|\\--//|.'-._  (
             )'   .'\/o\/o\/'.   `(
              ) .' . \====/ . '. (
               )  / <<    >> \  (
                '-._/``  ``\_.-'
          jgs     __\\'--'//__
                 (((""`  `"")))
        EOC
        """))
}

WEAPONS = {
    "sword": 10,
    "spear": 15,
    "axe":   20,
}

MOVE_DELTAS = {
    "up":    (0, -1),
    "down":  (0,  1),
    "left":  (-1, 0),
    "right": (1,  0),
}


class MUDClient:
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((HOST, PORT))
        self.rfile = self.sock.makefile("r", buffering=1)
        self.current_weapon = "sword"

    def _send(self, command):
        self.sock.sendall((command + "\n").encode())
        return self.rfile.readline().rstrip("\n")

    def _handle_move(self, cmd):
        dx, dy = MOVE_DELTAS[cmd]
        response = self._send(f"move {dx} {dy}")
        parts = shlex.split(response)
        if parts[0] == "ok":
            print(f"Moved to ({parts[1]}, {parts[2]})")
        elif parts[0] == "encounter":
            x, y, name, hello = parts[1], parts[2], parts[3], parts[4]
            print(f"Moved to ({x}, {y})")
            if name in CUSTOM_MONSTERS:
                print(cowthink(hello, cowfile=CUSTOM_MONSTERS[name]))
            else:
                print(cowthink(hello, cow=name))

    def _handle_addmon(self, arg):
        usage = "Usage: addmon <NAME> hello <MSG> hp <HP> coords <X> <Y>"
        args = shlex.split(arg)
        if not args:
            print(usage)
            return
        name = args[0]
        if name not in list_cows() | set(CUSTOM_MONSTERS.keys()):
            print(f"Unknown monster {name}")
            return
        params = {}
        i = 1
        try:
            while i < len(args):
                if args[i] == "hello":
                    params["hello"] = args[i + 1]
                    i += 2
                elif args[i] == "hp":
                    params["hp"] = int(args[i + 1])
                    i += 2
                elif args[i] == "coords":
                    params["x"] = int(args[i + 1])
                    params["y"] = int(args[i + 2])
                    i += 3
                else:
                    print(f"Unknown parameter: {args[i]}\n{usage}")
                    return
        except (IndexError, ValueError):
            print(f"Invalid arguments\n{usage}")
            return
        if not all(k in params for k in ("hello", "hp", "x", "y")):
            print(f"Missing required parameters\n{usage}")
            return
        x, y = params["x"], params["y"]
        if not (0 <= x < FIELD_SIZE and 0 <= y < FIELD_SIZE):
            print(f"Coordinates out of bounds. Field is {FIELD_SIZE}x{FIELD_SIZE}")
            return
        response = self._send(
            f"addmon {shlex.quote(name)} {x} {y} {params['hp']} {shlex.quote(params['hello'])}"
        )
        print(f"Added monster {name} at ({x}, {y}) saying {params['hello']} with {params['hp']} HP")
        if response == "replaced":
            print("Replaced the old monster")

    def _handle_attack(self, arg):
        usage = "Usage: attack <NAME> [with <WEAPON>]"
        args = shlex.split(arg) if arg else []
        if not args:
            print(usage)
            return
        name = args[0]
        weapon = self.current_weapon
        if len(args) == 3 and args[1] == "with":
            if args[2] not in WEAPONS:
                print(f"Unknown weapon {args[2]}")
                return
            weapon = args[2]
        elif len(args) != 1:
            print(usage)
            return
        self.current_weapon = weapon
        damage = WEAPONS[weapon]
        response = self._send(f"attack {shlex.quote(name)} {damage}")
        parts = response.split()
        if parts[0] == "no_monster":
            print("No monster here")
        elif parts[0] == "wrong_monster":
            print(f"No {name} here")
        elif parts[0] == "damaged":
            print(f"Attacked {name}, damage {parts[1]} hp")
            print(f"{name} now has {parts[2]} hp")
        elif parts[0] == "killed":
            print(f"Attacked {name}, damage {parts[1]} hp")
            print(f"{name} died")

    def run(self):
        print("<<< Welcome to Python-MUD 0.1 >>>")
        while True:
            try:
                line = input(">> ")
            except (EOFError, KeyboardInterrupt):
                print()
                self.sock.close()
                return
            line = line.strip()
            if not line:
                continue
            try:
                parts = shlex.split(line)
            except ValueError as e:
                print(f"Parse error: {e}")
                continue
            cmd = parts[0]
            if cmd == "exit":
                self._send("exit")
                break
            elif cmd in MOVE_DELTAS:
                if len(parts) != 1:
                    print("This command takes no arguments")
                    continue
                self._handle_move(cmd)
            elif cmd == "addmon":
                self._handle_addmon(line[len(cmd):].strip())
            elif cmd == "attack":
                self._handle_attack(line[len(cmd):].strip())
            else:
                print(f"Unknown command: {cmd}")
        self.sock.close()


if __name__ == "__main__":
    MUDClient().run()
