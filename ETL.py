import os
import pandas as pd
import psycopg2
from Bio import SeqIO
import numpy as np
from collections import Counter
from psycopg2.extras import execute_values
from datetime import datetime
from config import *

from scipy.stats import entropy

def populate_warehouse():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    metadata_df = pd.read_csv(METADATA_CSV)
    metadata_df.fillna('', inplace=True)

    virus_name_to_id = {}

    for _, row in metadata_df.iterrows():
        virus_name = row['Virus Name'].strip().lower()

        try:
            release_date = datetime.strptime(row['Release date'], "%Y/%m/%d").date()
        except (ValueError, TypeError):
            release_date = None

        cursor.execute("""
            INSERT INTO virus_metadata (virus_name, genus, isolate_location, release_date, submitter, host, vector)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (virus_name) DO NOTHING
            RETURNING id;
        """, (
            virus_name,
            row['Genus'],
            row['Isolate'],
            release_date,
            row['Submitter'],
            row['Host'],
            row['Vector']
        ))

        result = cursor.fetchone()
        if result:
            virus_id = result[0]
        else:
            cursor.execute("SELECT id FROM virus_metadata WHERE virus_name = %s", (virus_name,))
            virus_id = cursor.fetchone()[0]

        virus_name_to_id[virus_name] = virus_id

    conn.commit()

    features_df = pd.read_csv(FEATURES_CSV)
    features_df.fillna('', inplace=True)

    for _, row in features_df.iterrows():
        virus_name = row['Virus_Name'].strip().lower()
        accession = row['Accession'].strip()
        length = int(row['Length'])
        sequence = row['Sequence'].strip().upper()

        if virus_name not in virus_name_to_id:
            print(f"⚠️ Virus '{virus_name}' not found in metadata. Skipping genome: {accession}")
            continue

        virus_id = virus_name_to_id[virus_name]

        # === Insert genome with sequence ===
        cursor.execute("""
            INSERT INTO genomes (accession, virus_id, raw_sequence, length)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (accession) DO NOTHING
            RETURNING id;
        """, (accession, virus_id, sequence, length))

        result = cursor.fetchone()
        if result:
            genome_id = result[0]
        else:
            cursor.execute("SELECT id FROM genomes WHERE accession = %s", (accession,))
            genome_id = cursor.fetchone()[0]

        # === Insert features ===
        cursor.execute("""
            INSERT INTO features (
                genome_id, gc_content, percent_a, percent_t, percent_c, percent_g,
                entropy, quartile1_gc, quartile2_gc, quartile3_gc, quartile4_gc
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """, (
            genome_id,
            row['GC_content'],
            row['%A'],
            row['%T'],
            row['%C'],
            row['%G'],
            row['Shannon_entropy'],
            row['Quartile1_GC'],
            row['Quartile2_GC'],
            row['Quartile3_GC'],
            row['Quartile4_GC']
        ))

    conn.commit()
    cursor.close()
    conn.close()

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
                features['Sequence'] = record.seq
                all_records.append(features)
    return pd.DataFrame(all_records)

if __name__ == "__main__":
    df = process_fasta_directory(FASTA_FOLDER)
    df.to_csv("virus_features.csv", index=False)
    populate_warehouse()



