-- Tabela: virus_metadata (czysto opisowa – dane źródłowe, biologiczne)
CREATE TABLE virus_metadata (
    id SERIAL PRIMARY KEY,
    virus_name TEXT NOT NULL UNIQUE,           -- np. Abutilon golden mosaic virus
    genus TEXT,                         -- np. Begomovirus
    isolate_location TEXT,              -- np. Mexico: Yucatan
    release_date DATE,
    submitter TEXT,
    host TEXT,
    vector TEXT
);

-- Tabela: genomes (pojedyncze sekwencje genomowe powiązane z metadanymi)
CREATE TABLE genomes (
    id SERIAL PRIMARY KEY,
    accession TEXT UNIQUE NOT NULL,     -- np. GCF_002821485.1
    virus_id INTEGER NOT NULL REFERENCES virus_metadata(id) ON DELETE CASCADE,
    raw_sequence TEXT,                  -- sekwencja DNA
    length INTEGER                      -- długość sekwencji
);

-- Tabela: features (cechy biologiczne wyciągnięte z sekwencji genomowej)
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
    quartile4_gc FLOAT
);

-- Tabela: models (rejestr modeli ML)
CREATE TABLE models (
    version TEXT PRIMARY KEY,
    algorithm TEXT,
    accuracy FLOAT,
    trained_on DATE
);

-- Tabela: classification_results (wyniki klasyfikacji)
CREATE TABLE classification_results (
    id SERIAL PRIMARY KEY,
    genome_id INTEGER NOT NULL REFERENCES genomes(id) ON DELETE CASCADE,
    model_version TEXT NOT NULL REFERENCES models(version) ON DELETE CASCADE,
    predicted_genus TEXT,
    confidence FLOAT,
    predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
