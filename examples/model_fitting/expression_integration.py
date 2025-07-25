"""
Expression Component Integration
================================

Demonstrate definite and improper integration capabilities of Expression components.

This example shows how to use the symbolic integration features of Expression 
components for analytical computation of integrals, including improper integration
with infinite bounds.

.. note::
   This example requires the latest version of HyperSpy with improper integration 
   support. If you're running from source, you may need to use:
   ``PYTHONPATH=/path/to/hyperspy python examples/model_fitting/expression_integration.py``
"""

import numpy as np
import hyperspy.api as hs

#%%
# Create a polynomial Expression component
# =======================================

# Define a quadratic function: f(x) = x^2 + 2x + 1
poly = hs.model.components1D.Expression(
    expression="a * x**2 + b * x + c",
    name="Quadratic",
    a=1.0,  # Set parameter values during creation
    b=2.0,
    c=1.0,
    compute_integrals=True  # Enable symbolic integration
)

print("Polynomial function: f(x) = x² + 2x + 1")

#%%
# Definite Integration
# ====================

# Compute definite integral from 0 to 3
definite_result = poly.integrate((0, 3), variable='x', method='symbolic')
print(f"Definite integral from 0 to 3: {definite_result}")

# Expected: [x³/3 + x² + x] from 0 to 3 = 9 + 9 + 3 = 21
expected_definite = (3**3)/3 + 3**2 + 3
print(f"Expected result: {expected_definite}")

#%%
# Improper Integration (New Feature)
# ====================================

# Create exponential decay function for improper integration
exp_decay = hs.model.components1D.Expression(
    expression="a * exp(-b * x)",
    name="ExponentialDecay",
    a=1.0,  # Set parameter values during creation
    b=1.0,
    compute_integrals=True
)

print("\nExponential decay function: f(x) = e^(-x)")

# Improper integration from 0 to infinity
# Note: symbolic integration doesn't support infinite bounds, use numerical
improper_result = exp_decay.integrate((0, np.inf), method='numerical')
print(f"Improper integral from 0 to ∞: {improper_result:.6f}")

# Expected result: ∫₀^∞ e^(-x) dx = 1
print(f"Expected result: 1.0")
print(f"Match: {np.isclose(improper_result, 1.0, rtol=1e-6)}")

# Show convergence by comparing finite bounds
print("\nConvergence analysis:")
finite_bounds = [5, 10, 20, 50]
for bound in finite_bounds:
    finite_result = exp_decay.integrate((0, bound), method='numerical')
    error = abs(finite_result - improper_result)
    print(f"Finite bound [0, {bound:2d}]: {finite_result:.6f}, Error: {error:.2e}")

#%%
# Gaussian Improper Integration
# =============================

# Create Gaussian function for bilateral improper integration
gaussian = hs.model.components1D.Expression(
    expression="a * exp(-(x - mu)**2 / (2 * sigma**2))",
    name="Gaussian",
    a=1.0,  # Set parameter values during creation
    mu=0.0,
    sigma=1.0,
    compute_integrals=True
)

print(f"\nGaussian function: f(x) = e^(-x²/2)")

# Improper integration from -∞ to +∞
gaussian_result = gaussian.integrate((-np.inf, np.inf), method='numerical')
print(f"Gaussian integral (-∞ to +∞): {gaussian_result:.6f}")

# Expected result: ∫₋∞^∞ e^(-x²/2) dx = √(2π) ≈ 2.507
expected_gaussian = np.sqrt(2 * np.pi)
print(f"Expected result (√(2π)): {expected_gaussian:.6f}")
print(f"Match: {np.isclose(gaussian_result, expected_gaussian, rtol=1e-4)}")

#%%
# Parameter Substitution with Improper Integration
# ================================================

print("\nImproper integration with parameter substitution:")

# Original parameters: a=1, b=1, integral should be a/b = 1
original_improper = exp_decay.integrate((0, np.inf), method='numerical')
print(f"Original (a=1, b=1): ∫₀^∞ = {original_improper:.6f}")

# Custom parameters: a=2, b=0.5, integral should be a/b = 4
custom_improper = exp_decay.integrate((0, np.inf), method='numerical', 
                                     parameters_values=[2.0, 0.5])
print(f"Custom (a=2, b=0.5): ∫₀^∞ = {custom_improper:.6f}")
print(f"Expected (a/b = 2/0.5): {2.0/0.5:.6f}")

#%%
# Error Handling for Improper Integration  
# ========================================

print("\nDemonstrating error handling:")

# Try symbolic method with infinite bounds (should fail)
try:
    symbolic_improper = exp_decay.integrate((0, np.inf), method='symbolic')
    print(f"Symbolic with infinite bounds: {symbolic_improper}")
except NotImplementedError as e:
    print(f"Expected error - Symbolic with ∞: {str(e)[:60]}...")

# Auto method should fall back to numerical for infinite bounds
auto_improper = exp_decay.integrate((0, np.inf), method='auto')
print(f"Auto method with infinite bounds: {auto_improper:.6f}")

#%%
# Rational Function Example
# =========================

# Create rational function that converges over infinite domain
rational = hs.model.components1D.Expression(
    expression="1 / (1 + x**2)",
    name="RationalFunction", 
    compute_integrals=True
)

print(f"\nRational function: f(x) = 1/(1 + x²)")

# This integral converges to π
rational_result = rational.integrate((-np.inf, np.inf), method='numerical')
print(f"Rational integral (-∞ to +∞): {rational_result:.6f}")
print(f"Expected result (π): {np.pi:.6f}")
print(f"Match: {np.isclose(rational_result, np.pi, rtol=1e-4)}")

print("\n✓ All improper integration examples completed successfully!")
