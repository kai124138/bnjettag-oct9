import unittest
import numpy as np
from check_deployment_stability import apply, constants, choose_representation, selection_indices, REPRESENTATIONS


class DeploymentTests(unittest.TestCase):
    def test_rounding_and_float32_execution(self):
        s, b = constants(np.ones(5), [0.5/256, 1.5/256, -1.5/256, .1, 0], 'fractional8')
        np.testing.assert_array_equal(b[:3], [0, 2/256, -2/256])
        output = apply(np.ones((2, 5), dtype=np.float64), s, b)
        self.assertEqual(output.dtype, np.float32)

    def test_coarsest_exact_tie_and_accuracy_priority(self):
        acc = dict.fromkeys(REPRESENTATIONS, .7)
        self.assertEqual(choose_representation(acc), 'fractional8')
        acc['float32'] = .701
        self.assertEqual(choose_representation(acc), 'float32')

    def test_selection_split_reproduces_calibrator(self):
        y = np.tile(np.arange(5), 13)
        chosen = selection_indices(y, 20260917)
        rng = np.random.default_rng(20260917)
        fit = []
        expected = []
        for k in range(5):
            ids = rng.permutation(np.flatnonzero(y == k))
            fit.extend(ids[:len(ids)//2]); expected.extend(ids[len(ids)//2:])
        np.testing.assert_array_equal(chosen, expected)
        self.assertFalse(set(chosen) & set(fit))
        self.assertEqual(set(chosen) | set(fit), set(range(len(y))))


if __name__ == '__main__':
    unittest.main()
