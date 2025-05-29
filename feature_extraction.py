import os

import pandas as pd
from Bio import SeqIO
import numpy as np
from collections import Counter
from config import *

from scipy.stats import entropy


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

    quartiles = [seq[i*length//4:(i+1)*length//4] for i in range(4)]
    quartile_gc = [(s.count("G") + s.count("C")) / len(s) if len(s) > 0 else 0 for s in quartiles]
    quartile_a = [(s.count("A")) / len(s) if len(s) > 0 else 0 for s in quartiles]
    quartile_t = [(s.count("T")) / len(s) if len(s) > 0 else 0 for s in quartiles]
    quartile_c = [(s.count("C")) / len(s) if len(s) > 0 else 0 for s in quartiles]
    quartile_g = [(s.count("G")) / len(s) if len(s) > 0 else 0 for s in quartiles]

    features = {
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

    for i in range(4):
        features[f"Quartile{i+1}_%A"] = quartile_a[i]
        features[f"Quartile{i+1}_%T"] = quartile_t[i]
        features[f"Quartile{i+1}_%C"] = quartile_c[i]
        features[f"Quartile{i+1}_%G"] = quartile_g[i]

    return features

def process_fasta_directory(folder_path):
    all_records = []
    for filename in os.listdir(folder_path):
        if filename.endswith(".fa") or filename.endswith(".fasta"):
            filepath = os.path.join(folder_path, filename)
            for record in SeqIO.parse(filepath, "fasta"):
                features = calculate_features(record.seq)
                features['Virus_Name'] = os.path.splitext(filename)[0].lower().replace("_", " ").strip()
                features['Accession'] = record.id
                features['Sequence'] = record.seq
                all_records.append(features)
    return pd.DataFrame(all_records)


df = process_fasta_directory(FASTA_FOLDER)
df.to_csv("virus_features.csv", index=False)