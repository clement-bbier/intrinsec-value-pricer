#!/usr/bin/env python3
"""Test script pour vérifier les imports."""

try:
    from app.ui.result_tabs.optional import peer_multiples
    print("OK - Peer multiples import")
except Exception as e:
    print(f"ERROR - Peer multiples import: {e}")

try:
    from core.valuation.strategies import monte_carlo
    print("OK - Monte Carlo import")
except Exception as e:
    print(f"ERROR - Monte Carlo import: {e}")

try:
    from app.ui.result_tabs.optional import scenario_analysis
    print("OK - Scenario analysis import")
except Exception as e:
    print(f"ERROR - Scenario analysis import: {e}")

try:
    from app.ui.result_tabs.optional import historical_backtest
    print("OK - Historical backtest import")
except Exception as e:
    print(f"ERROR - Historical backtest import: {e}")

try:
    from app.ui.result_tabs.optional import monte_carlo_distribution
    print("OK - Monte Carlo distribution import")
except Exception as e:
    print(f"ERROR - Monte Carlo distribution import: {e}")

print("Test termine.")