import pandas as pd
import psycopg2
from datetime import datetime
from sklearn.ensemble import RandomForestClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score
import joblib
import os
from config import *
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

MODEL_VERSION = "_v1"

# === Prepare output directory ===
os.makedirs(MODEL_OUTPUT_DIR, exist_ok=True)

# === Connect to DB and fetch data ===
conn = psycopg2.connect(**DB_CONFIG)
cursor = conn.cursor()

print("Fetching features and labels from DB...")

query = """
SELECT
    f.genome_id,
    v.genus,
    f.gc_content, 
    f.percent_a, f.percent_t, f.percent_c, f.percent_g,
    f.entropy,
    f.quartile1_gc, f.quartile2_gc, f.quartile3_gc, f.quartile4_gc,
    f.quartile1_percent_a, f.quartile1_percent_t, f.quartile1_percent_c, f.quartile1_percent_g,
    f.quartile2_percent_a, f.quartile2_percent_t, f.quartile2_percent_c, f.quartile2_percent_g,
    f.quartile3_percent_a, f.quartile3_percent_t, f.quartile3_percent_c, f.quartile3_percent_g,
    f.quartile4_percent_a, f.quartile4_percent_t, f.quartile4_percent_c, f.quartile4_percent_g 
FROM features f
JOIN genomes g ON f.genome_id = g.id
JOIN virus_metadata v ON g.virus_id = v.id
WHERE v.genus IS NOT NULL;
"""

df = pd.read_sql(query, conn)
df.dropna(inplace=True)

X = df.drop(columns=['genome_id', 'genus'])
y = df['genus']
genome_ids = df['genome_id']

# === Models ===
models = {
    'RandomForest': RandomForestClassifier(n_estimators=100, random_state=42),
    'MLP': MLPClassifier(hidden_layer_sizes=(64, 32), max_iter=300, random_state=42),
    'SVM': SVC(probability=True, kernel='rbf', random_state=42)
}

# === Cross-validation config ===
cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

# === Train, cross-validate, and save ===
for model_name, model in models.items():

    # Cross-validated scores
    scores = cross_val_score(model, X, y, cv=cv, scoring='accuracy')
    avg_acc = scores.mean()
    print(f"{model_name} Accuracy: {avg_acc:.4f}")

    #Full prediction for all data
    y_pred = cross_val_predict(model, X, y, cv=cv)
    model.fit(X, y)

    #Save model to disk
    model_path = os.path.join(MODEL_OUTPUT_DIR, f"{model_name}_v1.joblib")
    joblib.dump(model, model_path)

    labels = sorted(list(set(y)))
    cm = confusion_matrix(y, y_pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)

    plt.figure(figsize=(10, 8))

    disp.plot(cmap="Blues")
    plt.title(f"Confusion Matrix – {model_name}")
    plt.xticks(rotation=45, ha='right', rotation_mode='anchor')
    plt.tight_layout()

    cm_path = os.path.join(MODEL_OUTPUT_DIR, f"{model_name}_confusion_matrix.png")
    plt.savefig(cm_path)
    plt.close()
    print(f"Saved confusion matrix to {cm_path}")

    #Register model in DB
    cursor.execute("""
        INSERT INTO models (version, algorithm, accuracy, trained_on)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (version) DO NOTHING;
    """, (
        model_name + MODEL_VERSION,
        model_name,
        float(avg_acc),
        datetime.now().date()
    ))

    #Save predictions
    for genome_id, prediction in zip(genome_ids, y_pred):
        cursor.execute("""
            INSERT INTO classification_results (
                genome_id, model_version, predicted_genus, predicted_at
            )
            VALUES (%s, %s, %s, %s);
        """, (
            int(genome_id),
            model_name + MODEL_VERSION,
            prediction,
            datetime.now()
        ))

conn.commit()
cursor.close()
conn.close()
