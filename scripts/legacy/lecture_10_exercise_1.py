"""
Student Class Implementation

Create a Student class that manages student information and grades.
Requirements:

- Initialize the class with:
    - name (string)
    - student_id (integer)
    - grades (empty list initially)
- Implement the following methods:
    - add_grade(grade): Adds a grade (0-100) to the student's grades list
    - get_average(): Returns the average of all grades (return 0 if no grades)
    - get_letter_grade(): Returns letter grade based on average:
        - A: 90-100, B: 80-89, C: 70-79, D: 60-69, F: below 60
    - __str__(): Returns a string representation like "John Doe (ID: 12345) - Average: 85.5 (B)"

Example Use:

student = Student("Alice Smith", 12345)
student.add_grade(92)
student.add_grade(87)
student.add_grade(95)
print(student)  # Should print: Alice Smith (ID: 12345) - Average: 91.3 (A)
print(student.get_average())  # Should print: 91.33333333333333
"""