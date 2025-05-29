CREATE TABLE virus_metadata (
    id SERIAL PRIMARY KEY,
    virus_name TEXT NOT NULL UNIQUE,
    genus TEXT,
    isolate_location TEXT,
    release_date DATE,
    submitter TEXT,
    host TEXT,
    vector TEXT
);

CREATE TABLE genomes (
    id SERIAL PRIMARY KEY,
    accession TEXT UNIQUE NOT NULL,
    virus_id INTEGER NOT NULL REFERENCES virus_metadata(id) ON DELETE CASCADE,
    raw_sequence TEXT,
    length INTEGER
);

CREATE TABLE features (
    id SERIAL PRIMARY KEY,
    genome_id INTEGER NOT NULL REFERENCES genomes(id) ON DELETE CASCADE,
    gc_content FLOAT,
    percent_a FLOAT,
    percent_t FLOAT,
    percent_c FLOAT,
    percent_g FLOAT,
    entropy FLOAT,
    quartile1_gc FLOAT,
    quartile2_gc FLOAT,
    quartile3_gc FLOAT,
    quartile4_gc FLOAT,
    quartile1_percent_a FLOAT,
    quartile1_percent_t FLOAT,
    quartile1_percent_c FLOAT,
    quartile1_percent_g FLOAT,
    quartile2_percent_a FLOAT,
    quartile2_percent_t FLOAT,
    quartile2_percent_c FLOAT,
    quartile2_percent_g FLOAT,
    quartile3_percent_a FLOAT,
    quartile3_percent_t FLOAT,
    quartile3_percent_c FLOAT,
    quartile3_percent_g FLOAT,
    quartile4_percent_a FLOAT,
    quartile4_percent_t FLOAT,
    quartile4_percent_c FLOAT,
    quartile4_percent_g FLOAT
);

CREATE TABLE models (
    version TEXT PRIMARY KEY,
    algorithm TEXT,
    accuracy FLOAT,
    trained_on DATE
);

CREATE TABLE classification_results (
    id SERIAL PRIMARY KEY,
    genome_id INTEGER NOT NULL REFERENCES genomes(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL REFERENCES models(version) ON DELETE CASCADE,
    predicted_genus TEXT,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
