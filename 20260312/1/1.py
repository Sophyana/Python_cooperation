from io import StringIO
from cowsay import read_dot_cow, cowthink, list_cows
import shlex
import cmd


class Game(cmd.Cmd):
    prompt = ">> "
    intro = "<<< Welcome to Python-MUD 0.1 >>>"
    field_size = 10
    custom_monsters = {
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

    def __init__(self):
        super().__init__()
        self.player_x = 0
        self.player_y = 0
        self.monsters = {}

    def encounter(self, x, y):
        if (x, y) in self.monsters:
            name, hello, hp = self.monsters[(x, y)]
            if name in self.custom_monsters:
                print(cowthink(hello, cowfile=self.custom_monsters[name]))
            else:
                print(cowthink(hello, cow=name))

    def move_player(self, dx, dy, arg):
        if arg:
            print("Move commands should not have arguments.")
            return
        self.player_x = (self.player_x + dx) % self.field_size
        self.player_y = (self.player_y + dy) % self.field_size
        print(f"Moved to ({self.player_x}, {self.player_y})")
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
        """Add a monster to the game."""
        usage = "Usage: addmon <NAME> hello <MESSAGE> hp <HP> coords <X> <Y>"
        args = shlex.split(arg)
        if not args:
            print(f"Invalid arguments\n{usage}")
            return

        name = args[0]
        params = {}
        param_names = ["hello", "hp", "coords"]
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

            if len(params) != len(param_names):
                print(f"Invalid number of arguments\n{usage}")
                return

            hello = params["hello"]
            hp = int(params["hp"])
            x, y = params["coords"]

            if not (0 <= x < self.field_size and 0 <= y < self.field_size):
                print(f"Invalid coordinates\nField size is {self.field_size}x{self.field_size}")
                return

            replaced = (x, y) in self.monsters
            self.monsters[(x, y)] = (name, hello, hp)
            print(f"Added monster {name} to ({x}, {y}) saying {hello} with {hp} HP")
            if replaced:
                print("Replaced the old monster")

        except (ValueError, IndexError):
            print(f"Invalid arguments\n{usage}")
            return


if __name__ == "__main__":
    Game().cmdloop()
