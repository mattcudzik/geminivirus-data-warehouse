import pandas as pd
import psycopg2
from datetime import datetime
from config import *


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
            print(f"Virus '{virus_name}' not found in metadata. Skipping genome: {accession}")
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
                entropy, quartile1_gc, quartile2_gc, quartile3_gc, quartile4_gc, 
                quartile1_percent_a,
                quartile1_percent_t,
                quartile1_percent_c,
                quartile1_percent_g,
                quartile2_percent_a,
                quartile2_percent_t,
                quartile2_percent_c,
                quartile2_percent_g,
                quartile3_percent_a,
                quartile3_percent_t,
                quartile3_percent_c,
                quartile3_percent_g,
                quartile4_percent_a,
                quartile4_percent_t,
                quartile4_percent_c,
                quartile4_percent_g 
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
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
            row['Quartile4_GC'],

            row["Quartile1_%A"],
            row["Quartile1_%T"],
            row["Quartile1_%C"],
            row["Quartile1_%G"],

            row["Quartile2_%A"],
            row["Quartile2_%T"],
            row["Quartile2_%C"],
            row["Quartile2_%G"],

            row["Quartile3_%A"],
            row["Quartile3_%T"],
            row["Quartile3_%C"],
            row["Quartile3_%G"],

            row["Quartile4_%A"],
            row["Quartile4_%T"],
            row["Quartile4_%C"],
            row["Quartile4_%G"]
        ))

    conn.commit()
    cursor.close()
    conn.close()

populate_warehouse()



