import unittest

from pyjuliusalign import alignFromTextgrid


class TestAlignFromTextgrid(unittest.TestCase):
    def test_copy_chunking(self):
        self.assertEqual(
            [[10, 20, 30, 40], [50], [60]],
            alignFromTextgrid.copyChunking(
                [10, 20, 30, 40, 50, 60], [[1, 2, 3, 4], [5], [6]]
            ),
        )

    def test_get_best_chunking(self):
        self.assertEqual(
            [[1, 2], [3], [2, 1]],
            alignFromTextgrid.getBestChunking([1, 2, 3, 2, 1], [3, 3, 3]),
        )

        # The buckets can be larger than the chunks available
        self.assertEqual(
            [[1, 2], [3], [2, 1]],
            alignFromTextgrid.getBestChunking([1, 2, 3, 2, 1], [4, 3, 4]),
        )

        # The buckets can be smaller than the chunks available
        self.assertEqual(
            [[1, 2], [3], [2, 1]],
            alignFromTextgrid.getBestChunking([1, 2, 3, 2, 1], [2, 3, 2]),
        )

        # The buckets can be smaller than the chunks available
        self.assertEqual(
            [[1, 2], [3], [2], [1, 3]],
            alignFromTextgrid.getBestChunking([1, 2, 3, 2, 1, 3], [4, 2, 2, 4]),
        )

        self.assertEqual(
            [[1], [2], [4, 3, 2], [3, 1]],
            alignFromTextgrid.getBestChunking([1, 2, 4, 3, 2, 3, 1], [4, 3, 400, 5]),
        )

    def test_iterate_chunks(self):

        sut = alignFromTextgrid.iterateChunks([1, 2, 3, 4, 5, 6], 3)

        for nextVal in [
            [[1], [2], [3, 4, 5, 6]],
            [[1], [2, 3], [4, 5, 6]],
            [[1], [2, 3, 4], [5, 6]],
            [[1], [2, 3, 4, 5], [6]],
            [[1, 2], [3], [4, 5, 6]],
            [[1, 2], [3, 4], [5, 6]],
            [[1, 2], [3, 4, 5], [6]],
            [[1, 2, 3], [4], [5, 6]],
            [[1, 2, 3], [4, 5], [6]],
            [[1, 2, 3, 4], [5], [6]],
        ]:
            self.assertEqual(nextVal, next(sut))

        with self.assertRaises(StopIteration) as _:
            next(sut)
