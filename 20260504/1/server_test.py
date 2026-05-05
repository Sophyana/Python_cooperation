"""Тесты отработки сервером команд клиента (запуск сервера в отдельном процессе)."""
import unittest
import multiprocessing
import socket
import time
import asyncio

from mood.server.__main__ import run_server

HOST = "127.0.0.1"
PORT = 8888


def wait_for_server(host, port, timeout=5):
    """Дождаться готовности сервера принимать соединения."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except (ConnectionRefusedError, OSError):
            time.sleep(0.1)
    raise TimeoutError("Server did not start in time.")


class TestMudServer(unittest.IsolatedAsyncioTestCase):
    """Запускаем сервер в отдельном процессе и шлём команды клиента по TCP."""

    @classmethod
    def setUpClass(cls):
        """Поднять сервер в отдельном процессе перед всеми тестами."""
        cls.server_process = multiprocessing.Process(
            target=run_server, kwargs={"host": HOST, "port": PORT}, daemon=True)
        cls.server_process.start()
        wait_for_server(HOST, PORT)

    @classmethod
    def tearDownClass(cls):
        """Остановить серверный процесс после всех тестов."""
        cls.server_process.terminate()
        cls.server_process.join()

    async def asyncSetUp(self):
        """Открыть соединение и зарегистрироваться под ником priest."""
        self.reader, self.writer = await asyncio.open_connection(HOST, PORT)
        self.writer.write(b"priest\n")
        await self.writer.drain()
        response = (await self.reader.readline()).decode().rstrip('\n')
        self.assertEqual(response, "SUCCESS")

    async def asyncTearDown(self):
        """Закрыть соединение клиента."""
        self.writer.close()
        await self.writer.wait_closed()

    async def read_full_response(self, timeout=1.0):
        """Дочитать весь доступный ответ за timeout секунд."""
        buffer = []
        start = time.time()
        while time.time() - start < timeout:
            try:
                line = await asyncio.wait_for(self.reader.readline(), timeout=0.2)
                if not line:
                    break
                buffer.append(line.decode())
            except asyncio.TimeoutError:
                break
        return "".join(buffer)

    async def send_command(self, command):
        """Отправить команду и вернуть ответ сервера."""
        self.writer.write(f"{command}\n".encode())
        await self.writer.drain()
        return await self.read_full_response()

    async def test_addmon(self):
        """Установка монстра рядом с игроком — широковещательное сообщение."""
        response = await self.send_command(
            "addmon dragon hello 'boo' hp 100 coords 5 5")
        self.assertIn("priest", response)
        self.assertIn("added a monster dragon at (5, 5)", response)
        self.assertIn("100 health points", response)

    async def test_approach_monster(self):
        """Подход к монстру: появление монстра и произнесение приветствия."""
        await self.send_command(
            "addmon dragon hello 'boo' hp 100 coords 0 1")
        response = await self.send_command("down")
        self.assertIn("Moved to (0, 1)", response)
        self.assertIn("boo", response)

    async def test_attack_monster(self):
        """Атака на монстра: широковещательное сообщение об уроне и новом hp."""
        await self.send_command(
            "addmon dragon hello 'boo' hp 100 coords 0 0")
        response = await self.send_command("attack dragon with sword")
        self.assertIn("priest attacked dragon at (0, 0)", response)
        self.assertIn("damage 10 hp", response)
        self.assertIn("dragon now has 90 health points", response)


if __name__ == '__main__':
    unittest.main()
