"""Tests for the geometric Brownian motion stock-price simulator."""

import unittest
from math import exp, isfinite, log, sqrt
from statistics import mean, variance

from OptionsHedgingLab.market import simulate_gbm_path


def make_path(**overrides):
    """Use one baseline scenario and change only what each test needs."""
    inputs = dict(
        stock_price=100.0,
        drift=0.05,
        volatility=0.20,
        time_to_expiry=1.0,
        steps=12,
        seed=42,
    )
    inputs.update(overrides)
    return simulate_gbm_path(**inputs)


class TestMarket(unittest.TestCase):
    def test_time_grid_includes_start_and_expiry(self):
        path = make_path(stock_price=80.0, time_to_expiry=0.5, steps=4)

        self.assertEqual(path[0], (0.0, 80.0))
        self.assertEqual([t for t, _ in path], [0.0, 0.125, 0.25, 0.375, 0.5])
        for _, price in path:
            self.assertTrue(isfinite(price))
            self.assertGreater(price, 0.0)

    def test_seed_controls_the_path(self):
        self.assertEqual(make_path(seed=42), make_path(seed=42))
        self.assertNotEqual(make_path(seed=42), make_path(seed=43))

    def test_zero_drift_and_volatility_give_a_flat_path(self):
        for _, price in make_path(drift=0.0, volatility=0.0):
            self.assertEqual(price, 100.0)

    def test_zero_volatility_gives_deterministic_growth(self):
        for drift in (0.05, -0.05):
            with self.subTest(drift=drift):
                for t, price in make_path(drift=drift, volatility=0.0):
                    self.assertAlmostEqual(price, 100.0 * exp(drift * t), places=10)

    def test_log_returns_have_the_expected_mean_and_variance(self):
        # Compare one six-month return from each of 4,000 seeded paths.
        dt = 0.5
        drift = 0.05
        volatility = 0.40
        returns = []

        for seed in range(4000):
            start, end = make_path(
                drift=drift,
                volatility=volatility,
                time_to_expiry=dt,
                steps=1,
                seed=seed,
            )
            returns.append(log(end[1] / start[1]))

        expected_mean = (drift - 0.5 * volatility**2) * dt
        expected_variance = volatility**2 * dt
        n = len(returns)

        # Allow five standard errors for sampling variation.
        self.assertAlmostEqual(
            mean(returns),
            expected_mean,
            delta=5 * sqrt(expected_variance / n),
        )
        self.assertAlmostEqual(
            variance(returns),
            expected_variance,
            delta=5 * expected_variance * sqrt(2 / (n - 1)),
        )

    def test_invalid_inputs_raise_value_error(self):
        cases = [
            {"stock_price": 0.0},
            {"stock_price": float("inf")},
            {"drift": float("nan")},
            {"volatility": -0.2},
            {"time_to_expiry": 0.0},
            {"steps": 0},
            {"steps": 2.5},
            {"steps": True},
        ]

        for inputs in cases:
            with self.subTest(inputs=inputs):
                with self.assertRaises(ValueError):
                    make_path(**inputs)

    def test_price_underflow_raises_overflow_error(self):
        # This extreme decline rounds the simulated price to zero.
        with self.assertRaises(OverflowError):
            make_path(drift=-1000.0, volatility=0.0, steps=1)