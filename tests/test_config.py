import unittest

from unlocker.argparser import parser


class TestArgParser(unittest.TestCase):
    def test_defaults(self):
        # mocking sys.argv is risky if running in parallel, but here we can pass args to parse_args
        args = parser.parse_args([])
        self.assertEqual(args.config, "config.ini")
        self.assertFalse(args.verbose)
        self.assertIsNone(args.logfile)

    def test_custom_args(self):
        args = parser.parse_args(["--config", "myconf.ini", "--verbose", "--logfile", "out.log"])
        self.assertEqual(args.config, "myconf.ini")
        self.assertTrue(args.verbose)
        self.assertEqual(args.logfile, "out.log")
