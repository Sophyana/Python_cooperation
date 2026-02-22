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


if len(sys.argv) < 2:
    print("Использование: script.py <путь_к_каталогу> [<имя_ветки>]")
    sys.exit(1)

repo_path = sys.argv[1]

if len(sys.argv) == 2:
    one_arg(repo_path)
else:
    branch_name = sys.argv[2]
    two_arg(repo_path, branch_name)