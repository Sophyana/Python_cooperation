"""Модуль общих констант."""
import os
from io import StringIO
from cowsay import read_dot_cow

PORT = 8888
HOST = "localhost"
FIELD_SIZE = 10
INTRO = "<<< Welcome to Python-MUD 0.1 >>>"
CUSTOM_MONSTERS = {"jgsbat": read_dot_cow(StringIO(r"""
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
        """))}

_EXTRA_MONSTER_FILE = os.path.join(os.path.dirname(__file__), "extra_monster.cow")
if os.path.exists(_EXTRA_MONSTER_FILE):
    with open(_EXTRA_MONSTER_FILE) as _f:
        CUSTOM_MONSTERS["pinguin"] = read_dot_cow(_f)
