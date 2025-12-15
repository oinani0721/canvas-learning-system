"""
Exercise 1: Simple Payroll Calculator
You work for a small business that needs to calculate weekly pay for hourly employees. Write a program that processes multiple employees' time sheets.
Requirements:
- Use a while loop to process multiple employees (until user types "done")
- Use a for loop to collect daily hours for each employee (Monday through Friday)
- Apply overtime rules: hours over 40 get paid at 1.5x the regular rate
- Calculate and display each employee's total pay

Business Rules:
- Regular hours: $15.50 per hour
- Overtime hours (over 40): $23.25 per hour (1.5x regular rate)
- Work week is Monday through Friday

Sample Output:

Weekly Payroll Calculator
Enter daily hours for each employee (or 'done' to finish)
Enter employee name (or 'done' to quit): Alice
Enter hours for Monday: 8
Enter hours for Tuesday: 8
Enter hours for Wednesday: 9
Enter hours for Thursday: 8
Enter hours for Friday: 10
Alice worked 43.0 hours
Regular pay (40.0 hours): $620.00
Overtime pay (3.0 hours): $69.75
Total pay: $689.75
"""

regular_rate = 15.50
overtime_rate = regular_rate * 1.5

print("Weekly Payroll Calculator")
print("Enter daily hours for each employee (or 'done' to finish)")

employee_name = input("Enter employee name (or 'done' to quit): ")

while employee_name != "done":
    total_hours = 0
    
    # Your code here: use a for loop to get hours for each day
    # Calculate regular and overtime hours
    # Display the results
    
    days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    for day in days_of_week:
        while True:
            try:
                hours = float(input(f"Enter hours for {day}: "))
                if hours < 0:
                    print("Hours cannot be negative. Please enter a valid number.")
                    continue
                total_hours += hours
                break
            except ValueError:
                print("Invalid input. Please enter a number for hours.")
    
    print(f"{employee_name} worked {total_hours:.1f} hours")
    
    regular_hours = 0
    overtime_hours = 0
    
    if total_hours > 40:
        regular_hours = 40
        overtime_hours = total_hours - 40
    else:
        regular_hours = total_hours
        overtime_hours = 0
        
    regular_pay = regular_hours * regular_rate
    overtime_pay = overtime_hours * overtime_rate
    total_pay = regular_pay + overtime_pay
    
    print(f"Regular pay ({regular_hours:.1f} hours): ${regular_pay:.2f}")
    print(f"Overtime pay ({overtime_hours:.1f} hours): ${overtime_pay:.2f}")
    print(f"Total pay: ${total_pay:.2f}")
    
    employee_name = input("Enter employee name (or 'done' to quit): ")

print("Payroll processing complete!")