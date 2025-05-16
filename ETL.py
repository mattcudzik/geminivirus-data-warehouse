import os
import pandas as pd


def read_csv_virus_names(csv_file):
    df = pd.read_csv(csv_file)
    # Assuming the virus names are in the 'Virus Name' column
    return set(df['Virus Name'].str.lower().str.strip())

def read_virus_names_from_files(fasta_folder):
    virus_names = set()
    # Loop through all files in the folder
    for file_name in os.listdir(fasta_folder):
        # Check if the file is a .fa or .fai file
        if file_name.endswith(".fa"):
            # Extract virus name from the filename (before the extension)
            virus_name = os.path.splitext(file_name)[0]
            virus_names.add(virus_name.lower().replace("_", " ").strip())

    return virus_names

# Function to compare and print mismatches
def compare_virus_names(csv_file, fasta_folder):
    csv_names = read_csv_virus_names(csv_file)

    fasta_names = read_virus_names_from_files(fasta_folder)

    csv_not_in_fasta = csv_names.difference(fasta_names)
    fasta_not_in_csv = fasta_names.difference(csv_names)

    print("Viruses in CSV but not in .fa/.fai:")
    for name in csv_not_in_fasta:
        print(name)

    print("\nViruses in .fa/.fai but not in CSV:")
    for name in fasta_not_in_csv:
        print(name)

csv_file = 'scraped_virus_data.csv'  # Path to your CSV file
fasta_folder = 'genome'  # Path to your folder containing .fa and .fai files

# Run the comparison
compare_virus_names(csv_file, fasta_folder)
