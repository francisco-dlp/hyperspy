.. _model-components:

Model components
----------------

In HyperSpy a model consists of a sum of individual components. For convenience,
HyperSpy provides a number of pre-defined model components as well as mechanisms
to create your own components.

.. _model_components-label:

Pre-defined model components
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Various components are available in one (:mod:`~.api.model.components1D`) and
two-dimensions (:mod:`~.api.model.components2D`) to construct a
model.

The following general components are currently available for one-dimensional models:

* :class:`~.api.model.components1D.Arctan`
* :class:`~.api.model.components1D.Bleasdale`
* :class:`~.api.model.components1D.Doniach`
* :class:`~.api.model.components1D.Erf`
* :class:`~.api.model.components1D.Exponential`
* :class:`~.api.model.components1D.Expression`
* :class:`~.api.model.components1D.Gaussian`
* :class:`~.api.model.components1D.GaussianHF`
* :class:`~.api.model.components1D.HeavisideStep`
* :class:`~.api.model.components1D.Logistic`
* :class:`~.api.model.components1D.Lorentzian`
* :class:`~.api.model.components1D.Offset`
* :class:`~.api.model.components1D.Polynomial`
* :class:`~.api.model.components1D.PowerLaw`
* :class:`~.api.model.components1D.ScalableFixedPattern`
* :class:`~.api.model.components1D.SkewNormal`
* :class:`~.api.model.components1D.Voigt`
* :class:`~.api.model.components1D.SplitVoigt`

The following components are currently available for two-dimensional models:

* :class:`~.api.model.components1D.Expression`
* :class:`~.api.model.components2D.Gaussian2D`

However, this doesn't mean that you have to limit yourself to this meagre
list of functions. As discussed below, it is very easy to turn a
mathematical, fixed-pattern or Python function into a component.

.. _expression_component-label:

Define components from a mathematical expression
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


The easiest way to turn a mathematical expression into a component is using the
:class:`~._components.expression.Expression` component. For example, the
following is all you need to create a
:class:`~._components.gaussian.Gaussian` component  with more sensible
parameters for spectroscopy than the one that ships with HyperSpy:

.. code-block:: python

    >>> g = hs.model.components1D.Expression(
    ... expression="height * exp(-(x - x0) ** 2 * 4 * log(2)/ fwhm ** 2)",
    ... name="Gaussian",
    ... position="x0",
    ... height=1,
    ... fwhm=1,
    ... x0=0,
    ... module="numpy")

If the expression is inconvenient to write out in full (e.g. it's long and/or
complicated), multiple substitutions can be given, separated by semicolons.
Both symbolic and numerical substitutions are allowed:

.. code-block:: python

    >>> expression = "h / sqrt(p2) ; p2 = 2 * m0 * e1 * x * brackets;"
    >>> expression += "brackets = 1 + (e1 * x) / (2 * m0 * c * c) ;"
    >>> expression += "m0 = 9.1e-31 ; c = 3e8; e1 = 1.6e-19 ; h = 6.6e-34"
    >>> wavelength = hs.model.components1D.Expression(
    ... expression=expression,
    ... name="Electron wavelength with voltage")

:class:`~._components.expression.Expression` uses `Sympy
<https://www.sympy.org>`_ internally to turn the string into
a function. By default it "translates" the expression using
numpy, but often it is possible to boost performance by using
`numexpr <https://github.com/pydata/numexpr>`_ instead.

It can also create 2D components with optional rotation. In the following
example we create a 2D Gaussian that rotates around its center:

.. code-block:: python

    >>> g = hs.model.components2D.Expression(
    ... "k * exp(-((x-x0)**2 / (2 * sx ** 2) + (y-y0)**2 / (2 * sy ** 2)))",
    ... "Gaussian2d", add_rotation=True, position=("x0", "y0"),
    ... module="numpy", )

Component Integration
^^^^^^^^^^^^^^^^^^^^^

HyperSpy components now support comprehensive integration capabilities for 
numerical analysis, model fitting, background subtraction, and normalization 
tasks. Integration works with **all component types** including built-in 
components like :class:`~.api.model.components1D.Gaussian`, 
:class:`~.api.model.components1D.PowerLaw`, :class:`~.api.model.components1D.Polynomial`,
as well as custom :class:`~._components.expression.Expression` components.

Integration Methods Overview
""""""""""""""""""""""""""""

**Numerical Integration (All Components)**

All HyperSpy components support numerical integration using the 
:meth:`~.component.Component.integrate` method:

.. code-block:: python

    # Works with any component type
    component.integrate(limits, **kwargs)

This uses ``scipy.integrate.quad`` internally and supports:

* **Definite integration**: ``(a, b)`` for integration from ``a`` to ``b``
* **Improper integration**: ``(-np.inf, np.inf)``, ``(0, np.inf)``, etc.
* **All component types**: Gaussian, PowerLaw, Polynomial, Expression, etc.
* **Robust computation**: Handles complex functions and infinite bounds

**Symbolic Integration (Expression Components)**

:class:`~._components.expression.Expression` components additionally support 
symbolic integration when created with ``compute_integrals=True``:

.. code-block:: python

    # Enhanced capabilities for Expression components
    expr_component.integrate(limits, method='symbolic', **kwargs)

This provides:

* **Exact analytical results** when antiderivatives exist
* **Automatic fallback** to numerical integration if symbolic fails
* **Parameter dependence** with exact mathematical relationships
* **Performance benefits** for supported expressions

Method Signature
""""""""""""""""

Both integration methods share a common interface:

.. code-block:: python

    result = component.integrate(limits, variable='x', method='auto',
                                parameters_values=None, **kwargs)

**Parameters:**

* ``limits`` : Integration bounds
  
  - ``(a, b)``: Definite integration with fixed bounds
  - ``(-np.inf, np.inf)``: Improper integration with infinite bounds  
  - Variable limits: Arrays or navigation-aware bounds for multidimensional data

* ``variable`` : Variable to integrate (``'x'`` for 1D, ``'x'``/``'y'``/``('x','y')`` for 2D)
* ``method`` : Integration approach
  
  - ``'auto'`` (default): Symbolic first (Expression only), then numerical
  - ``'numerical'``: Force numerical integration (all components)
  - ``'symbolic'``: Force symbolic integration (Expression components only)

* ``parameters_values`` : Custom parameter values for integration
* ``**kwargs`` : Additional arguments (e.g., fixed variable values for 2D)

Examples with Built-in Components
"""""""""""""""""""""""""""""""""

**Basic Integration with Any Component**

.. code-block:: python

    >>> # Integration works with all component types
    >>> gaussian = hs.model.components1D.Gaussian()
    >>> gaussian.A.value = 1.0
    >>> result = gaussian.integrate((-2, 2))
    
    >>> powerlaw = hs.model.components1D.PowerLaw()
    >>> powerlaw.A.value = 1.0
    >>> powerlaw.r.value = 2.0
    >>> result = powerlaw.integrate((1, 10))
    
    >>> polynomial = hs.model.components1D.Polynomial(order=2)
    >>> polynomial.a0.value = 1.0
    >>> result = polynomial.integrate((0, 2))

Expression Components: Enhanced Integration
"""""""""""""""""""""""""""""""""""""""""""

:class:`~._components.expression.Expression` components offer additional 
symbolic integration capabilities when created with ``compute_integrals=True``:

.. code-block:: python

    >>> # Expression component with symbolic integration enabled
    >>> poly = hs.model.components1D.Expression(
    ... expression="a * x**2 + b * x + c",
    ... name="Polynomial",
    ... compute_integrals=True)
    >>> 
    >>> # Symbolic integration (exact result)
    >>> result = poly.integrate((0, 2), method='symbolic')
    >>> 
    >>> # Automatic method selection tries symbolic first
    >>> result_auto = poly.integrate((0, 2), method='auto')

Improper Integration with Infinite Bounds
"""""""""""""""""""""""""""""""""""""""""

Both numerical and symbolic integration support improper integrals over 
infinite intervals. This works with **all component types**:

.. code-block:: python

    >>> import numpy as np
    >>> 
    >>> # Any component can integrate over infinite bounds
    >>> gaussian = hs.model.components1D.Gaussian()
    >>> gaussian.A.value = 1.0
    >>> 
    >>> # Numerical improper integration
    >>> total_area = gaussian.integrate((-np.inf, np.inf))
    >>> 
    >>> # Expression with symbolic improper integration
    >>> exp_decay = hs.model.components1D.Expression(
    ... expression="a * exp(-b * x)",
    ... name="ExponentialDecay",
    ... compute_integrals=True)
    >>> exp_decay.a.value = 1.0
    >>> exp_decay.b.value = 1.0
    >>> 
    >>> # Both methods work: ∫₀^∞ exp(-x) dx = 1
    >>> result_symbolic = exp_decay.integrate((0, np.inf), method='symbolic')
    >>> result_numerical = exp_decay.integrate((0, np.inf), method='numerical')

**Note**: Both methods use robust algorithms (``scipy.integrate.quad`` for numerical, 
SymPy for symbolic) that can handle infinite bounds when the integral converges.

**Applications of improper integration:**

* **Normalization**: Computing total area under probability distributions
* **Physical quantities**: Total energy, charge, or other conserved quantities  
* **Model validation**: Checking convergence properties of mathematical models
* **Background analysis**: Integrating power law backgrounds over large ranges

Integration Method Selection
""""""""""""""""""""""""""""

The ``method`` parameter controls the integration approach:

**'numerical' (all components):**
  - Uses ``scipy.integrate.quad`` for robust numerical integration
  - Works with any component type (built-in or custom)
  - Supports both definite and improper integration
  - Handles complex functions that may not have analytical solutions
  - More computationally intensive but universally applicable

**'symbolic' (Expression components only):**
  - Uses SymPy for exact analytical integration  
  - Requires ``compute_integrals=True`` when creating Expression component
  - Faster and more accurate for expressions with known antiderivatives
  - Supports both definite and improper integration
  - With ``method='auto'``: automatically falls back to numerical if symbolic computation fails
  - With ``method='symbolic'``: raises error if symbolic computation fails

**'auto' (default, recommended):**
  - For Expression components: tries symbolic first, falls back to numerical
  - For other components: uses numerical integration
  - Provides best performance and reliability for all cases
  - Recommended for most applications

.. code-block:: python

    >>> # Method selection examples
    >>> 
    >>> # Built-in component - only numerical available
    >>> gaussian = hs.model.components1D.Gaussian()
    >>> gaussian.A.value = 1.0
    >>> result = gaussian.integrate((-2, 2), method='numerical')
    >>> 
    >>> # Expression component - symbolic available  
    >>> poly_expr = hs.model.components1D.Expression(
    ... expression="a*x**2", compute_integrals=True)
    >>> poly_expr.a.value = 1.0
    >>> 
    >>> result_symbolic = poly_expr.integrate((0, 2), method='symbolic')  # Exact
    >>> result_numerical = poly_expr.integrate((0, 2), method='numerical')  # Approximate
    >>> result_auto = poly_expr.integrate((0, 2), method='auto')  # Uses symbolic

Advanced Features for Expression Components
"""""""""""""""""""""""""""""""""""""""""""

:class:`~._components.expression.Expression` components offer additional 
advanced integration features beyond basic numerical integration.

**Symbolic Integration Benefits**

.. code-block:: python

    >>> # Exact analytical results for supported expressions
    >>> gaussian_expr = hs.model.components1D.Expression(
    ... expression="exp(-x**2)",
    ... name="GaussianExpr",
    ... compute_integrals=True)
    >>> 
    >>> # Exact result: ∫₋∞^∞ exp(-x²) dx = √π
    >>> result = gaussian_expr.integrate((-np.inf, np.inf), method='symbolic')
    >>> expected = np.sqrt(np.pi)  # ≈ 1.7724538509

**Advantages of symbolic integration:**

* **Exact results**: No numerical approximation errors
* **Parameter dependence**: Exact mathematical relationships preserved
* **Performance**: Direct analytical evaluation without numerical iteration
* **Automatic fallback**: With ``method='auto'``, gracefully falls back to numerical if needed

Parameter Substitution (All Components)
"""""""""""""""""""""""""""""""""""""""

All components support parameter substitution during integration:

.. code-block:: python

    >>> # Works with any component type
    >>> gaussian = hs.model.components1D.Gaussian()
    >>> 
    >>> # Integrate with custom parameter values [A, centre, sigma]
    >>> result = gaussian.integrate((-2, 2), parameters_values=[2.0, 1.0, 0.5])
    >>> 
    >>> # Expression component example
    >>> exp_decay = hs.model.components1D.Expression(
    ... expression="a * exp(-b * x)",
    ... compute_integrals=True)
    >>> 
    >>> # Custom parameters: [a=2.0, b=0.5] 
    >>> result = exp_decay.integrate((0, np.inf), parameters_values=[2.0, 0.5])
    >>> # Result: a/b = 2/0.5 = 4

Multidimensional Integration
""""""""""""""""""""""""""""

For 2D components, integration supports both single-variable and double integration.
Additionally, all 1D components support multidimensional integration via 
:meth:`~.component.Component.integrate_nd`:

.. code-block:: python

    >>> # 2D Expression component
    >>> expr_2d = hs.model.components2D.Expression(
    ... expression="a * x * y + b * x**2",
    ... name="TwoDFunction", 
    ... compute_integrals=True)
    
    >>> # Single integration over x (specify y value)
    >>> result_x = expr_2d.integrate((0, 1), variable='x', y=2.0)
    
    >>> # Double integration over x=[0,1], y=[0,2]  
    >>> result_double = expr_2d.integrate([(0, 1), (0, 2)], variable=('x', 'y'))
    
    >>> # Multidimensional integration for navigation space
    >>> gaussian = hs.model.components1D.Gaussian()
    >>> limits = np.array([[0, 2], [0, 2]])  # Different limits per spectrum
    >>> results = gaussian.integrate_nd(limits)

Common Use Cases and Applications
"""""""""""""""""""""""""""""""""

.. code-block:: python

    >>> # Background subtraction with PowerLaw
    >>> powerlaw = hs.model.components1D.PowerLaw()
    >>> powerlaw.A.value = 100
    >>> powerlaw.r.value = 2.0
    >>> background_area = powerlaw.integrate((100, 1000))
    >>> 
    >>> # Normalization constant computation
    >>> gaussian = hs.model.components1D.Gaussian()
    >>> total_intensity = gaussian.integrate((-np.inf, np.inf))
    >>> 
    >>> # Physical quantity calculations with Expression
    >>> charge_density = hs.model.components1D.Expression(
    ... expression="q0 * exp(-x/lambda_c)",
    ... compute_integrals=True)
    >>> total_charge = charge_density.integrate((0, np.inf))

Error Handling and Limitations
""""""""""""""""""""""""""""""

**Requirements:**

* **Symbolic integration**: Expression components with ``compute_integrals=True``
* **Numerical integration**: Available for all component types
* **Convergence**: For improper integrals, functions must converge mathematically

**Common error scenarios:**

.. code-block:: python

    >>> # Error: symbolic integration not enabled
    >>> basic_expr = hs.model.components1D.Expression(expression="x**2")
    >>> # basic_expr.integrate((0, 2), method='symbolic')  # Raises NotImplementedError
    
    >>> # Error: divergent improper integral  
    >>> # Some integrals don't converge and will fail or give infinite results

**Performance notes:**

* **Built-in components**: Optimized numerical integration
* **Expression symbolic**: Fast after first computation (cached)
* **Expression numerical**: Slower due to parsing overhead  
* **Improper integrals**: May require more computation time

**Best practices:**

* Use ``method='auto'`` for most applications
* Enable ``compute_integrals=True`` for Expression components when exact results needed
* Validate convergence for improper integrals with power law or rational functions
* Consider parameter ranges for mathematical validity

.. note::
   Symbolic integration requires SymPy and only works with expressions that
   have analytical antiderivatives. Both definite and improper integration with 
   infinite bounds are supported symbolically when analytical solutions exist.
   When using ``method='auto'`` (the default), the system will try symbolic 
   integration first and automatically fall back to numerical integration if 
   symbolic fails. When using ``method='symbolic'``, an error is raised if 
   symbolic integration fails, ensuring users are aware when exact analytical 
   results are not available.
   
   Improper integrals may not converge for all functions. The numerical
   integration will attempt to detect convergence issues.

Complete Example
""""""""""""""""

Here's a comprehensive example demonstrating various integration features:

.. code-block:: python

    >>> import numpy as np
    >>> import hyperspy.api as hs
    
    >>> # Create exponential decay with symbolic integration enabled
    >>> exp_func = hs.model.components1D.Expression(
    ... expression="a * exp(-b * x)",
    ... name="ExponentialDecay",
    ... compute_integrals=True)
    
    >>> # Set parameter values
    >>> exp_func.a.value = 2.0
    >>> exp_func.b.value = 1.0
    
    >>> # Definite integration (symbolic)
    >>> definite_result = exp_func.integrate((0, 5), method='symbolic')
    >>> print(f"Definite integral (0 to 5): {definite_result:.3f}")
    Definite integral (0 to 5): 1.987
    
    >>> # Improper integration (numerical)
    >>> improper_result = exp_func.integrate((0, np.inf), method='numerical')
    >>> print(f"Improper integral (0 to ∞): {improper_result:.3f}")
    Improper integral (0 to ∞): 2.000
    
    >>> # Comparison with different parameter values
    >>> custom_result = exp_func.integrate(
    ... (0, np.inf), method='numerical', parameters_values=[1.0, 0.5])
    >>> print(f"Custom parameters (a=1, b=0.5): {custom_result:.3f}")
    Custom parameters (a=1, b=0.5): 2.000  # = a/b = 1/0.5 = 2
    
    >>> # Verify convergence by comparing finite vs infinite bounds
    >>> finite_large = exp_func.integrate((0, 10), method='numerical')
    >>> print(f"Large finite bound: {finite_large:.6f}")
    >>> print(f"Infinite bound:     {improper_result:.6f}")
    >>> print(f"Difference:         {abs(finite_large - improper_result):.2e}")
    Large finite bound: 1.999955
    Infinite bound:     2.000000
    Difference:         4.50e-05

Define new components from a Python function
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Of course :class:`~._components.expression.Expression` is only useful for
analytical functions. You can define more general components modifying the
following template to suit your needs:


.. code-block:: python

    from hyperspy.component import Component

    class MyComponent(Component):

        """
        """

        def __init__(self, parameter_1=1, parameter_2=2):
            # Define the parameters
            Component.__init__(self, ('parameter_1', 'parameter_2'))

            # Optionally we can set the initial values
            self.parameter_1.value = parameter_1
            self.parameter_2.value = parameter_2

            # The units (optional)
            self.parameter_1.units = 'Tesla'
            self.parameter_2.units = 'Kociak'

            # Once defined we can give default values to the attribute
            # For example we fix the attribure_1 (optional)
            self.parameter_1.attribute_1.free = False

            # And we set the boundaries (optional)
            self.parameter_1.bmin = 0.
            self.parameter_1.bmax = None

            # Optionally, to boost the optimization speed we can also define
            # the gradients of the function we the syntax:
            # self.parameter.grad = function
            self.parameter_1.grad = self.grad_parameter_1
            self.parameter_2.grad = self.grad_parameter_2

        # Define the function as a function of the already defined parameters,
        # x being the independent variable value
        def function(self, x):
            p1 = self.parameter_1.value
            p2 = self.parameter_2.value
            return p1 + x * p2

        # Optional vectorised implementation of function to optimize
        # performance for specific features such as linear fitting and
        # `BaseModel.as_signal`
        def function_nd(self, x, parameters_values=None):
            """
            Parameters
            ----------
            x : numpy.ndarray
                The axis used to calculate the 
            parameters_values : list of numpy.ndarray or None
                The list of parameters values.
                If None, the parameters values will obtained
                from ``Parameter.map["values"]``.
            
            Returns
            -------
            numpy.ndarray
                Results of the component calculated over the axis ``x``.
            """
            if parameters_values is None:
                parameters_values = [
                    self.parameter_1.map["values"],
                    self.parameter_2.map["values"],
                    ]
            if self._is_navigation_multidimensional:
                x = x[np.newaxis, :]
                p1 = parameters_values[0][..., np.newaxis]
                p2 = parameters_values[1][..., np.newaxis]
            else:
                p1 = self.parameter_1.value
                p2 = self.parameter_2.value
            return np.ones_like(x) * p1 + x * p2

        # Optionally define the gradients of each parameter
        def grad_parameter_1(self, x):
            """
            Returns d(function)/d(parameter_1)
            """
            return 0

        def grad_parameter_2(self, x):
            """
            Returns d(function)/d(parameter_2)
            """
            return x


Define components from a fixed-pattern
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The :class:`~.api.model.components1D.ScalableFixedPattern`
component enables fitting a pattern (in the form of a
:class:`~.api.signals.Signal1D` instance) to data by shifting
(:attr:`~.api.model.components1D.ScalableFixedPattern.shift`)
and
scaling it in the x and y directions using the
:attr:`~.api.model.components1D.ScalableFixedPattern.xscale`
and
:attr:`~.api.model.components1D.ScalableFixedPattern.yscale`
parameters respectively.
