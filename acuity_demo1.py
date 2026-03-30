import numpy as np

# 1. Base Case Assumptions (The "Deterministic" View)
iterations = 10000
hold_period = 5.0
initial_ebitda = 10.0# $10M
entry_multiple = 10.0
purchase_price = initial_ebitda * entry_multiple # $100M
initial_debt = 50.0# $50M
initial_equity = purchase_price - initial_debt# $50M

# 2. Injecting Volatility (The "Acuity" Probabilistic Engine)
# In production, the 'scale' (StdDev) comes from Polymarket or Historical Variance
np.random.seed(42)

# Simulate Exit Multiple (Base: 10x, StdDev: 1.5x)
exit_multiples = np.random.normal(loc=10.0, scale=1.5, size=iterations)

# Simulate Average Interest Rate (Base: 5%, StdDev: 1.5%)
avg_interest_rates = np.random.normal(loc=0.05, scale=0.015, size=iterations)

# Simulate Year 5 EBITDA (Base: $15M, StdDev: $2M)
exit_ebitdas = np.random.normal(loc=15.0, scale=2.0, size=iterations)

# 3. Running the Vectorized LBO Math
# Simplified Cash Flow: Assume 50% of EBITDA goes to debt paydown
cumulative_fcf_for_debt = ((initial_ebitda + exit_ebitdas) / 2) * hold_period * 0.5

# Calculate ending debt (Ensuring debt doesn't go below 0)
ending_debt = np.maximum(0, initial_debt - cumulative_fcf_for_debt)

# 4. Calculating Exit Outputs & Returns
exit_enterprise_values = exit_ebitdas * exit_multiples
exit_equity_values = exit_enterprise_values - ending_debt

# Cap downside at total loss (Equity cannot go below $0 in standard PE)
exit_equity_values = np.maximum(0, exit_equity_values)

# Calculate IRR for all 10,000 iterations
# If exit equity is 0, the investment is a total loss (IRR = -100%)
irrs = np.where(exit_equity_values > 0, 
  (exit_equity_values / initial_equity) ** (1 / hold_period) - 1,  -1.0)

# 5. Acuity Risk Analytics
prob_irr_less_than_10 = np.mean(irrs < 0.10) * 100
capital_loss_prob = np.mean(irrs < 0.0) * 100
mean_irr = np.mean(irrs) * 100

# Quick deterministic calculation for comparison
base_ending_debt = max(0, 50.0 - (((10.0 + 15.0) / 2) * 5 * 0.5))
base_exit_equity = (15.0 * 10.0) - base_ending_debt
base_case_irr = (base_exit_equity / initial_equity) ** (1/5) - 1

print("--- ACUITY MVP: LBO RISK ENGINE ---")
print(f"Base Case IRR (Deterministic):{base_case_irr * 100:.1f}%")
print(f"Mean Probabilistic IRR:{mean_irr:.1f}%")
print(f"Probability IRR < 10%:{prob_irr_less_than_10:.1f}%")
print(f"Probability of Capital Loss: {capital_loss_prob:.1f}%")