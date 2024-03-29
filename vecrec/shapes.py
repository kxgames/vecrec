#!/usr/bin/env python

from __future__ import division

import math
import random
import operator
import autoprop
from functools import wraps

# Utility Functions

def cast_anything_to_vector(input):
    """
    Convert the given input to a vector if possible, otherwise raise a 
    `VectorCastError`.  The following types can be converted to a vector:

    - `Vector` (in which case the input will be returned unchanged).
    - Iterable with exactly two elements.
    - Object with *x* and *y* attributes.
    """
    if isinstance(input, Vector):
        return input

    # If the input object is a container with two elements, use those elements 
    # to construct a vector.

    try: return Vector(*input)
    except: pass

    # If the input object has x and y attributes, use those attributes to 
    # construct a vector.
    
    try: return Vector(input.x, input.y)
    except: pass

    # If the function has returned by now, the input object could not be cast 
    # to a vector.  Throw an exception.

    raise VectorCastError(input)

def cast_anything_to_rectangle(input):
    """
    Convert the given input to a rectangle if possible, otherwise raise a 
    `RectCastError`.  The following types can be converted to a rectangle:

    - `Shape`, or anything implementing that interface (see 
      `cast_shape_to_rectangle()`).
    - `Vector`, or anything that can be coverted into a vector (see 
      `cast_anything_to_vector()`).  The resulting rectangle will have zero 
      area.
    """

    # If the input object implements the shape interface, use that information 
    # to directly return a rectangle object.
    
    try: return cast_shape_to_rectangle(input)
    except: pass

    # If the input object can be cast to a vector, try to represent that vector 
    # as a rectangle.  Such a rectangle is located where the vector points and 
    # has no area (i.e. width = height = 0).

    try: return Rect.from_vector(input)
    except: pass

    # If the function has returned by now, the input object could not be cast 
    # to a rectangle.  Throw an exception.

    raise RectCastError(input)

def cast_shape_to_rectangle(input):
    """
    Convert the given shape to a rectangle if possible, otherwise raise a 
    `RectCastError`.
    """
    if isinstance(input, Rect):
        return input

    # If the input object implements the shape interface (i.e. has bottom, left, 
    # width, and height attributes), use that information to construct a bona 
    # fide rectangle object.

    try: return Rect.from_shape(input)
    except: pass

    raise RectCastError(input)


def accept_anything_as_vector(function):
    """
    Method decorator that converts an argument to a vector.

    Examples::

        >>> import vecrec
        >>> class MyClass:
        ...     @vecrec.accept_anything_as_vector
        ...     def f(self, v):
        ...         return v
        ...
        >>> x = MyClass()
        >>> x.f(1, 2)
        Vector(1.000000, 2.000000)
        >>> x.f((1, 2))
        Vector(1.000000, 2.000000)

    """
    @wraps(function)
    def decorator(self, *input):
        if len(input) == 1: input = input[0]
        vector = cast_anything_to_vector(input)
        return function(self, vector)
    return decorator

def accept_anything_as_rectangle(function):
    """
    Method decorator that converts an argument to a rectangle.

    Example::

        >>> import vecrec
        >>> from collections import namedtuple
        >>> class MyClass:
        ...     @vecrec.accept_anything_as_rectangle
        ...     def f(self, r):
        ...         return r
        ... 
        >>> ShapeLike = namedtuple('_', 'bottom left width height')
        >>> shape = ShapeLike(1, 2, 3, 4)
        >>> x = MyClass()
        >>> x.f(shape)
        Rect(2.000000, 1.000000, 3.000000, 4.000000)
    """
    @wraps(function)
    def decorator(self, input):
        rect = cast_anything_to_rectangle(input)
        return function(self, rect)
    return decorator

def accept_shape_as_rectangle(function):
    """
    Method decorator that converts an argument to a rectangle.  

    Unlike `accept_anything_as_rectangle()`, only arguments that implement the 
    `Shape` interface are accepted.  Vector arguments will trigger a 
    `RectCastError`.
    """
    @wraps(function)
    def decorator(self, input):
        rect = cast_shape_to_rectangle(input)
        return function(self, rect)
    return decorator


def _overload_left_side(f, scalar_ok=False):
    """Helper function to make left-side operators."""

    def operator(self, other):
        try: x, y = cast_anything_to_vector(other)
        except: pass
        else: return Vector(f(self.x, x), f(self.y, y))

        # Zero is treated as a special case, because the built-in sum() 
        # function expects to be able to add zero to things.
        
        if (other == 0) or (scalar_ok):
            return Vector(f(self.x, other), f(self.y, other))
        else:
            raise VectorCastError(other)

    return operator

def _overload_right_side(f, scalar_ok=False):
    """Helper function to make right-side operators."""

    def operator(self, other):
        try: x, y = cast_anything_to_vector(other)
        except: pass
        else: return Vector(f(x, self.x), f(y, self.y))

        if (other == 0) or (scalar_ok):
            return Vector(f(other, self.x), f(other, self.y))
        else:
            raise VectorCastError(other)

    return operator

def _overload_in_place(f, scalar_ok=False):
    """Helper function to make in-place operators."""

    def operator(self, other):
        try: x, y = cast_anything_to_vector(other)
        except: pass
        else: self.x, self.y = f(self.x, x), f(self.y, y); return self

        if (other == 0) or (scalar_ok):
            self.x, self.y = f(self.x, other), f(self.y, other)
            return self
        else:
            raise VectorCastError(other)

    return operator

# Geometry Functions

phi = golden_ratio = 1/2 + math.sqrt(5) / 2

@autoprop
class Shape(object):
    """
    Provide an interface for custom shape classes to interact with the 
    rectangle class.

    For example, rectangles can be instantiated from shapes and can test for 
    collisions against shapes.  The interface is very simple, requiring only 
    four methods to be redefined.  These methods specify the outer dimensions, 
    i.e. the bounding rectangle, of the shape subclass.
    """

    def get_bottom(self):
        raise NotImplementedError

    def get_left(self):
        raise NotImplementedError

    def get_width(self):
        raise NotImplementedError

    def get_height(self):
        raise NotImplementedError


@autoprop
class Vector(object):
    """
    Represent a mutable two-dimensional vector.

    In particular, this class features a number of factory methods to create 
    vectors from various inputs and a number of overloaded operators to 
    facilitate vector arithmetic.
    """

    @staticmethod
    def null():
        """Return a null vector."""
        return Vector(0, 0)

    @staticmethod
    def random(magnitude=1):
        """Create a unit vector pointing in a random direction."""
        theta = random.uniform(0, 2 * math.pi)
        return magnitude * Vector(math.cos(theta), math.sin(theta))

    @staticmethod
    def from_radians(angle):
        """Create a unit vector that makes the given angle with the x-axis."""
        return Vector(math.cos(angle), math.sin(angle))

    @staticmethod
    def from_degrees(angle):
        """Create a unit vector that makes the given angle with the x-axis."""
        return Vector.from_radians(angle * math.pi / 180)

    @staticmethod
    def from_tuple(coordinates):
        """Create a vector from a two element tuple."""
        return Vector(*coordinates)

    @staticmethod
    def from_scalar(scalar):
        """Create a vector from a single scalar value."""
        return Vector(scalar, scalar)

    @staticmethod
    def from_rectangle(box):
        """Create a vector randomly within the given rectangle."""
        x = box.left + box.width * random.uniform(0, 1)
        y = box.bottom + box.height * random.uniform(0, 1)
        return Vector(x, y)

    @staticmethod
    def from_anything(input):
        return cast_anything_to_vector(input)


    def copy(self):
        """Return a copy of this vector."""
        from copy import deepcopy
        return deepcopy(self)

    @accept_anything_as_vector
    def assign(self, other):
        """Copy the given vector into this one."""
        self._x, self._y = other.tuple

    def normalize(self):
        """Set the magnitude of this vector to unity, in place."""
        try:
            self /= self.magnitude
        except ZeroDivisionError:
            raise NullVectorError

    def scale(self, magnitude):
        """Set the magnitude of this vector in place."""
        self.normalize()
        self *= magnitude

    def interpolate(self, target, extent):
        """Move this vector towards the given towards the target by the given 
        extent.  The extent should be between 0 and 1."""
        target = cast_anything_to_vector(target)
        self += extent * (target - self)

    @accept_anything_as_vector
    def project(self, axis):
        """Project this vector onto the given axis."""
        projection = self.get_projection(axis)
        self.assign(projection)

    @accept_anything_as_vector
    def dot_product(self, other):
        """Return the dot product of the given vectors."""
        return self.x * other.x + self.y * other.y

    @accept_anything_as_vector
    def perp_product(self, other):
        """Return the perp product of the given vectors.  The perp product is
        just a cross product where the third dimension is taken to be zero and
        the result is returned as a scalar."""

        return self.x * other.y - self.y * other.x

    def rotate(self, angle):
        """
        Rotate the given vector by an angle. Angle measured in radians 
        counter-clockwise.
        """
        x, y = self.tuple
        self._x = x * math.cos(angle) - y * math.sin(angle)
        self._y = x * math.sin(angle) + y * math.cos(angle)

    def round(self, digits=0):
        """
        Round the elements of the given vector to the given number of digits. 
        """
        self._x = round(self.x, digits)
        self._y = round(self.y, digits)


    def __init__(self, x, y):
        """Construct a vector using the given coordinates."""
        self._x = x
        self._y = y

    def __repr__(self):
        """Return a string representation of this vector."""
        return "Vector(%f, %f)" % self.tuple

    def __str__(self):
        """Return a string representation of this vector."""
        return "<%.2f, %.2f>" % self.tuple

    def __iter__(self):
        """Iterate over this vectors coordinates."""
        yield self.x
        yield self.y

    def __bool__(self):
        """Return true is the vector is not degenerate."""
        return self != (0, 0)

    __nonzero__ = __bool__

    def __getitem__(self, i):
        """Return the specified coordinate."""
        return self.tuple[i]

    def __eq__(self, other):
        """Return true if the given object has the same coordinates as this 
        vector."""
        try:
            other = cast_anything_to_vector(other)
            return self.x == other.x and self.y == other.y
        except VectorCastError:
            return False

    def __ne__(self, other):
        """Return true if the given object has different coordinates than this 
        vector."""
        return not self.__eq__(other)

    def __neg__(self):
        """Return a copy of this vector with the signs flipped."""
        return Vector(-self.x, -self.y)

    def __abs__(self):
        """Return the absolute value of this vector."""
        return Vector(abs(self.x), abs(self.y))
    
    __add__ = _overload_left_side(operator.add)
    __radd__ = _overload_right_side(operator.add)
    __iadd__ = _overload_in_place(operator.add)

    __sub__ = _overload_left_side(operator.sub)
    __rsub__ = _overload_right_side(operator.sub)
    __isub__ = _overload_in_place(operator.sub)

    __mul__ = _overload_left_side(operator.mul, scalar_ok=True)
    __rmul__ = _overload_right_side(operator.mul, scalar_ok=True)
    __imul__ = _overload_in_place(operator.mul, scalar_ok=True)

    __floordiv__ = _overload_left_side(operator.floordiv, scalar_ok=True)
    __rfloordiv__ = _overload_right_side(operator.floordiv, scalar_ok=True)
    __ifloordiv__ = _overload_in_place(operator.floordiv, scalar_ok=True)

    __truediv__ = _overload_left_side(operator.truediv, scalar_ok=True)
    __rtruediv__ = _overload_right_side(operator.truediv, scalar_ok=True)
    __itruediv__ = _overload_in_place(operator.truediv, scalar_ok=True)
    
    __div__ = __truediv__
    __rdiv__ = __rtruediv__
    __idiv__ = __itruediv__

    __mod__ = _overload_left_side(operator.mod, scalar_ok=True)
    __rmod__ = _overload_right_side(operator.mod, scalar_ok=True)
    __imod__ = _overload_in_place(operator.mod, scalar_ok=True)

    __pow__  = _overload_left_side(operator.pow, scalar_ok=True)
    __rpow__  = _overload_right_side(operator.pow, scalar_ok=True)
    __ipow__  = _overload_in_place(operator.pow, scalar_ok=True)

    def get_x(self):
        """Get the x coordinate of this vector."""
        return self._x

    def set_x(self, x):
        """Set the x coordinate of this vector."""
        self._x = x

    def get_y(self):
        """Get the y coordinate of this vector."""
        return self._y

    def set_y(self, y):
        """Set the y coordinate of this vector."""
        self._y = y

    def get_xy(self):
        """Return the vector as a tuple."""
        return self.x, self.y

    def set_xy(self, xy):
        """Set the x and y coordinates of this vector from a tuple."""
        self._x, self._y = xy

    def get_tuple(self):
        """Return the vector as a tuple."""
        return self.x, self.y

    def set_tuple(self, xy):
        """Set the x and y coordinates of this vector."""
        self._x, self._y = xy
    
    def get_magnitude(self):
        """Calculate the length of this vector."""
        return math.sqrt(self.magnitude_squared)

    def set_magnitude(self, scale):
        """Set the magnitude of this vector.   This is an alias for 
        `scale()`."""
        self.scale(scale)

    def get_magnitude_squared(self):
        """Calculate the square of the length of this vector.  This is
        slightly more efficient that finding the real length."""
        return self.x**2 + self.y**2

    @accept_anything_as_vector
    def get_distance(self, other):
        """Return the Euclidean distance between the two input vectors."""
        return (other - self).magnitude

    @accept_anything_as_vector
    def get_distance_squared(self, other):
        """Return the squared Euclidean distance between the two input vectors."""
        return (other - self).magnitude_squared

    @accept_anything_as_vector
    def get_manhattan(self, other):
        """Return the Manhattan distance between the two input vectors."""
        return sum(abs(other - self))

    def get_unit(self):
        """Return a unit vector parallel to this one."""
        result = self.copy()
        result.normalize()
        return result

    def get_orthogonal(self):
        """Return a vector that is orthogonal to this one.  The resulting
        vector is not normalized."""
        return Vector(-self.y, self.x)

    def get_orthonormal(self):
        """Return a vector that is orthogonal to this one and that has been 
        normalized."""
        return self.orthogonal.unit

    def get_scaled(self, magnitude):
        """Return a unit vector parallel to this one."""
        result = self.copy()
        result.scale(magnitude)
        return result

    def get_interpolated(self, target, extent):
        """Return a new vector that has been moved towards the given target by 
        the given extent.  The extent should be between 0 and 1."""
        result = self.copy()
        result.interpolate(target, extent)
        return result

    @accept_anything_as_vector
    def get_projection(self, axis):
        """Return the projection of this vector onto the given axis.  The 
        axis does not need to be normalized."""
        scale = axis.dot(self) / axis.dot(axis)
        return axis * scale

    @accept_anything_as_vector
    def get_components(self, other):
        """Break this vector into one vector that is perpendicular to the 
        given vector and another that is parallel to it."""
        tangent = self.get_projection(other)
        normal = self - tangent
        return normal, tangent

    def get_radians(self):
        """Return the angle between this vector and the positive x-axis 
        measured in radians.  Result will be between -pi and pi."""
        if not self: raise NullVectorError()
        return math.atan2(self.y, self.x)

    def set_radians(self, angle):
        """Set the angle that this vector makes with the x-axis."""
        self._x, self._y = math.cos(angle), math.sin(angle)

    def get_positive_radians(self):
        """Return the positive angle between this vector and the positive x-axis 
        measured in radians."""
        return (2 * math.pi + self.get_radians()) % (2 * math.pi)

    def get_degrees(self):
        """Return the angle between this vector and the positive x-axis measured 
        in degrees."""
        return self.radians * 180 / math.pi

    def set_degrees(self, angle):
        """Set the angle that this vector makes with the x-axis."""
        self.set_radians(angle * math.pi / 180)

    @accept_anything_as_vector
    def get_radians_to(self, other):
        """Return the angle between the two given vectors in radians.  If 
        either of the inputs are null vectors, an exception is thrown."""
        return other.radians - self.radians

    @accept_anything_as_vector
    def get_degrees_to(self, other):
        """Return the angle between the two given vectors in degrees.  If
        either of the inputs are null vectors, an exception is thrown."""
        return other.degrees - self.degrees

    def get_rotated(self, angle):
        """Return a vector rotated by angle from the given vector.  Angle 
        measured in radians counter-clockwise."""
        result = self.copy()
        result.rotate(angle)
        return result

    def get_rounded(self, digits):
        """Return a vector with the elements rounded to the given number of 
        digits."""
        result = self.copy()
        result.round(digits)
        return result

    # Aliases
    dot = dot_product
    perp = perp_product

@autoprop
class Rect(Shape):
    """
    Represent a mutable two-dimensional rectangle.
    """

    def __init__(self, left, bottom, width, height):
        self._left = left
        self._bottom = bottom
        self._width = width
        self._height = height

    def __repr__(self):
        return "Rect(%f, %f, %f, %f)" % self.tuple

    def __str__(self):
        return '<Rect bottom={0} left={1} width={2} height={3}>'.format(
                self.bottom, self.left, self.width, self.height)

    def __eq__(self, other):
        try:
            return (self.bottom == other.bottom and
                    self.left == other.left and
                    self.width == other.width and
                    self.height == other.height)
        except AttributeError:
            return False

    @accept_anything_as_vector
    def __add__(self, vector):
        result = self.copy()
        result.displace(vector)
        return result

    @accept_anything_as_vector
    def __iadd__(self, vector):
        self.displace(vector)
        return self

    @accept_anything_as_vector
    def __sub__(self, vector):
        result = self.copy()
        result.displace(-vector)
        return result

    @accept_anything_as_vector
    def __isub__(self, vector):
        self.displace(-vector)
        return self

    def __contains__(self, other):
        return self.contains(other)


    @staticmethod
    def null():
        """Create a rectangle with everything set to zero.  It will be located 
        at the origin and have no area."""
        return Rect(0, 0, 0, 0)

    @staticmethod
    def from_size(width, height):
        """Create a rectangle with the given width and height.  The bottom-left 
        corner will be on the origin."""
        return Rect(0, 0, width, height)

    @staticmethod
    def from_width(width, ratio=1/phi):
        """Create a rectangle with the given width.  The height will be 
        calculated from the given ratio, or the golden ratio by default."""
        return Rect.from_size(width, ratio * width)

    @staticmethod
    def from_height(height, ratio=phi):
        """Create a rectangle with the given height.  The width will be 
        calculated from the given ratio, or the golden ratio by default."""
        return Rect.from_size(ratio * height, height)

    @staticmethod
    def from_square(size):
        """Create a rectangle with the same width and height."""
        return Rect.from_size(size, size)

    @staticmethod
    def from_dimensions(left, bottom, width, height):
        """Create a rectangle with the given dimensions.  This is an alias for 
        the constructor."""
        return Rect(left, bottom, width, height)

    @staticmethod
    def from_sides(left, top, right, bottom):
        """Create a rectangle with the specified edge coordinates."""
        width = right - left; height = top - bottom
        return Rect.from_dimensions(left, bottom, width, height)

    @staticmethod
    def from_corners(v1, v2):
        """Create the rectangle defined by the two corners.  The corners can be 
        specified in any order."""
        v1 = cast_anything_to_vector(v1)
        v2 = cast_anything_to_vector(v2)

        left = min(v1.x, v2.x);  top = max(v1.y, v2.y)
        right = max(v1.x, v2.x); bottom = min(v1.y, v2.y)

        return Rect.from_sides(left, top, right, bottom)

    @staticmethod
    def from_bottom_left(position, width, height):
        """Create a rectangle with the given width, height, and bottom-left 
        corner."""
        position = cast_anything_to_vector(position)
        return Rect(position.x, position.y, width, height)

    @staticmethod
    def from_center(position, width, height):
        """Create a rectangle with the given dimensions centered at the given 
        position."""
        position = cast_anything_to_vector(position) - (width/2, height/2)
        return Rect(position.x, position.y, width, height)

    @staticmethod
    def from_vector(position):
        """Create a rectangle from a vector.  The rectangle will have no area, 
        and its bottom-let corner will be the same as the vector."""
        position = cast_anything_to_vector(position)
        return Rect(position.x, position.y, 0, 0)

    @staticmethod
    def from_points(*points):
        """Create a rectangle that contains all the given points."""
        left = min(cast_anything_to_vector(p).x for p in points)
        top = max(cast_anything_to_vector(p).y for p in points)
        right = max(cast_anything_to_vector(p).x for p in points)
        bottom = min(cast_anything_to_vector(p).y for p in points)
        return Rect.from_sides(left, top, right, bottom)

    @staticmethod
    def from_shape(shape):
        """Create a rectangle from an object that implements the `Shape` 
        interface."""
        bottom, left = shape.bottom, shape.left
        width, height = shape.width, shape.height
        return Rect(left, bottom, width, height)

    @staticmethod
    def from_pygame_surface(surface):
        """Create a rectangle from a `pygame.Surface`."""
        width, height = surface.get_size()
        return Rect.from_size(width, height)
    
    @staticmethod
    def from_pyglet_window(window):
        """Create a rectangle from a `pyglet.window.Window`."""
        return Rect.from_size(window.width, window.height)
    
    @staticmethod
    def from_pyglet_image(image):
        """Create a rectangle from a `pyglet.image.AbstractImage`."""
        return Rect.from_size(image.width, image.height)
    
    @staticmethod
    def from_union(*inputs):
        """Create a rectangle that contains all the given inputs.  Each input 
        must implement the `Shape` interface."""
        rects = [cast_shape_to_rectangle(x) for x in inputs]
        left = min(x.left for x in rects)
        top = max(x.top for x in rects)
        right = max(x.right for x in rects)
        bottom = min(x.bottom for x in rects)
        return Rect.from_sides(left, top, right, bottom)

    @staticmethod
    def from_intersection(*inputs):
        """Create a rectangle that represents the overlapping area between all 
        the given inputs.  Each input must implement the `Shape` interface."""
        rects = [cast_shape_to_rectangle(x) for x in inputs]
        left = max(x.left for x in rects)
        top = min(x.top for x in rects)
        right = min(x.right for x in rects)
        bottom = max(x.bottom for x in rects)
        return Rect.from_sides(left, top, right, bottom)


    def grow(self, *padding):
        """Grow this rectangle by the given padding on all sides."""
        try:
            lpad, rpad, tpad, bpad = padding
        except ValueError:
            lpad = rpad = tpad = bpad = padding[0]

        self._bottom -= bpad
        self._left -= lpad
        self._width += lpad + rpad
        self._height += tpad + bpad
        return self

    def shrink(self, *padding):
        """
        Shrink this rectangle by the given padding on all sides.  

        The padding can either be a single number (to be applied to all sides), or 
        a tuple of 4 number (to be applied to the left, right, top, and bottom, 
        respectively).
        """
        try:
            lpad, rpad, tpad, bpad = padding
        except ValueError:
            lpad = rpad = tpad = bpad = padding[0]

        self._bottom += bpad
        self._left += lpad
        self._width -= lpad + rpad
        self._height -= tpad + bpad
        return self

    @accept_anything_as_vector
    def displace(self, vector):
        """Displace this rectangle by the given vector."""
        self._bottom += vector.y
        self._left += vector.x
        return self

    def round(self, *args):
        """Round the dimensions of the given rectangle to the given number of 
        digits."""
        self._left = round(self._left, *args)
        self._bottom = round(self._bottom, *args)
        self._width = round(self._width, *args)
        self._height = round(self._height, *args)

    def set(self, shape):
        """Fill this rectangle with the dimensions of the given shape."""
        self.bottom, self.left = shape.bottom, shape.left
        self.width, self.height = shape.width, shape.height
        return self

    def copy(self):
        """Return a copy of this rectangle."""
        from copy import deepcopy
        return deepcopy(self)

    @accept_shape_as_rectangle
    def inside(self, other):
        """Return true if this rectangle is inside the given shape."""
        return ( self.left >= other.left and
                 self.right <= other.right and
                 self.top <= other.top and
                 self.bottom >= other.bottom)

    @accept_anything_as_rectangle
    def outside(self, other):
        """Return true if this rectangle is outside the given shape."""
        return not self.touching(other)

    @accept_anything_as_rectangle
    def touching(self, other):
        """Return true if this rectangle is touching the given shape."""
        if self.top < other.bottom: return False
        if self.bottom > other.top: return False

        if self.left > other.right: return False
        if self.right < other.left: return False

        return True

    @accept_anything_as_rectangle
    def contains(self, other):
        """Return true if the given shape is inside this rectangle."""
        return (self.left <= other.left and
                self.right >= other.right and
                self.top >= other.top and
                self.bottom <= other.bottom)

    @accept_anything_as_rectangle
    def align_left(self, target):
        """Make the left coordinate of this rectangle equal to that of the 
        given rectangle."""
        self.left = target.left

    @accept_anything_as_rectangle
    def align_center_x(self, target):
        """Make the center-x coordinate of this rectangle equal to that of the 
        given rectangle."""
        self.center_x = target.center_x

    @accept_anything_as_rectangle
    def align_right(self, target):
        """Make the right coordinate of this rectangle equal to that of the 
        given rectangle."""
        self.right = target.right

    @accept_anything_as_rectangle
    def align_top(self, target):
        """Make the top coordinate of this rectangle equal to that of the 
        given rectangle."""
        self.top = target.top

    @accept_anything_as_rectangle
    def align_center_y(self, target):
        """Make the center-y coordinate of this rectangle equal to that of the 
        given rectangle."""
        self.center_y = target.center_y

    @accept_anything_as_rectangle
    def align_bottom(self, target):
        """Make the bottom coordinate of this rectangle equal to that of the 
        given rectangle."""
        self.bottom = target.bottom

    # Scalar properties

    def get_left(self):
        return self._left

    def set_left(self, x):
        self._left = x

    def get_center_x(self):
        return self._left + self._width / 2

    def set_center_x(self, x):
        self._left = x - self._width / 2

    def get_right(self):
        return self._left + self._width

    def set_right(self, x):
        self._left = x - self._width

    def get_top(self):
        return self._bottom + self._height

    def set_top(self, y):
        self._bottom = y - self._height

    def get_center_y(self):
        return self._bottom + self._height / 2

    def set_center_y(self, y):
        self._bottom = y - self._height / 2

    def get_bottom(self):
        return self._bottom

    def set_bottom(self, y):
        self._bottom = y

    def get_area(self):
        return self._width * self._height

    def get_width(self):
        return self._width

    def set_width(self, width):
        self._width = width

    def get_height(self):
        return self._height

    def set_height(self, height):
        self._height = height

    def get_half_width(self):
        return self._width / 2

    def set_half_width(self, half_width):
        self._width = 2 * half_width

    def get_half_height(self):
        return self._height / 2

    def set_half_height(self, half_height):
        self._height = 2 * half_height

    # Vector properties

    def get_top_left(self):
        return Vector(self.left, self.top)

    @accept_anything_as_vector
    def set_top_left(self, point):
        self.top = point[1]
        self.left = point[0]

    def get_top_center(self):
        return Vector(self.center_x, self.top)

    @accept_anything_as_vector
    def set_top_center(self, point):
        self.top = point[1]
        self.center_x = point[0]

    def get_top_right(self):
        return Vector(self.right, self.top)

    @accept_anything_as_vector
    def set_top_right(self, point):
        self.top = point[1]
        self.right = point[0]

    def get_center_left(self):
        return Vector(self.left, self.center_y)

    @accept_anything_as_vector
    def set_center_left(self, point):
        self.center_y = point[1]
        self.left = point[0]

    def get_center(self):
        return Vector(self.center_x, self.center_y)

    @accept_anything_as_vector
    def set_center(self, point):
        self.center_y = point[1]
        self.center_x = point[0]

    def get_center_right(self):
        return Vector(self.right, self.center_y)

    @accept_anything_as_vector
    def set_center_right(self, point):
        self.center_y = point[1]
        self.right = point[0]

    def get_bottom_left(self):
        return Vector(self.left, self.bottom)

    @accept_anything_as_vector
    def set_bottom_left(self, point):
        self.bottom = point[1]
        self.left = point[0]

    def get_bottom_center(self):
        return Vector(self.center_x, self.bottom)

    @accept_anything_as_vector
    def set_bottom_center(self, point):
        self.bottom = point[1]
        self.center_x = point[0]

    def get_bottom_right(self):
        return Vector(self.right, self.bottom)

    @accept_anything_as_vector
    def set_bottom_right(self, point):
        self.bottom = point[1]
        self.right = point[0]

    def get_vertices(self):
        return self.top_left, self.top_right, self.bottom_right, self.bottom_left

    def set_vertices(self, vertices):
        self.top_left = vertices[0]
        self.top_right = vertices[1]
        self.bottom_right = vertices[2]
        self.bottom_left = vertices[3]

    def get_size(self):
        return Vector(self._width, self._height)

    def set_size(self, width, height):
        self._width = width
        self._height = height

    def get_size_as_int(self):
        from math import ceil
        return Vector(int(ceil(self._width)), int(ceil(self._height)))

    def get_dimensions(self):
        return (self._left, self._bottom), (self._width, self._height)

    def get_tuple(self):
        return self._left, self._bottom, self._width, self._height

    # Have to define properties manually, because `accept_anything_as_vector` 
    # causes `autoprop` to ignore the setters.
    top_left = property(get_top_left, set_top_left)
    top_center = property(get_top_center, set_top_center)
    top_right = property(get_top_right, set_top_right)
    center_left = property(get_center_left, set_center_left)
    center = property(get_center, set_center)
    center_right = property(get_center_right, set_center_right)
    bottom_left = property(get_bottom_left, set_bottom_left)
    bottom_center = property(get_bottom_center, set_bottom_center)
    bottom_right = property(get_bottom_right, set_bottom_right)

    # Rect properties

    def get_union(self, *rectangles):
        return Rect.from_union(self, *rectangles)

    def get_intersection(self, *rectangles):
        return Rect.from_intersection(self, *rectangles)

    def get_grown(self, padding):
        result = self.copy()
        result.grow(padding)
        return result

    def get_shrunk(self, padding):
        result = self.copy()
        result.shrink(padding)
        return result

    def get_rounded(self, *args):
        result = self.copy()
        result.round(*args)
        return result


def get_distance(a, b):
    """Return the distance between the two given vectors."""
    a = cast_anything_to_vector(a)
    return a.get_distance(b)

def get_distance_squared(a, b):
    """
    Return the squared distance between the to given vectors.

    It is faster to calculate squared distances than "normal" distances, so 
    prefer this function to `get_distance()` if possible.  For example, if you 
    just need to find which of several vectors is closest to another, the one 
    with the closest squared distance will also have the closest "normal" 
    distance.
    """
    a = cast_anything_to_vector(a)
    return a.get_distance_squared(b)

def interpolate(a, b, num_points=3):
    """Return a list of vectors that linearly interpolate between the given 
    vectors."""
    a = cast_anything_to_vector(a)
    b = cast_anything_to_vector(b)
    interpolation = [a]
    steps = num_points - 1
    assert steps >= 0

    for step in range(1, steps):
        v = a.get_interpolated(b, step/steps)
        interpolation.append(v)

    interpolation.append(b)
    return interpolation


# Exceptions

class NullVectorError(ValueError):
    """Thrown when an operation chokes on a null vector."""
    pass

class VectorCastError(TypeError):
    """Thrown when an inappropriate object is used as a vector."""

    def __init__(self, object):
        Exception.__init__(self, "Could not cast %s to vector." % repr(object))


class RectCastError(TypeError):
    """Thrown when an inappropriate object is used as a rectangle."""

    def __init__(self, object):
        Exception.__init__(self, "Could not cast %s to rectangle." % type(object))



