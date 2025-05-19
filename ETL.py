import os
import pandas as pd
from Bio import SeqIO
import numpy as np
from collections import Counter

from pandas.core.interchange.dataframe_protocol import DataFrame
from scipy.stats import entropy

def find_missing_data(csv_file, fasta_folder):

    def read_csv_virus_names(csv_file):
        df = pd.read_csv(csv_file)
        return set(df['Virus Name'].str.lower().str.strip())

    def read_virus_names_from_files(fasta_folder):
        virus_names = set()

        for file_name in os.listdir(fasta_folder):
            if file_name.endswith(".fa"):
                virus_name = os.path.splitext(file_name)[0]
                virus_names.add(virus_name.lower().replace("_", " ").strip())

        return virus_names

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

def calculate_features(seq):
    seq = str(seq).upper()
    length = len(seq)

    if length == 0:
        return {}

    counts = Counter(seq)
    a = counts.get('A', 0) / length
    t = counts.get('T', 0) / length
    c = counts.get('C', 0) / length
    g = counts.get('G', 0) / length
    gc = g + c

    base_freqs = np.array([a, t, c, g])
    shannon_entropy = entropy(base_freqs, base=2)

    # GC content w 4 częściach
    quartiles = [seq[i*length//4:(i+1)*length//4] for i in range(4)]
    quartile_gc = [(s.count("G") + s.count("C")) / len(s) if len(s) > 0 else 0 for s in quartiles]

    return {
        "%A": a,
        "%T": t,
        "%C": c,
        "%G": g,
        "GC_content": gc,
        "Shannon_entropy": shannon_entropy,
        "Quartile1_GC": quartile_gc[0],
        "Quartile2_GC": quartile_gc[1],
        "Quartile3_GC": quartile_gc[2],
        "Quartile4_GC": quartile_gc[3],
        "Length": length
    }

def process_fasta_directory(folder_path):
    all_records = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".fa") or filename.endswith(".fasta"):
            filepath = os.path.join(folder_path, filename)
            for record in SeqIO.parse(filepath, "fasta"):
                features = calculate_features(record.seq)
                features['Virus_Name'] = os.path.splitext(filename)[0].lower().replace("_", " ").strip()
                features['Accession'] = record.id
                all_records.append(features)
    return pd.DataFrame(all_records)

if __name__ == "__main__":
    fasta_folder = "genome"
    df = process_fasta_directory(fasta_folder)
    print(df.head())
    df.to_csv("virus_features.csv", index=False)

#find_missing_data('scraped_virus_data.csv', 'genome')
