import unittest
from unittest.mock import MagicMock, patch

import unlock


class TestUnlockScript(unittest.TestCase):
    def test_import_unlock(self):
        """Just importing the module to ensure it's covered."""
        self.assertTrue(hasattr(unlock, "main"))

    @patch("os.path.isfile")
    @patch("unlock.ServerUnlocker")
    @patch("asyncio.run")
    @patch("unlock.parser.parse_args")
    @patch("configparser.ConfigParser")
    def test_main_success(
        self, mock_config_parser, mock_parse_args, mock_asyncio_run, mock_server_unlocker, mock_isfile
    ):
        """Test main execution path with valid configuration."""
        # Setup mocks
        mock_isfile.return_value = True
        mock_args = MagicMock()
        mock_args.verbose = False
        mock_args.logfile = None
        mock_args.config = "config.ini"
        mock_parse_args.return_value = mock_args

        mock_config = MagicMock()
        mock_config.sections.return_value = ["server1"]

        # Setup get behavior for required args
        def config_get_side_effect(section, arg, fallback=None):
            if arg in ("host", "port", "ssh_private_key", "known_hosts", "cryptsetup_passphrase"):
                return "value"
            return fallback

        mock_config.get.side_effect = config_get_side_effect
        mock_config.getint.return_value = 22

        # Make config indexable like a dict for client initialization
        mock_config.__getitem__.return_value = MagicMock()

        mock_config_parser.return_value = mock_config

        # Run main
        unlock.main()

        # Verifications
        mock_config.read.assert_called_with("config.ini")
        mock_server_unlocker.assert_called()
        mock_asyncio_run.assert_called()

    @patch("os.path.isfile")
    @patch("sys.exit")
    @patch("sys.stderr")
    @patch("unlock.parser.parse_args")
    @patch("configparser.ConfigParser")
    def test_main_no_servers(self, mock_config_parser, mock_parse_args, mock_stderr, mock_exit, mock_isfile):
        """Test main exits if no servers configured."""
        mock_isfile.return_value = True
        mock_exit.side_effect = SystemExit
        mock_args = MagicMock()
        mock_args.verbose = False
        mock_args.logfile = None
        mock_args.config = "config.ini"
        mock_parse_args.return_value = mock_args

        mock_config = MagicMock()
        mock_config.sections.return_value = []  # No sections
        mock_config_parser.return_value = mock_config

        with self.assertRaises(SystemExit):
            unlock.main()

        mock_exit.assert_called_with(1)

    @patch("os.path.isfile")
    @patch("sys.exit")
    @patch("sys.stderr")
    @patch("unlock.parser.parse_args")
    @patch("configparser.ConfigParser")
    def test_main_missing_required_arg(self, mock_config_parser, mock_parse_args, mock_stderr, mock_exit, mock_isfile):
        """Test main exits if a required argument is missing."""
        mock_isfile.return_value = True
        mock_exit.side_effect = SystemExit
        mock_args = MagicMock()
        mock_args.verbose = False
        mock_args.logfile = None
        mock_args.config = "config.ini"
        mock_parse_args.return_value = mock_args

        mock_config = MagicMock()
        mock_config.sections.return_value = ["server1"]
        # Simulate missing 'host'
        mock_config.get.return_value = None
        mock_config_parser.return_value = mock_config

        with self.assertRaises(SystemExit):
            unlock.main()

        mock_exit.assert_called_with(1)

    @patch("os.path.isfile")
    @patch("sys.exit")
    @patch("sys.stderr")
    @patch("unlock.parser.parse_args")
    @patch("configparser.ConfigParser")
    def test_main_invalid_port(self, mock_config_parser, mock_parse_args, mock_stderr, mock_exit, mock_isfile):
        """Test main exits if port is invalid."""
        mock_isfile.return_value = True
        mock_exit.side_effect = SystemExit
        mock_args = MagicMock()
        mock_args.verbose = False
        mock_args.logfile = None
        mock_args.config = "config.ini"
        mock_parse_args.return_value = mock_args

        mock_config = MagicMock()
        mock_config.sections.return_value = ["server1"]
        # All strings present
        mock_config.get.return_value = "somevalue"
        # Port raises ValueError
        mock_config.getint.side_effect = ValueError
        mock_config_parser.return_value = mock_config

        with self.assertRaises(SystemExit):
            unlock.main()

        mock_exit.assert_called_with(1)
