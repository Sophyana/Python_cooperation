"""Тесты клиента с использованием мокеров (без реального сервера)."""
import unittest
from unittest.mock import Mock, AsyncMock, patch
from io import StringIO

from mood.client.__main__ import Client


class TestClientCommands(unittest.IsolatedAsyncioTestCase):
    """Проверка преобразования пользовательской команды в протокол клиент->сервер."""

    async def asyncSetUp(self):
        """Создать клиента с замоканым writer перед каждым тестом."""
        self.writer = Mock()
        self.writer.drain = AsyncMock()
        self.client = Client("tester", None)
        self.client.writer = self.writer

    async def test_addmon_dragon_valid(self):
        """Команда addmon с одним набором параметров отправляется корректно."""
        await self.client.process_command(
            "addmon dragon hello 'boo' hp 30 coords 1 1")
        self.writer.write.assert_called_once_with(
            b"addmon dragon hello 'boo' hp 30 coords 1 1\n")

    async def test_addmon_cheese_valid(self):
        """Команда addmon с другим набором параметров (имя/координаты)."""
        await self.client.process_command(
            "addmon cheese hello 'squeak' hp 5 coords 2 3")
        self.writer.write.assert_called_once_with(
            b"addmon cheese hello 'squeak' hp 5 coords 2 3\n")

    async def test_addmon_invalid_missing_params(self):
        """Команда addmon с неполным набором параметров не уходит на сервер."""
        with patch('sys.stdout', new_callable=StringIO):
            await self.client.process_command("addmon dragon hp 30")
        self.writer.write.assert_not_called()

    async def test_attack_sword(self):
        """Команда attack с допустимым оружием sword отправляется корректно."""
        await self.client.process_command("attack dragon with sword")
        self.writer.write.assert_called_once_with(
            b"attack dragon with sword\n")

    async def test_attack_axe(self):
        """Команда attack с другим допустимым оружием axe отправляется корректно."""
        await self.client.process_command("attack dragon with axe")
        self.writer.write.assert_called_once_with(
            b"attack dragon with axe\n")

    async def test_attack_invalid_weapon(self):
        """Команда attack с недопустимым оружием — клиент не шлёт на сервер."""
        captured = StringIO()
        with patch('sys.stdout', captured):
            await self.client.process_command("attack dragon with stick")
        self.writer.write.assert_not_called()
        self.assertIn("Unknown weapon", captured.getvalue())


if __name__ == '__main__':
    unittest.main()
