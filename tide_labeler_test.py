import unittest

from tide_labeler import NEAP_MARK, SPRING_MARK, label_tides


class LabelTidesTest(unittest.TestCase):
    def test_marks_single_extrema_per_cycle(self):
        heights = [10.0, 11.2, 12.4, 12.3, 11.1, 9.8, 9.9, 10.5]
        labels = label_tides(heights, tolerance=0.05)

        self.assertEqual(labels.count(SPRING_MARK), 1)
        self.assertEqual(labels.count(NEAP_MARK), 1)
        self.assertEqual(labels.index(SPRING_MARK), 2)
        self.assertEqual(labels.index(NEAP_MARK), 5)

    def test_ignores_small_fluctuations(self):
        heights = [
            10.0,
            10.02,
            10.01,
            10.03,
            9.97,
            9.96,
            9.94,
            10.02,
            10.28,
            10.25,
            10.04,
        ]
        labels = label_tides(heights, tolerance=0.05)

        self.assertEqual(labels.count(SPRING_MARK), 1)
        self.assertEqual(labels.count(NEAP_MARK), 1)
        self.assertEqual(labels.index(SPRING_MARK), 8)
        self.assertEqual(labels.index(NEAP_MARK), 6)


if __name__ == "__main__":
    unittest.main()
