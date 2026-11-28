"""Simulate stock-price paths for the hedging experiments."""

from math import exp, isfinite, sqrt
from random import Random


def simulate_gbm_path(
    *,
    stock_price: float,
    drift: float,
    volatility: float,
    time_to_expiry: float,
    steps: int,
    seed: int,
) -> list[tuple[float, float]]:


    """Generate one stock-price path using geometric Brownian motion.

    drift and volatility are annualized decimals. time_to_expiry is in years.
    steps is the number of intervals between the initial price and expiry.

    Return (elapsed_years, price) pairs, including the start and end points.
    Reuse the same inputs and seed to reproduce the path.
    """

    if not isfinite(stock_price) or stock_price <=0:
        raise ValueError("stock price must be finite and postitive")
    if not isfinite(drift):
        raise ValueError("drift must be finite")
    if not isfinite(volatility) or volatility < 0:
        raise ValueError("volatility must be finite and nonnegative")
    if not isfinite(time_to_expiry) or time_to_expiry <= 0:
        raise ValueError("time_to_expiry must be finite and positive")
    if isinstance(steps, bool) or not isinstance(steps, int) or steps < 1:
        raise ValueError("steps must be a positive integer")


    rng = Random(seed)
    dt = time_to_expiry / steps

    #under GBM, each steps log return has this mean and standrad deviation
    log_return_mean = (drift - 0.5 * volatility**2) * dt
    log_return_std = volatility * sqrt(dt)

    price = stock_price
    path = [(0.0, price)]

    for step in range(1, steps + 1):
        log_return = rng.gauss(log_return_mean, log_return_std)
        price *= exp(log_return)
        if not isfinite(price or price <= 0):
            raise OverflowError("Simulated price is outside the positive float range")

        elapsed_years = time_to_expiry * (step / steps)
        path.append((elapsed_years, price))
    return path
