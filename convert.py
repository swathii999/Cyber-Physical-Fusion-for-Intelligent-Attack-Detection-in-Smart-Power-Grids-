import pandas as pd

# Path to the input Excel file
input_excel_file = 'UMD Cyber Attacks Dataset.xlsx'  # Make sure the file is in the same directory or provide the full path

# Read the Excel file
df = pd.read_excel(input_excel_file)

# Path to save the output CSV file
output_csv_file = 'UMD_Cyber_Attacks_Dataset.csv'  # This will save in the same directory

# Convert to CSV and save
df.to_csv(output_csv_file, index=False)

print(f"File has been successfully converted and saved as: {output_csv_file}")
