**********************************************
``vecrec`` --- 2D vector and rectangle classes
**********************************************

This package provides 2D vector and rectangle classes.  These classes were 
written to be used in games, so they have some methods that conveniently tie 
into ``pyglet`` and ``pygame``, but for the most part they are quite general 
and could be used for almost anything.

.. image:: https://travis-ci.org/kxgames/vecrec.svg?branch=master
    :target: https://travis-ci.org/kxgames/vecrec

Installation
============
The ``vecrec`` module is pure-python, dependency-free, and available from 
PyPI::

   $ pip install vecrec

Basic Usage
===========
In lieu of complete API documentation, here are a few examples showing how to 
construct and use use the ``Vector`` and ``Rect`` classes provided by this 
package::

   >>> from vecrec import Vector, Rect
   >>> a = Vector(1, 2)
   >>> b = Vector(3, 4)
   >>> a + b
   Vector(4, 6)

Rectangles are more commonly constructed using factory methods::

   >>> Rect.from_size(8, 11)
   Rect(0, 0, 8, 11)
   >>> Rect.from_center(a, 1, 1)
   Rect(0, 1, 1, 1)
