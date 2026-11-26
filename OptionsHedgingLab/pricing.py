"""European option payoffs and Black-Scholes pricing for a non-dividend-paying stock."""

from dataclasses import dataclass
from math import erfc, exp, isfinite, log, pi, sqrt
from typing import Literal

@dataclass(frozen = True)
class OptionQuote:
    """Price and sensities per share for the holder of the option"""

    price: float
    delta: float 
    gamma: float
    vega: float
    theta: float 


def _check_spot_and_strike(stock_price: float, strike: float) -> None:
    if not isfinite(stock_price) or stock_price < 0:
        raise ValueError("stock_price must be finite and non negative")
    if not isfinite(strike) or strike <= 0:
        raise ValueError("strike must be finite and positive")

def call_payoff(stock_price: float, strike: float) -> float:
    """Cash owed per shate to the call holder at expiration""" 
    _check_spot_and_strike(stock_price, strike)
    return max(stock_price - strike, 0.0)

def put_payoff(stock_price: float, strike: float) -> float:
    """Cash owed per share to the put holder at experiation"""
    _check_spot_and_strike(stock_price, strike)
    return max(strike - stock_price, 0.0)

def _normal_cdf(x: float) -> float:
    """Probability that a standard normal variable is at most x"""
    return 0.5 * erfc(-x / sqrt(2.0))

def black_scholes(
        option_type: Literal["call", "put"], 
        *, 
        stock_price: float, 
        strike: float, 
        time_to_expiry: float, 
        rate: float, 
        volatility: float, 
) -> OptionQuote:
    """Calculate price and Greeks before expiration.
    
    time_to_expiry is in years. The continuously compounded risk-free rate
    and annual volatility are decimals (0.05 for 5%, 0.20 for 20%).
    Vega is per 1.0 change in volatility. Theta is per year of elapsed time.
    At expiration, settle with call_payoff or put_payoff.
    """

    if option_type not in("call", "put"):
        raise ValueError("option_type must be 'call' or 'put'")

    _check_spot_and_strike(stock_price, strike)
    if stock_price == 0:
        raise ValueError("stock price must be positive for pre-expiry pricing")
    if not isfinite(time_to_expiry) or time_to_expiry <= 0:
        raise ValueError("time_to_expiry must be finite and positive")
    if not isfinite(volatility) or volatility <= 0:
        raise ValueError("volatility must be finite and positive")
    if not isfinite(rate):
        raise ValueError("rate must be finite")

    sqrt_time = sqrt(time_to_expiry)
    total_vol = volatility * sqrt_time
    discounted_strike = strike * exp(-rate * time_to_expiry)

    d1 = (log(stock_price / strike) + rate * time_to_expiry) / total_vol
    d1 += 0.5 * total_vol
    d2 = d1 - total_vol
    density = exp(-0.5 * d1**2) / sqrt(2.0 * pi)

    # These terms are shared by calls and puts with the same inputs.
    gamma = density / (stock_price * total_vol)
    vega = stock_price * density * sqrt_time
    time_decay = -stock_price * density * volatility / (2.0 * sqrt_time)

    if option_type == "call":
        delta = _normal_cdf(d1)
        exercise_probability = _normal_cdf(d2)
        price = stock_price * delta - discounted_strike * exercise_probability
        theta = time_decay - rate * discounted_strike * exercise_probability
    else:
        delta = -_normal_cdf(-d1)
        exercise_probability = _normal_cdf(-d2)
        price = discounted_strike * exercise_probability + stock_price * delta
        theta = time_decay + rate * discounted_strike * exercise_probability

    return OptionQuote(price=price, delta=delta, gamma=gamma, vega=vega, theta=theta)

    




