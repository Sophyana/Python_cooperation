from pathlib import Path
import zlib
import sys


for obj in Path.(sys.argv[1]).glob(".git/object/??/*"):
	print(obj)
	data = zlib.decopress(obj.read_bytes())


