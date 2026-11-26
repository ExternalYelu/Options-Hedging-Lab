"""Tests for European option prices, Greeks, and expiration payoffs."""

import unittest
from math import exp

from OptionsHedgingLab.pricing import black_scholes, call_payoff, put_payoff


def quote(option_type, *, stock_price=100.0, time_to_expiry=1.0, volatility=0.20):
    """Price an option with a $100 strike and a 5% annual rate."""
    return black_scholes(
        option_type,
        stock_price=stock_price,
        strike=100.0,
        time_to_expiry=time_to_expiry,
        rate=0.05,
        volatility=volatility,
    )


class TestPricing(unittest.TestCase):
    def test_gamma_matches_change_in_delta(self):
        # A two-cent interval centered on $100 gives a local slope.
        bump = 0.01
        for kind in ("call", "put"):
            with self.subTest(kind=kind):
                delta_up = quote(kind, stock_price=100.0 + bump).delta
                delta_down = quote(kind, stock_price=100.0 - bump).delta
                estimated_gamma = (delta_up - delta_down) / (2 * bump)
                self.assertAlmostEqual(quote(kind).gamma, estimated_gamma, delta=1e-7)

    def test_reference_prices(self):
        self.assertAlmostEqual(quote("call").price, 10.45058357, places=7)
        self.assertAlmostEqual(quote("put").price, 5.57352602, places=7)

    def test_payoffs_at_expiration(self):
        # Each row is (final stock price, expected call payoff, expected put payoff).
        cases = [(0, 0, 100), (95, 0, 5), (100, 0, 0), (105, 5, 0)]
        for stock_price, expected_call, expected_put in cases:
            with self.subTest(stock_price=stock_price):
                self.assertEqual(call_payoff(stock_price, 100), expected_call)
                self.assertEqual(put_payoff(stock_price, 100), expected_put)

    def test_put_call_parity(self):
        # For this stock, call price - put price = stock price - discounted strike.
        discounted_strike = 100.0 * exp(-0.05 * 1.0)
        for spot in (85.0, 100.0, 115.0):
            with self.subTest(spot=spot):
                call = quote("call", stock_price=spot)
                put = quote("put", stock_price=spot)
                self.assertAlmostEqual(call.price - put.price, spot - discounted_strike)

    def test_delta_matches_change_in_price(self):
        bump = 0.01
        for kind in ("call", "put"):
            with self.subTest(kind=kind):
                price_up = quote(kind, stock_price=100.0 + bump).price
                price_down = quote(kind, stock_price=100.0 - bump).price
                estimated_delta = (price_up - price_down) / (2 * bump)
                self.assertAlmostEqual(quote(kind).delta, estimated_delta, delta=1e-7)

    def test_vega_matches_change_in_price(self):
        bump = 0.0001
        for kind in ("call", "put"):
            with self.subTest(kind=kind):
                price_up = quote(kind, volatility=0.20 + bump).price
                price_down = quote(kind, volatility=0.20 - bump).price
                estimated_vega = (price_up - price_down) / (2 * bump)
                self.assertAlmostEqual(quote(kind).vega, estimated_vega, delta=1e-5)

    def test_theta_matches_passage_of_time(self):
        bump = 0.0001  # years
        for kind in ("call", "put"):
            with self.subTest(kind=kind):
                # Later in calendar time means less time remaining until expiry.
                price_later = quote(kind, time_to_expiry=1.0 - bump).price
                price_earlier = quote(kind, time_to_expiry=1.0 + bump).price
                estimated_theta = (price_later - price_earlier) / (2 * bump)
                self.assertAlmostEqual(quote(kind).theta, estimated_theta, delta=1e-6)

    def test_invalid_pricing_inputs_raise_value_error(self):
        cases = [
            {"option_type": "invalid"},
            {"option_type": "call", "stock_price": 0.0},
            {"option_type": "put", "time_to_expiry": 0.0},
            {"option_type": "call", "volatility": -0.20},
            {"option_type": "put", "volatility": float("nan")},
        ]
        for inputs in cases:
            with self.subTest(inputs=inputs):
                with self.assertRaises(ValueError):
                    quote(**inputs)