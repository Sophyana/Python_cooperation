"""Модуль общих констант."""
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
