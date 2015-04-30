# Copyright 2014, 2015 Holger Kohr, Jonas Adler
#
# This file is part of RL.
#
# RL is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# RL is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with RL.  If not, see <http://www.gnu.org/licenses/>.


from __future__ import unicode_literals, print_function, division
from __future__ import absolute_import
from future.builtins import zip

# import numpy as np
# from scipy.lib.blas import get_blas_funcs

# from RL.utility.utility import allEqual
from RL.space.space import HilbertSpace
from RL.utility.utility import errfmt

from future import standard_library
standard_library.install_aliases()


class ProductSpace(HilbertSpace):
    """Product space (X1 x X2 x ... x Xn)
    """

    def __init__(self, *spaces):
        if len(spaces) == 0:
            raise TypeError("Empty product not allowed")
        if not all(spaces[0].field == y.field for y in spaces):
            raise TypeError("All spaces must have the same field")

        self.spaces = spaces
        self._dimension = len(self.spaces)
        self._field = spaces[0].field  # X_n has same field

    def zero(self):
        return self.makeVector(*[space.zero() for space in self.spaces])

    def empty(self):
        return self.makeVector(*[space.empty() for space in self.spaces])

    def innerImpl(self, x, y):
        return (sum(space.innerImpl(xp, yp)
                    for space, xp, yp in zip(self.spaces, x.parts, y.parts)))

    def linCombImpl(self, z, a, x, b, y):
        for space, zp, xp, yp in zip(self.spaces, z.parts, x.parts, y.parts):
            space.linCombImpl(zp, a, xp, b, yp)

    @property
    def field(self):
        return self._field

    @property
    def dimension(self):
        return self._dimension

    def equals(self, other):
        return (isinstance(other, ProductSpace) and
                all(x.equals(y) for x, y in zip(self.spaces, other.spaces)))

    def makeVector(self, *args):
        return ProductSpace.Vector(self, *args)

    def __getitem__(self, index):
        return self.spaces[index]

    def __len__(self):
        return self.dimension

    def __str__(self):
        return ('ProductSpace(' +
                ', '.join(str(space) for space in self.spaces) + ')')

    class Vector(HilbertSpace.Vector):
        def __init__(self, space, *args):
            HilbertSpace.Vector.__init__(self, space)

            if not isinstance(args[0], HilbertSpace.Vector):
                # Delegate constructors
                self.parts = (tuple(space.makeVector(arg)
                                    for arg, space in zip(args, space.spaces)))
            else:  # Construct from existing tuple
                if any(part.space != space
                       for part, space in zip(args, space.spaces)):
                    raise TypeError(errfmt('''
                    The spaces of all parts must correspond to this
                    space's parts'''))

                self.parts = args

        def __getitem__(self, index):
            return self.parts[index]

        def __str__(self):
            return (self.space.__str__() +
                    '::Vector(' + ', '.join(str(part) for part in self.parts) +
                    ')')

        def __repr__(self):
            return (self.space.__repr__() + '::Vector(' +
                    ', '.join(part.__repr__() for part in self.parts) + ')')


class PowerSpace(HilbertSpace):
    """Product space with the same underlying space (X x X x ... x X)
    """

    def __init__(self, underlying_space, dimension):
        if dimension <= 0:
            raise TypeError('Empty or negative product not allowed')

        self.underlying_space = underlying_space
        self._dimension = dimension

    def zero(self):
        return self.makeVector(*[self.underlying_space.zero()
                                 for _ in range(self.dimension)])

    def empty(self):
        return self.makeVector(*[self.underlying_space.empty()
                                 for _ in range(self.dimension)])

    def innerImpl(self, x, y):
        return sum(self.underlying_space.innerImpl(xp, yp)
                   for xp, yp in zip(x.parts, y.parts))

    def linCombImpl(self, z, a, x, b, y):
        for zp, xp, yp in zip(z.parts, x.parts, y.parts):
            self.underlying_space.linCombImpl(zp, a, xp, b, yp)

    @property
    def field(self):
        return self.underlying_space.field

    @property
    def dimension(self):
        return self._dimension

    def equals(self, other):
        return (isinstance(other, PowerSpace) and
                self.underlying_space.equals(other.underlying_space) and
                self.dimension == other.dimension)

    def makeVector(self, *args):
        return PowerSpace.Vector(self, *args)

    def __getitem__(self, index):
        if index < -self.dimension or index >= self.dimension:
            raise IndexError('Index out of range')
        return self.underlying_space

    def __len__(self):
        return self.dimension

    def __str__(self):
        return ('PowerSpace(' + str(self.underlying_space) + ', ' +
                str(self.dimension) + ')')

    class Vector(HilbertSpace.Vector):
        def __init__(self, space, *args):
            HilbertSpace.Vector.__init__(self, space)

            if not isinstance(args[0], HilbertSpace.Vector):
                # Delegate constructors
                self.parts = tuple(space.makeVector(arg)
                                   for arg, space in zip(args, space.spaces))
            else:  # Construct from existing tuple
                if len(args) != self.space.dimension:
                    raise TypeError('The dimension of the space is wrong')

                if any(part.space != self.space.underlying_space
                       for part in args):
                    raise TypeError(errfmt('''
                    The spaces of all parts must correspond to this space's
                    parts'''))

                self.parts = args

        def __getitem__(self, index):
            return self.parts[index]

        def __str__(self):
            return (self.space.__str__() + '::Vector(' +
                    ', '.join(str(part) for part in self.parts) + ')')

        def __repr__(self):
            return (self.space.__repr__() + '::Vector(' +
                    ', '.join(part.__repr__() for part in self.parts) + ')')
