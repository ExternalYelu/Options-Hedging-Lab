# Options Hedging Lab

**When does using gamma to decide when to rebalance an options hedge reduce risk more effectively than rebalancing on a fixed schedule, after transaction costs?**

Suppose I sell a call option and buy enough shares to hedge it. By tomorrow morning the stock may have moved, the option will be a day closer to expiration, and the number of shares I need may have changed. I can adjust the hedge every morning. I can wait until the share position is a certain distance from its target. Or I can use gamma to estimate how much the target has moved since my last trade. Each choice leaves me with a different trading bill and a different amount of cash when the option comes due.

I’m building a Python simulator for a Michigan MFAMS research project to compare those three choices. The comparison I care about is **how closely each hedge covers the option payoff at a similar trading cost**. The experiment will use simulated prices so that every rule faces exactly the same quiet stretches, sharp moves, and expiration prices.

**The project is at the research-design stage.** The December 21 target is a working simulation and a report of the results.

## What gamma tells the hedger

**Delta** gives the share position that offsets the option seller’s immediate exposure to a small stock-price move. A call with a delta of 0.50 has roughly the same local price sensitivity as half a share. Someone who sold a call covering 100 shares would therefore buy about 50 shares to hedge it. **Gamma** estimates how much delta changes per dollar of movement in the stock. Gamma can be particularly high when the stock is near the strike and expiration is close. [Options Industry Council’s explanation of gamma](https://www.optionseducation.org/advancedconcepts/gamma)

For example, suppose the stock trades at $100 and the call has a delta of 0.50 and a gamma of 0.04 per dollar. At the last adjustment, the seller bought 50 shares. The stock then rises to $102.

| What the seller knows | What it implies for the hedge |
| --- | --- |
| The stock moved $2 since the last trade. | The old gamma estimates a delta increase of 0.04 × 2 = 0.08, or about eight additional shares for the contract. |
| The seller’s threshold is six shares. | The gamma rule calls for a trade at this observation. A scheduled rule can wait until its next trading time. |
| Suppose the freshly calculated delta is 0.57. | The direct delta rule sees a seven-share gap and also trades. Both rules buy seven shares to reach the current target. |

The distinction is in **when to trade**. Once a rule calls for a trade, the engine recalculates delta to size the order. The example also shows why the comparison could go either way. Gamma measures a local slope. It can change over a large move, and the passage of time can change delta even when the stock finishes the day where it started. The direct delta rule gives me a way to measure how much those differences matter.

## The three rules

Each rule starts with the same option premium and the same opening hedge. Each observes the stock on the same grid of times and can act only on information available at that point. The thresholds below are measured in shares per option on one share of stock, so the rules can be compared across contract sizes.

| Rule | Decision at each observation | What I’ll vary |
| --- | --- | --- |
| Fixed schedule | Rebalance to current delta every *k* observations. | The interval between adjustments. |
| Delta threshold | Recalculate delta. Trade when the absolute gap between current delta and shares held reaches the threshold. | The size of the permitted share gap. |
| Gamma trigger | Multiply gamma recorded at the last rebalance by the stock-price change since that rebalance. Trade when the magnitude of that estimate reaches the threshold. Refresh the reference price and gamma after the trade. | The size of the estimated share gap that triggers an order. |

The last-rebalance convention matters. Several small moves in the same direction can add up to a trade even if no individual move would trigger one. Conversely, the stock can move away and return between observations. All three rules face that same limit on what they can observe.

My working hypothesis is that the gamma trigger can save trades during quiet stretches and use that budget to adjust sooner during larger moves. The direct delta threshold is the harder benchmark. On small moves over short intervals, the gamma estimate and the measured delta change should be close. I’d expect the most informative paths to be the ones where those two rules disagree about whether to trade.

## Following the money through one simulation

The baseline is a European option on a stock that pays no dividends. A European option settles at expiration. The simulator will use one share per option, allow fractional hedge positions, and express results in dollars per option. The 100-share example above is just a convenient way to picture the trades.

1. **Sell the option.** Receive the Black–Scholes premium in cash. Buy the initial delta shares for a call, or sell shares short for a put. Deduct the opening trading cost. The cash balance can be negative if the hedge requires borrowing.
2. **Carry the position.** Between observations, leave the share count alone and accrue interest on the cash balance. The baseline uses one constant rate for borrowing and lending.
3. **Process a trade.** If the rule triggers, move the share position to current delta. Buying shares spends cash, selling shares raises cash, and either side pays a cost proportional to the dollar value traded. At five basis points per side, for example, buying $1,000 of stock costs $0.50 in addition to the purchase price.
4. **Settle at expiration.** Close the stock position, charge the closing cost, and pay the option holder. A call pays the amount by which the final stock price exceeds the strike, floored at zero. A put pays the amount by which the strike exceeds the final stock price, also floored at zero.

**Terminal hedging error** is the cash left after that last step. If the liquidated hedge has $11.80 available and the option pays $12.00, the error is −$0.20. Positive error means a surplus. The ledger deducts every trading cost as it occurs, so the closing balance already includes those costs. A separate tally shows how much the rule spent to produce that outcome.

## How I’ll run the comparison

**Start with a market whose assumptions are known.** The first experiments will generate stock paths using geometric Brownian motion with constant volatility. The pricing model will use that same volatility, the same interest rate, and the same expiry as the simulation. The baseline will use risk-neutral drift equal to the interest rate. This gives me a controlled setting in which discrete trading and explicit costs can explain differences between rules. Black and Scholes provide the continuous-time pricing benchmark. [Black and Scholes, 1973](https://doi.org/10.1086/260062)

**Vary the conditions that could change the answer.**

| Experiment | Question it answers |
| --- | --- |
| Change volatility while holding the initial stock price and strike fixed. | As stock moves grow larger, how closely does gamma from the last trade track the actual change in delta? |
| Change the time to expiration, including short-dated options near the strike. | Can the trigger keep up when the target share position changes sharply over a small price range? |
| Move the per-trade cost from zero to progressively higher rates. | How much of the benefit of frequent adjustments survives the trading bill? |
| Introduce sudden price jumps as a later stress test. | How much error accumulates across a jump before any rule has an opportunity to react? |

**Select settings before evaluating them.** For each market scenario, I’ll test several fixed intervals and trigger thresholds on development paths. I’ll use those runs to identify settings with comparable average dollar costs, then freeze the settings and evaluate them on a fresh set of random seeds. I’ll report the costs actually realized on those held-out paths. If two rules end up spending materially different amounts, their results belong at different points on the cost plot.

**Compare like with like.** On each held-out path, all three rules see the same prices in the same order. To estimate uncertainty, I’ll resample whole paths, keeping the three outcomes from each path together, and recompute the difference in performance. That preserves the fact that a difficult expiration for one rule may also be difficult for the others.

## What would count as a result?

The main figure will plot **average dollars spent trading** on the horizontal axis and **root mean squared terminal hedging error** on the vertical axis. Each point will represent a rule at one interval or threshold. Squaring each path’s error before averaging gives large misses more weight, and taking the square root puts the result back in dollars. At a comparable cost, a lower point means the funded hedge tracked its liability more closely. The transaction-cost literature gives a reason to examine both axes together. [Leland, 1985](https://doi.org/10.1111/j.1540-6261.1985.tb02383.x)

I’ll also report **average signed error**, which shows a tendency to finish short or with cash left over, and the **5th percentile of signed error**, which shows the outcome at the boundary of the worst 5% of paths. Trade count and total dollar volume will help explain the bill. Two rules can trade equally often and pay different amounts if one places larger orders.

If gamma beats the fixed schedule at similar cost but ties the direct delta threshold, the evidence would favor waiting for hedge exposure to change. It would give little reason to prefer the gamma estimate over measuring the gap directly. If gamma performs well for longer-dated options and falls behind near expiration, that boundary is worth reporting. If the paired uncertainty intervals are too wide to distinguish the rules, that is the limit of the conclusion for that scenario. All of these conclusions would apply to the simulated market and cost assumptions under which they were measured.

## What I’ll build and how I’ll check it

| Component | Planned checks |
| --- | --- |
| **Python pricer** for European calls and puts, with delta, gamma, vega, and theta. Vega measures sensitivity to volatility and theta to the passage of time. | Compare analytical Greeks with finite differences from small changes in pricing inputs. Check call–put parity, expiry payoffs, and the sign and units of each Greek. Handle expiration separately, where the payoff has a corner at the strike. |
| **Stock-path generator** with configurable volatility, maturity, and seed. | Reproduce paths from a saved seed. Compare simulated log-return means and variances against the values implied by the baseline model. |
| **Hedge ledger and trading rules** sharing one cash and settlement convention. | Work through a short path by hand, including interest and the opening and closing costs. Confirm that two rules forced to trade at identical times produce identical holdings, cash, and terminal error. |
| **Experiment runner and report** that preserve scenario inputs, seeds, and policy settings alongside each result. | Repeat a run from its recorded settings. In the zero-cost baseline, check that frequent rebalancing reduces aggregate replication error as the observation grid becomes finer. Trace individual paths to explain exceptions and large losses. |

The December deliverable is the Python implementation, a worked path that a reader can audit trade by trade, and the held-out comparisons with uncertainty estimates. All prices will be generated by the simulator, so reproducing the research will require no paid options dataset. A C++ implementation is a possible follow-up if profiling identifies a slow component worth benchmarking against Python.
