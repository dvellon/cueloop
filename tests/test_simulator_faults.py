from __future__ import annotations

import unittest

from cueloop.simulator import parse_sequence


class SimulatorTests(unittest.TestCase):
    def test_sequence_parser(self) -> None:
        result = parse_sequence("background:1.5,door_knock:3")
        self.assertEqual([(item.event, item.seconds) for item in result], [("background", 1.5), ("door_knock", 3.0)])

    def test_sequence_parser_rejects_unknown(self) -> None:
        with self.assertRaises(Exception):
            parse_sequence("glass_break:2")


if __name__ == "__main__":
    unittest.main()
