"""
Coffee Shop Discount Calculator

The local coffee shop has the following discount rules:
- If you buy 5 or more coffees, you get a 20% discount
- If you're a student AND it's before 10am, you get a 15% discount
- If it's your birthday, you get a 25% discount
- Only the highest discount can be applied

Write a program that:
1. Asks for the number of coffees ordered
2. Asks if the customer is a student (yes/no)
3. Asks for the current hour (0-23 where 0 is 12AM and 23 is 11PM)
4. Asks if it's the customer's birthday (yes/no)
5. Calculates and prints the highest discount the customer is eligible for

Each coffee costs $5.

Example output:
Number of coffees: 3
Are you a student? (yes/no): yes
What hour is it? (0-23): 9
Is it your birthday? (yes/no): no

Original price: $15.00
You get a 15% student discount!
Final price: $12.75

HINT: You can retrieve user input using the input() function. For example:
number_of_coffees = input("Number of coffees: ")

HINT: You can convert a string to an integer using the int() function. For example:
number_of_coffees = int(number_of_coffees)
"""

