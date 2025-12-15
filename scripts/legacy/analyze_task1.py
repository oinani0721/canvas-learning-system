
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Create a directory to save the plots
if not os.path.exists('plots'):
    os.makedirs('plots')

# Load the dataset
try:
    df = pd.read_csv('Credit.csv')
except FileNotFoundError:
    print("Error: Credit.csv not found. Please make sure the file is in the correct directory.")
    exit()

# Identify quantitative variables
quantitative_vars = ['Income', 'Limit', 'Rating', 'Cards', 'Age', 'Education', 'Balance']

# --- Task 1: Create and save histograms for all quantitative variables ---

# Set plot style
sns.set_style("whitegrid")

# Generate and save a histogram for each quantitative variable
for var in quantitative_vars:
    plt.figure(figsize=(10, 6))
    sns.histplot(df[var], kde=True, bins=30)
    plt.title(f'Distribution of {var}', fontsize=16)
    plt.xlabel(var, fontsize=12)
    plt.ylabel('Frequency', fontsize=12)
    
    # Save the plot
    plot_path = f'plots/{var}_histogram.png'
    plt.savefig(plot_path)
    plt.close() # Close the plot to free up memory
    print(f"Histogram for {var} saved to {plot_path}")

print("\nTask 1 finished: All histograms have been generated and saved in the 'plots' directory.") 