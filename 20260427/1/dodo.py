"""doit-задачи для автоматизации сборки MUD: i18n, html, test."""
import glob
import os
import shutil

DOIT_CONFIG = {"default_tasks": ["html"]}

LOCALES_DIR = "mood/server/locales"
POT_FILE = f"{LOCALES_DIR}/messages.pot"
PO_FILE = f"{LOCALES_DIR}/ru_RU/LC_MESSAGES/messages.po"
MO_FILE = f"{LOCALES_DIR}/ru_RU/LC_MESSAGES/messages.mo"


def init_or_update_po():
    """Использовать init при отсутствии PO, иначе update."""
    if os.path.exists(PO_FILE):
        cmd = (f"pybabel update -D messages -d {LOCALES_DIR} "
               f"-l ru_RU -i {POT_FILE}")
    else:
        cmd = (f"pybabel init -D messages -d {LOCALES_DIR} "
               f"-l ru_RU -i {POT_FILE}")
    return cmd


def task_pot():
    """[Babel] Генерация POT-шаблона."""
    return {
        "actions": [f"pybabel extract -F babel.cfg -o {POT_FILE} ."],
        "targets": [POT_FILE],
        "clean": True,
    }


def task_po():
    """[Babel] Создание/обновление PO-файлов из POT-шаблона."""
    return {
        "actions": [init_or_update_po()],
        "file_dep": [POT_FILE],
        "targets": [PO_FILE],
        "clean": True,
    }


def task_mo():
    """[Babel] Компиляция переводов (.po -> .mo)."""
    return {
        "actions": [f"pybabel compile -D messages -d {LOCALES_DIR}"],
        "file_dep": [PO_FILE],
        "targets": [MO_FILE],
        "clean": True,
    }


def task_i18n():
    """Полная генерация перевода (pot -> po -> mo)."""
    return {
        "actions": None,
        "task_dep": ["pot", "po", "mo"],
    }


def task_html():
    """Генерация html-документации Sphinx."""
    rst_files = glob.glob("source/*.rst")
    return {
        "actions": ["sphinx-build -b html source build/html"],
        "file_dep": ["source/conf.py"] + rst_files,
        "targets": ["build/html/index.html"],
        "clean": [(shutil.rmtree, ["build/html"], {"ignore_errors": True})],
    }


def task_test():
    """Прогон тестов связки клиент+сервер (зависит от i18n)."""
    return {
        "actions": [
            "python3 -m unittest server_test.py",
            "python3 -m unittest client_test.py",
        ],
        "task_dep": ["i18n"],
    }
