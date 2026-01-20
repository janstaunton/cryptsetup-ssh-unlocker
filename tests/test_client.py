import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import asyncssh

from unlocker.client import ServerUnlocker


class TestServerUnlocker(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config_mock = MagicMock()
        self.config_mock.get.return_value = "localhost"
        self.config_mock.getint.return_value = 22
        self.config_mock.name = "test-server"

        self.server_unlocker = ServerUnlocker([self.config_mock])

    @patch("asyncssh.connect")
    async def test_ssh_unlock_success(self, mock_connect):
        # Setup mock connection
        mock_conn = AsyncMock()
        mock_connect.return_value.__aenter__.return_value = mock_conn

        # Call method
        ssh_options = {"host": "localhost"}
        await self.server_unlocker.ssh_unlock(ssh_options, "passphrase", "test-server")

        # Verify
        mock_conn.run.assert_awaited_with("cat > /lib/cryptsetup/passfifo", input="passphrase", check=True)

    @patch("asyncio.get_running_loop")
    @patch("unlocker.client.ServerUnlocker.ssh_unlock")
    async def test_unlock_server_success(self, mock_ssh_unlock, mock_get_loop):
        # Mock loop and connection
        mock_loop = MagicMock()
        mock_transport = MagicMock()
        mock_protocol = MagicMock()

        # create_connection returns (transport, protocol)
        mock_loop.create_connection = AsyncMock(return_value=(mock_transport, mock_protocol))
        mock_get_loop.return_value = mock_loop

        # We need to interrupt the infinite loop in unlock_server
        # essentially we want it to run once.
        # But unlock_server has a `while True`.
        # We can throw an exception to break it or mock sleep to raise exception?
        # A standard pattern for testing infinite loops is to mock sleep and raise an exception after N calls.

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError("Stop loop")]

            try:
                await self.server_unlocker.unlock_server(self.config_mock)
            except asyncio.CancelledError:
                pass

            # Verify TCP handshake was attempted
            mock_loop.create_connection.assert_awaited()

            # Verify SSH unlock was called
            mock_ssh_unlock.assert_awaited()

    @patch("asyncio.get_running_loop")
    async def test_unlock_server_connection_refused(self, mock_get_loop):
        mock_loop = MagicMock()
        mock_loop.create_connection = AsyncMock(side_effect=ConnectionRefusedError)
        mock_get_loop.return_value = mock_loop

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError("Stop loop")]

            try:
                await self.server_unlocker.unlock_server(self.config_mock)
            except asyncio.CancelledError:
                pass

            # Should have slept and retried (well, loop ran twice based on sleep side effect)
            self.assertTrue(mock_sleep.called)

    @patch("asyncio.get_running_loop")
    async def test_unlock_server_timeout_error(self, mock_get_loop):
        """Test handling of asyncio.TimeoutError during connection."""
        mock_loop = MagicMock()
        mock_loop.create_connection = AsyncMock(side_effect=asyncio.TimeoutError)
        mock_get_loop.return_value = mock_loop

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError("Stop loop")]
            try:
                await self.server_unlocker.unlock_server(self.config_mock)
            except asyncio.CancelledError:
                pass
            self.assertTrue(mock_sleep.called)

    @patch("asyncio.get_running_loop")
    async def test_unlock_server_disconnect_error(self, mock_get_loop):
        """Test handling of asyncssh.DisconnectError."""
        # We need to reach the part where it tries SSH unlock setup or similar.
        # But here valid connection -> wait_for -> ssh_unlock
        # Let's say connect succeeds, but ssh_unlock raises DisconnectError

        mock_loop = MagicMock()
        mock_loop.create_connection = AsyncMock(return_value=(MagicMock(), MagicMock()))
        mock_get_loop.return_value = mock_loop

        # We can mock ssh_unlock on the instance if we didn't patch the class method
        # But better to patch the class method or self.server_unlocker.ssh_unlock
        with patch.object(self.server_unlocker, "ssh_unlock", side_effect=asyncssh.DisconnectError(1, "Bye")):
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                mock_sleep.side_effect = [None, asyncio.CancelledError("Stop loop")]
                try:
                    await self.server_unlocker.unlock_server(self.config_mock)
                except asyncio.CancelledError:
                    pass
                self.assertTrue(mock_sleep.called)

    @patch("asyncio.get_running_loop")
    async def test_unlock_server_os_error(self, mock_get_loop):
        """Test handling of OSError."""
        mock_loop = MagicMock()
        mock_loop.create_connection = AsyncMock(side_effect=OSError("Network unreachable"))
        mock_get_loop.return_value = mock_loop

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_sleep.side_effect = [None, asyncio.CancelledError("Stop loop")]
            try:
                await self.server_unlocker.unlock_server(self.config_mock)
            except asyncio.CancelledError:
                pass
            self.assertTrue(mock_sleep.called)
