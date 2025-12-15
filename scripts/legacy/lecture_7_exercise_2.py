"""
Create a program that helps homeowners track their daily electricity usage and calculate monthly costs. 
This simulates a smart home energy monitoring system.

Requirements:
- Use a for loop to collect daily kilowatt-hour (kWh) usage for a month
- Use conditional statements to apply tiered pricing (common in real utility billing)
- Calculate total monthly cost and average daily usage
- Alert users when daily usage exceeds a threshold

Pricing Structure (typical residential rates):
- First 500 kWh: $0.12 per kWh
- Next 500 kWh (501-1000): $0.15 per kWh
- Over 1000 kWh: $0.18 per kWh

Sample Output:

Monthly Energy Usage Calculator
How many days in this month? 30
Enter kWh usage for day 1: 22.5
Enter kWh usage for day 2: 28.3
WARNING: High usage day! (28.3 kWh exceeds 25 kWh threshold)
Enter kWh usage for day 3: 19.8
...
Enter kWh usage for day 30: 24.1

--- Monthly Energy Report ---
Total monthly usage: 687.4 kWh
Average daily usage: 22.9 kWh
High usage days: 8

Monthly bill calculation:
First 500 kWh: 500.0 × $0.12 = $60.00
Next 187.4 kWh: 187.4 × $0.15 = $28.11
Total monthly cost: $88.11
"""

print("Monthly Energy Usage Calculator")
days_in_month = int(input("How many days in this month? "))

total_kwh = 0
high_usage_days = 0
threshold = 25  # Alert if daily usage exceeds 25 kWh

# Your code here: 
# - Use a for loop to get daily usage
# - Track total consumption and high usage days
# - Calculate tiered billing at the end

print(f"\n--- Monthly Energy Report ---")
# Display results here