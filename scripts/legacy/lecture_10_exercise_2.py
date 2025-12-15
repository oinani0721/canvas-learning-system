"""
Rectangle Class with Special Methods

Create a Rectangle class that represents a rectangle and implements special methods for comparison and arithmetic operations.

Requirements:
- Initialize the class with:
    - width (positive number)
    - height (positive number)

- Implement the following methods:
    - area(): Returns the area of the rectangle
    - perimeter(): Returns the perimeter of the rectangle
    - __str__(): Returns "Rectangle(width=5, height=3)"
    - __eq__(other): Two rectangles are equal if they have the same area
    - __lt__(other): One rectangle is less than another if its area is smaller

- Add validation: Raise a ValueError if width or height is not positive
"""