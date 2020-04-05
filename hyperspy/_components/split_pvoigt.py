# -*- coding: utf-8 -*-
# Copyright 2007-2016 The HyperSpy developers
#
# This file is part of  HyperSpy.
#
#  HyperSpy is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
#  HyperSpy is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with  HyperSpy.  If not, see <http://www.gnu.org/licenses/>.

import numpy as np

from hyperspy.component import Component
from hyperspy._components.gaussian import _estimate_gaussian_parameters
sqrt2pi = np.sqrt(2*np.pi)


class SplitVoigt(Component):

    r"""Split pseudo - voigt

    .. math::

        pV(x,centre,\sigma) = (1 - \eta) G(x,centre,\sigma)
        + \eta L(x,centre,\sigma)

        f(x) =
        \begin{cases}
        pV(x,centre,\sigma_{1}) & x \leq centre\\
        pV(x,centre,\sigma_{2}) & x > centre\\
        \end{cases}

    ================ ===========
    Variable          Parameter
    ================ ===========
    :math:`A`         A
    :math:`\eta`      fraction
    :math:`\sigma_1` sigma1
    :math:`\sigma_2` sigma2
    :math:`centre`    centre
    ================ ===========

    Notes
    -----
    A voigt function in which the upstream and downstream variance or
    sigma is allowed to vary to create an asymmetric profile

    In this case the voigt is a pseudo voigt- consisting of a
    mixed gaussian and lorentzian sum


    """

    def __init__(self, A=1., sigma1=1.,sigma2=1.0, fraction=0.0,centre=0.):
        Component.__init__(self, ('A', 'sigma1','sigma2', 'centre','fraction'))
        self.A.value = A
        self.sigma1.value = sigma1
        self.sigma2.value = sigma2
        self.centre.value = centre
        self.fraction.value = fraction


        # Boundaries
        self.A.bmin = 1.0e-8
        self.A.bmax = 1e8
        self.sigma2.bmin = 1.0e-8
        self.sigma2.bmax = 50.0
        self.sigma1.bmin = 1.0e-8
        self.sigma1.bmax = 50.0
        self.fraction.bmin = 1.0e-8
        self.fraction.bmax = 1.0
        self.isbackground = False
        self.convolved = True

    def function(self,x):
        """Split pseudo voigt - a linear combination  of gaussian and lorentzian

        Parameters
        ----------
        x : array
            independent variable
        A : float
            area of pvoigt peak
        center : float
            center position
        sigma1 : float
            standard deviation <= center position
        sigma2 : float
            standard deviation > center position
        fraction : float
            weight for lorentzian peak in the linear combination,
            and (1-fraction) is the weight for gaussian peak.
        """
        area      = self.A.value
        sigma1    = self.sigma1.value
        sigma2    = self.sigma2.value
        centre    = self.centre.value
        fraction  = self.fraction.value

        arg = (x-centre)
        lor1 = (area / (1.0 + ((1.0 * arg) / sigma1) ** 2)) \
            / (0.5*np.pi * (sigma1+sigma2))
        lor2 = (area / (1.0 + ((1.0 * arg) / sigma2) ** 2)) \
            / (0.5*np.pi * (sigma1+sigma2))

        prefactor = area / (sqrt2pi * 0.5*(sigma1+sigma2))
        gauss1 = prefactor*np.exp(-0.5 *arg*arg/(sigma1*sigma1))
        gauss2 = prefactor*np.exp(-0.5 *arg*arg/(sigma2*sigma2))

        p1 = (1.0-fraction)*gauss1 + fraction*lor1
        p2 = (1.0-fraction)*gauss2 + fraction*lor2
        return np.where(x<=centre,p1,p2)



    def estimate_parameters(self, signal, x1, x2, only_current=False):
        """Estimate the split voigt function by calculating the
           momenta the gaussian.

        Parameters
        ----------
        signal : Signal1D instance
        x1 : float
            Defines the left limit of the spectral range to use for the
            estimation.
        x2 : float
            Defines the right limit of the spectral range to use for the
            estimation.

        only_current : bool
            If False estimates the parameters for the full dataset.

        Returns
        -------
        bool

        Notes
        -----
        Adapted from http://www.scipy.org/Cookbook/FittingData

        Examples
        --------

        >>> g = hs.model.components1D.Gaussian()
        >>> x = np.arange(-10,10, 0.01)
        >>> data = np.zeros((32,32,2000))
        >>> data[:] = g.function(x).reshape((1,1,2000))
        >>> s = hs.signals.Signal1D({'data' : data})
        >>> s.axes_manager.axes[-1].offset = -10
        >>> s.axes_manager.axes[-1].scale = 0.01
        >>> g.estimate_parameters(s, -10,10, False)

        """
        super(SplitVoigt, self)._estimate_parameters(signal)
        axis = signal.axes_manager.signal_axes[0]
        centre, height, sigma = _estimate_gaussian_parameters(signal, x1, x2,
                                                              only_current)

        if only_current is True:
            self.centre.value = centre
            self.sigma1.value = sigma
            self.sigma2.value = sigma
            self.A.value = height * sigma * sqrt2pi
            if self.binned:
                self.A.value /= axis.scale
            return True
        else:
            if self.A.map is None:
                self._create_arrays()
            self.A.map['values'][:] = height * sigma * sqrt2pi
            if self.binned:
                self.A.map['values'][:] /= axis.scale
            self.A.map['is_set'][:] = True
            self.sigma1.map['values'][:] = sigma
            self.sigma1.map['is_set'][:] = True
            self.sigma2.map['values'][:] = sigma
            self.sigma2.map['is_set'][:] = True
            self.centre.map['values'][:] = centre
            self.centre.map['is_set'][:] = True
            self.fetch_stored_values()
            return True

    @property
    def height(self):
        return self.A.value / (self.sigma.value * sqrt2pi)

    @height.setter
    def height(self, value):
        self.A.value = value * self.sigma.value * sqrt2pi
