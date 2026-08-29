import unittest

import chess

from src.chess.pieces import (
    chess_board_to_position,
    normalize_piece_id,
    normalize_position,
    serialize_position,
)


class PieceFormatTests(unittest.TestCase):
    def test_legacy_piece_is_normalized(self):
        self.assertEqual(normalize_piece_id("RB0"), "RB")
        self.assertEqual(normalize_piece_id("pN1"), "pN")

    def test_empty_tokens_are_normalized(self):
        for token in ("", "--", "0", "1", "."):
            self.assertEqual(normalize_piece_id(token), "")

    def test_initial_chess_board_has_canonical_ids(self):
        position = chess_board_to_position(chess.Board())
        self.assertEqual(len(position), 64)
        self.assertEqual(position[0], "TN")
        self.assertEqual(position[4], "RN")
        self.assertEqual(position[60], "RB")

    def test_position_round_trip_serialization(self):
        original = chess_board_to_position(chess.Board())
        serialized = serialize_position(original)
        restored = normalize_position(serialized.split())
        self.assertEqual(restored, original)


if __name__ == "__main__":
    unittest.main()
