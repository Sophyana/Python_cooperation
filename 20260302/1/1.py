import sys
from io import StringIO
from cowsay import read_dot_cow, cowthink
import shlex
import cowsay

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
        name, hello = monsters[(x, y)]
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
    if len(args) != 4:
        print("Invalid arguments")
        return
    try:
        name = args[0]
        x = int(args[1])
        y = int(args[2])
        hello = args[3]
    except ValueError:
        print("Invalid arguments")
        return

    if name not in cowsay.CHARS.keys() and name not in custom_monsters:
        print("Cannot add unknown monster")
        return

    replaced = False
    if (x, y) in monsters:
        replaced = True

    monsters[(x, y)] = (name, hello)
    print(f"Added monster {name} to ({x}, {y}) saying {hello}")
    if replaced:
        print("Replaced the old monster")


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
