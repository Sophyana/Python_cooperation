import sys
from io import StringIO
from cowsay import read_dot_cow, cowthink
import shlex

FIELD_SIZE = 10
monsters = {}
player_x, player_y = 0, 0


jgsbat = read_dot_cow(StringIO(r"""
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
custom_monsters = {"jgsbat": jgsbat}


def encounter(x, y):
    if (x, y) in monsters:
        name, hello, _ = monsters[(x, y)]
        if name in custom_monsters:
            print(cowthink(hello, cowfile=custom_monsters[name]))
        else:
            print(cowthink(hello, cow=name))


def process_move(direction):
    global player_x, player_y
    if direction == "up":
        player_y = (player_y - 1) % FIELD_SIZE
    elif direction == "down":
        player_y = (player_y + 1) % FIELD_SIZE
    elif direction == "left":
        player_x = (player_x - 1) % FIELD_SIZE
    elif direction == "right":
        player_x = (player_x + 1) % FIELD_SIZE
    print(f"Moved to ({player_x}, {player_y})")
    if (player_x, player_y) in monsters:
        encounter(player_x, player_y)


def process_addmon(args):
    params = {}
    param_names = ["hello", "hp", "coords"]
    try:

        name = args[0]

        i = 1
        while i < (len(args)):
            param_name = args[i]
            if param_name in param_names:
                if param_name == "coords":
                    params[param_name] = (args[i + 1], args[i + 2])
                    i += 3
                else:
                    params[param_name] = args[i + 1]
                    i += 2
            else:
                print(f"Unknown parameter: {param_name}")
                return

        if not all(param in params for param in param_names):
            print("Please write all parameters: hello, hp, coords")
            return

        hello = params["hello"]
        hp = int(params["hp"])
        coords = params["coords"]

        if len(coords) != 2:
            print("Invalid coordinates")
            return
        x, y = int(coords[0]), int(coords[1])

        replaced = False
        if (x, y) in monsters:
            replaced = True

        monsters[(x, y)] = (name, hello, hp)
        print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} HP")
        if replaced:
            print("Replaced the old monster")

    except ValueError:
        print("Invalid arguments")
        return


print("<<< Welcome to Python-MUD 0.1 >>>")
while line := sys.stdin.readline().strip():
    chunks = shlex.split(line)
    command = chunks[0]
    args = chunks[1:]

    if command in ("up", "down", "left", "right"):
        if args:
            print("Invalid arguments")
        else:
            process_move(command)
    elif command == "addmon":
        process_addmon(args)
    else:
        print("Invalid command")
