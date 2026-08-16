import os
import sys
import joblib
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.append(ROOT_DIR)


# ============================================================
# IMPORT COMMON FILES
# ============================================================

from src.preprocessing import clean_text
from src.features import create_tfidf


# ============================================================
# PATHS
# ============================================================

DATA_PATH = os.path.join(
    ROOT_DIR,
    "data",
    "final_npn_ds.csv"
)

MODEL_PATH = os.path.join(
    ROOT_DIR,
    "models",
    "intent_model.pkl"
)

METRICS_PATH = os.path.join(
    ROOT_DIR,
    "evaluation",
    "intent_metrics.csv"
)

CM_PATH = os.path.join(
    ROOT_DIR,
    "evaluation",
    "intent_confusion_matrix.png"
)


# ============================================================
# 1. LOAD DATASET
# ============================================================

print("=" * 70)
print("LOADING DATASET")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print(
    "Dataset shape:",
    df.shape
)


# ============================================================
# 2. NORMALIZE COLUMN NAMES
# ============================================================

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
)

print("\nColumns found:")

print(
    df.columns.tolist()
)


# ============================================================
# 3. CHECK REQUIRED COLUMNS
# ============================================================

required_columns = [
    "text",
    "intent"
]

missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]

if missing_columns:

    raise ValueError(
        f"Missing required columns: {missing_columns}"
    )


# ============================================================
# 4. SELECT REQUIRED COLUMNS
# ============================================================

df = df[
    [
        "text",
        "intent"
    ]
].copy()


# ============================================================
# 5. REMOVE MISSING VALUES
# ============================================================

df = df.dropna(
    subset=[
        "text",
        "intent"
    ]
)


# ============================================================
# 6. CONVERT DATA TYPES
# ============================================================

df["text"] = (
    df["text"]
    .astype(str)
)

df["intent"] = (
    df["intent"]
    .astype(str)
    .str.lower()
    .str.strip()
)


# ============================================================
# 7. CLEAN TEXT
# ============================================================

print("\nCleaning text...")

df["clean_text"] = df["text"].apply(
    clean_text
)


# Remove empty text

df = df[
    df["clean_text"].str.len() > 0
]


# ============================================================
# 8. SHOW INTENT DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("INTENT DISTRIBUTION")
print("=" * 70)

print(
    df["intent"].value_counts()
)


# ============================================================
# 9. INPUT AND TARGET
# ============================================================

X = df["clean_text"]

y = df["intent"]


# ============================================================
# 10. TRAIN / TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(

    X,
    y,

    test_size=0.20,

    random_state=42,

    stratify=y
)


print("\n" + "=" * 70)
print("DATA SPLIT")
print("=" * 70)

print(
    "Training samples:",
    len(X_train)
)

print(
    "Testing samples:",
    len(X_test)
)


# ============================================================
# 11. TF-IDF + LINEAR SVM
# ============================================================

model = Pipeline([

    (
        "tfidf",
        create_tfidf()
    ),

    (
        "classifier",

        CalibratedClassifierCV(

            LinearSVC(
                class_weight="balanced"
            ),

            cv=3
        )
    )
])


# ============================================================
# 12. TRAIN MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING INTENT - LINEAR SVM")
print("=" * 70)

model.fit(
    X_train,
    y_train
)

print(
    "Training completed."
)


# ============================================================
# 13. PREDICTION
# ============================================================

y_pred = model.predict(
    X_test
)


# ============================================================
# 14. METRICS
# ============================================================

accuracy = accuracy_score(
    y_test,
    y_pred
)

precision = precision_score(
    y_test,
    y_pred,
    average="macro",
    zero_division=0
)

recall = recall_score(
    y_test,
    y_pred,
    average="macro",
    zero_division=0
)

f1 = f1_score(
    y_test,
    y_pred,
    average="macro",
    zero_division=0
)


# ============================================================
# 15. DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("INTENT RESULTS")
print("=" * 70)

print(
    f"Accuracy : {accuracy:.4f}"
)

print(
    f"Precision: {precision:.4f}"
)

print(
    f"Recall   : {recall:.4f}"
)

print(
    f"Macro F1 : {f1:.4f}"
)


# ============================================================
# 16. SAVE METRICS
# ============================================================

os.makedirs(
    os.path.dirname(METRICS_PATH),
    exist_ok=True
)

metrics = pd.DataFrame([

    {
        "model": "Linear SVM",
        "accuracy": accuracy,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "training_samples": len(X_train),
        "test_samples": len(X_test)
    }

])

metrics.to_csv(
    METRICS_PATH,
    index=False
)


# ============================================================
# 17. CONFUSION MATRIX
# ============================================================

labels = sorted(
    y_test.unique()
)

cm = confusion_matrix(
    y_test,
    y_pred,
    labels=labels
)


plt.figure(
    figsize=(10, 8)
)

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    xticklabels=labels,
    yticklabels=labels
)

plt.xlabel(
    "Predicted Intent"
)

plt.ylabel(
    "Actual Intent"
)

plt.title(
    "Intent Confusion Matrix - Linear SVM"
)

plt.tight_layout()

plt.savefig(
    CM_PATH,
    dpi=300
)

plt.close()


# ============================================================
# 18. SAVE MODEL
# ============================================================

os.makedirs(
    os.path.dirname(MODEL_PATH),
    exist_ok=True
)

joblib.dump(
    model,
    MODEL_PATH
)


# ============================================================
# 19. COMPLETE
# ============================================================

print("\n" + "=" * 70)
print("FILES SAVED")
print("=" * 70)

print(
    "Model:",
    MODEL_PATH
)

print(
    "Metrics:",
    METRICS_PATH
)

print(
    "Confusion Matrix:",
    CM_PATH
)

print(
    "\nIntent training completed successfully."
)