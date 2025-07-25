Added :meth:`~.component.Component.integrate` and 
:meth:`~.component.Component.integrate_nd` methods for numerical 
integration of components, and enhanced :class:`~._components.expression.Expression` 
with both symbolic and numerical integration support.

**Key features:**

* **Component integration**: Numerical integration for all component types using scipy.integrate.quad
* **Expression symbolic integration**: Exact analytical results for expressions with known antiderivatives  
* **Improper integration**: Support for integration over infinite bounds (e.g., ``(-np.inf, np.inf)``, ``(0, np.inf)``)
* **Variable limits**: Navigation-aware integration across multiple parameter sets
* **Parameter substitution**: Runtime parameter substitution for flexible analysis

See :ref:`expression_component-label` in the user guide for examples and usage details.
