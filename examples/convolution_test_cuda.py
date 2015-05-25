# -*- coding: utf-8 -*-
"""
simple_test_astra.py -- a simple test script

Copyright 2014, 2015 Holger Kohr

This file is part of RL.

RL is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

RL is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with RL.  If not, see <http://www.gnu.org/licenses/>.
"""
from __future__ import division, print_function, unicode_literals, absolute_import
from future import standard_library

import RL.operator.operator as op
import RL.operator.solvers as solvers
import RL.space.set as sets
import RL.space.discretizations as dd
import RL.space.function as fs
import RL.space.cuda as cs
import RLcpp
from solverExamples import *

from RL.utility.testutils import Timer

import matplotlib.pyplot as plt
import numpy as np

standard_library.install_aliases()


class CudaConvolution(op.LinearOperator):
    """ Calculates the circular convolution of two CUDA vectors
    """

    def __init__(self, kernel, adjointkernel=None):
        if not isinstance(kernel.space, cs.CudaRN):
            raise TypeError("Kernel must be CudaRN vector")

        self.space = kernel.space
        self.kernel = kernel
        self.adjkernel = (adjointkernel if adjointkernel is not None
                          else self.space.element(kernel[::-1]))
        self.norm = float(sum(abs(self.kernel[:])))  # eval at host

    def _apply(self, rhs, out):
        RLcpp.cuda.conv(rhs.data, self.kernel.data, out.data)

    @property
    def adjoint(self):
        return CudaConvolution(self.adjkernel, self.kernel)

    def opNorm(self):  # An upper limit estimate of the operator norm
        return self.norm

    @property
    def domain(self):
        return self.space

    @property
    def range(self):
        return self.space



#Continuous definition of problem
continuousSpace = fs.L2(sets.Interval(0, 10))

#Complicated functions to check performance
continuousKernel = continuousSpace.element(lambda x: np.exp(x/2)*np.cos(x*1.172))
continuousRhs = continuousSpace.element(lambda x: x**2*np.sin(x)**2*(x > 5))

#Discretization
rn = cs.CudaRN(5000)
d = dd.makeUniformDiscretization(continuousSpace, rn)
kernel = d.element(continuousKernel)
rhs = d.element(continuousRhs)

#Create operator
conv = CudaConvolution(kernel)

#Dampening parameter for landweber
iterations = 100
omega = 1/conv.opNorm()**2

#Display partial
partial = solvers.ForEachPartial(lambda result: plt.plot(conv(result)[:]))

#Test CGN
plt.figure()
plt.plot(rhs)
solvers.conjugate_gradient(conv, d.zero(), rhs, iterations, partial)

#Landweber
plt.figure()
plt.plot(rhs)
solvers.landweber(conv, d.zero(), rhs, iterations, omega, partial)

#testTimingCG
with Timer("Optimized CG"):
    solvers.conjugate_gradient(conv, d.zero(), rhs, iterations)

with Timer("Base CG"):
    conjugate_gradient_base(conv, d.zero(), rhs, iterations)

#Landweber timing
with Timer("Optimized LW"):
    solvers.landweber(conv, d.zero(), rhs, iterations, omega)

with Timer("Basic LW"):
    landweberBase(conv, d.zero(), rhs, iterations, omega)

plt.show()