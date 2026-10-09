"""Focused numerical/regression checks for output correction experiments."""
import unittest
import numpy as np
from scipy.special import softmax
from calibrate_outputs import fit_accuracy_bias, fit_nll, paired_ci, select_correction


class CalibrationTests(unittest.TestCase):
    def test_quantized_ties_and_monotonicity(self):
        rng = np.random.default_rng(1709)
        for _ in range(40):
            z = rng.integers(-4, 5, size=(80, 5)) / 4
            y = rng.integers(0, 5, len(z))
            initial = rng.integers(-2, 3, size=5) / 4
            old = ((z+initial).argmax(1) == y).sum()
            bias = fit_accuracy_bias(z, y, initial)
            self.assertGreaterEqual(((z+bias).argmax(1) == y).sum(), old)
            self.assertTrue(np.isfinite(bias).all())
            self.assertLessEqual(np.max(np.abs(bias)), 3)

    def test_equality_can_win_against_mixed_rival_indices(self):
        # At the shared threshold k=2 wins its tie with class 4, but loses
        # to class 0. Equality can therefore outperform either strict side.
        z = np.full((2, 5), -10.)
        z[0, 0] = z[1, 4] = 1.
        z[:, 2] = 0.
        y = np.array([0, 2])
        self.assertEqual(((z+np.array([0, 0, 1, 0, 0])).argmax(1) == y).sum(), 2)
        bias = fit_accuracy_bias(z, y)
        self.assertEqual(((z+bias).argmax(1) == y).sum(), 2)

    def test_synthetic_bias_improves_independent_samples(self):
        rng = np.random.default_rng(1309)
        latent = rng.normal(size=(2000, 5))
        y = latent.argmax(1)
        biased = latent + np.array([1., -.8, .3, 0., -.2])
        bias = fit_accuracy_bias(biased[:1000], y[:1000])
        base = (biased[1000:].argmax(1) == y[1000:]).mean()
        corrected = ((biased[1000:]+bias).argmax(1) == y[1000:]).mean()
        self.assertGreater(corrected, base + .1)
        scale, nll_bias = fit_nll(biased[:1000], y[:1000])
        self.assertGreater(((biased[1000:]*scale+nll_bias).argmax(1) == y[1000:]).mean(), base + .1)

    def test_temperature_preserves_winner(self):
        rng = np.random.default_rng(26)
        z = rng.integers(-20, 21, size=(100, 5)).astype(float)
        for temp in (.25, .5, 2., 10.):
            np.testing.assert_array_equal(z.argmax(1), softmax(z/temp, axis=1).argmax(1))

    def test_paired_interval_and_discordant_counts(self):
        y = np.zeros(10, dtype=int)
        base = np.tile([0., 1., -2., -2., -2.], (10, 1))
        new = base.copy()
        new[:3, :2] = [1., 0.]
        result = paired_ci(y, base, new)
        self.assertAlmostEqual(result['delta'], .3)
        self.assertEqual((result['corrected'], result['broken']), (3, 0))
        expected_width = 1.96*np.std(np.r_[np.ones(3), np.zeros(7)], ddof=1)/np.sqrt(10)
        np.testing.assert_allclose(result['ci95'], [.3-expected_width, .3+expected_width])
        np.testing.assert_array_equal(paired_ci(y, base, base)['ci95'], [0., 0.])

    def test_fewer_parameters_win_exact_validation_tie(self):
        self.assertEqual(select_correction({'vector_nll': .7, 'bias_accuracy': .7}), 'bias_accuracy')
        self.assertEqual(select_correction({'bias_nll': .7, 'identity': .7}), 'identity')
        self.assertEqual(select_correction({'identity': .7, 'vector_nll': .71}), 'vector_nll')


if __name__ == '__main__':
    unittest.main()
