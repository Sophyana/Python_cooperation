from pathlib import Path
import sys
import zlib


def find_commit(repo_path, commit_hash):
    with open(f"{repo_path}/.git/objects/{commit_hash[:2]}/{commit_hash[2:]}", "rb") as f:
        message = f.read()

    decompressed_message = zlib.decompress(message)
    obj_type, _, content = decompressed_message.partition(b"\x00")

    return content.decode()


def one_arg(repo_path):
    repo = Path(f"{repo_path}/.git/refs/heads")

    if not repo.is_dir():
        print(f"Ошибка: {repo_path} не является каталогом.")
        exit(0)

    for item in repo.iterdir():
        print(item.name)


def two_arg(repo_path, branch_name):
    with open(f"{repo_path}/.git/refs/heads/{branch_name}", "r") as f:
        commit = f.read()

    content = find_commit(repo_path, commit[:-1])
    print(content)

    tree_walk(repo_path, content)
    print("")

    with open(f"{repo_path}/.git/logs/refs/heads/{branch_name}", "r") as f:
        log = f.read()

    for el in log.split("\n")[:-1]:
        commit_hash = el.split(" ")[1]
        print(f"TREE for commit {commit_hash}")
        tree_walk(repo_path, find_commit(repo_path, commit_hash))

def tree_walk(repo_path, content):
    tree = content.split("\n")[0].split(" ")[1]
    with open(f"{repo_path}/.git/objects/{tree[:2]}/{tree[2:]}", "rb") as f:
        tree_content = f.read()

    branches = zlib.decompress(tree_content)
    obj_type, _, data = branches.partition(b"\x00")

    index = 0
    result = []
    git_modes = {
        "100644": "blob",
        "40000": "tree"
    }

    while index < len(data):
        mode_end = data.find(b" ", index)
        mode = data[index:mode_end].decode()
        index = mode_end + 1

        name_end = data.find(b"\x00", index)
        name = data[index:name_end].decode()
        index = name_end + 1

        sha1 = data[index:index + 20]
        index += 20

        sha1_hex = sha1.hex()
        result.append(f"{git_modes.get(mode, 'Неизвестный тип')} {sha1_hex}    {name} ")

    print("\n".join(result))

if len(sys.argv) < 2:
    print("Использование: script.py <путь_к_каталогу> [<имя_ветки>]")
    sys.exit(1)

repo_path = sys.argv[1]

if len(sys.argv) == 2:
    one_arg(repo_path)
else:
    branch_name = sys.argv[2]
    two_arg(repo_path, branch_name)