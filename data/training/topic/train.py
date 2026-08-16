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
    confusion_matrix,
    classification_report
)


# ============================================================
# PROJECT ROOT
# ============================================================

ROOT_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

sys.path.append(ROOT_DIR)


# ============================================================
# COMMON PREPROCESSING + FEATURES
# ============================================================

from src.preprocessing import clean_text
from src.features import create_tfidf


# ============================================================
# RANDOM STATE
# ============================================================

RANDOM_STATE = 42


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
    "topic_model.pkl"
)

METRICS_PATH = os.path.join(
    ROOT_DIR,
    "evaluation",
    "topic_metrics.csv"
)

CM_PATH = os.path.join(
    ROOT_DIR,
    "evaluation",
    "topic_confusion_matrix.png"
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
    "topic"
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
# 4. SELECT ONLY TEXT + TOPIC
# ============================================================

df = df[
    [
        "text",
        "topic"
    ]
].copy()

print("\nColumns used for Topic model:")

print(
    df.columns.tolist()
)


# ============================================================
# 5. CHECK MISSING VALUES
# ============================================================

print("\n" + "=" * 70)
print("MISSING VALUES")
print("=" * 70)

print(
    df.isnull().sum()
)


# Remove rows where text or topic is missing

df = df.dropna(
    subset=[
        "text",
        "topic"
    ]
)


# ============================================================
# 6. CONVERT DATA TYPES
# ============================================================

df["text"] = (
    df["text"]
    .astype(str)
)

df["topic"] = (
    df["topic"]
    .astype(str)
    .str.lower()
    .str.strip()
)


# ============================================================
# 7. TEXT PREPROCESSING
# ============================================================

print("\n" + "=" * 70)
print("TEXT PREPROCESSING")
print("=" * 70)

df["clean_text"] = df["text"].apply(
    clean_text
)

print(
    "Text preprocessing completed."
)


# ============================================================
# 8. PREPROCESSING EXAMPLES
# ============================================================

print("\n" + "=" * 70)
print("PREPROCESSING EXAMPLES")
print("=" * 70)

for i in range(
    min(10, len(df))
):

    print("\nOriginal:")

    print(
        df.iloc[i]["text"]
    )

    print("Processed:")

    print(
        df.iloc[i]["clean_text"]
    )


# ============================================================
# 9. REMOVE EMPTY TEXT
# ============================================================

before_empty_removal = len(df)

df = df[
    df["clean_text"].str.len() > 0
]

after_empty_removal = len(df)

print("\n" + "=" * 70)
print("EMPTY TEXT REMOVAL")
print("=" * 70)

print(
    "Rows removed:",
    before_empty_removal - after_empty_removal
)


# ============================================================
# 10. CHECK TOPIC LABELS
# ============================================================

print("\n" + "=" * 70)
print("TOPIC LABELS")
print("=" * 70)

print(
    df["topic"].unique()
)

print(
    "\nNumber of classes:",
    df["topic"].nunique()
)


# ============================================================
# 11. INITIAL TOPIC DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("INITIAL TOPIC DISTRIBUTION")
print("=" * 70)

print(
    df["topic"].value_counts()
)

print("\nPercentages:")

print(
    (
        df["topic"]
        .value_counts(
            normalize=True
        )
        * 100
    ).round(2)
)


# ============================================================
# 12. CHECK CONFLICTING TOPIC LABELS
# ============================================================

print("\n" + "=" * 70)
print("CHECKING CONFLICTING LABELS")
print("=" * 70)

conflict_check = (
    df.groupby(
        "clean_text"
    )["topic"]
    .nunique()
)

conflicting_texts = (
    conflict_check[
        conflict_check > 1
    ].index
)

print(
    "Texts with conflicting topic labels:",
    len(conflicting_texts)
)


# Show examples and remove conflicts

if len(conflicting_texts) > 0:

    print(
        "\nExamples of conflicts:"
    )

    for text in conflicting_texts[:10]:

        print(
            "\nText:",
            text
        )

        print(
            df[
                df["clean_text"] == text
            ]["topic"].unique()
        )

    df = df[
        ~df["clean_text"].isin(
            conflicting_texts
        )
    ]


# ============================================================
# 13. REMOVE EXACT DUPLICATES
# ============================================================

before_duplicates = len(df)

df = df.drop_duplicates(
    subset=[
        "clean_text",
        "topic"
    ]
)

after_duplicates = len(df)

print("\n" + "=" * 70)
print("DUPLICATE REMOVAL")
print("=" * 70)

print(
    "Rows before:",
    before_duplicates
)

print(
    "Rows after:",
    after_duplicates
)

print(
    "Duplicates removed:",
    before_duplicates - after_duplicates
)


# ============================================================
# 14. DATASET DIVERSITY
# ============================================================

print("\n" + "=" * 70)
print("DATASET DIVERSITY")
print("=" * 70)

print(
    "Total rows:",
    len(df)
)

print(
    "Unique text examples:",
    df["clean_text"].nunique()
)


# ============================================================
# 15. FINAL TOPIC DISTRIBUTION
# ============================================================

print("\n" + "=" * 70)
print("FINAL TOPIC DISTRIBUTION")
print("=" * 70)

print(
    df["topic"].value_counts()
)

print("\nPercentages:")

print(
    (
        df["topic"]
        .value_counts(
            normalize=True
        )
        * 100
    ).round(2)
)


# ============================================================
# 16. CHECK FOR VERY SMALL CLASSES
# ============================================================

class_counts = (
    df["topic"]
    .value_counts()
)

small_classes = (
    class_counts[
        class_counts < 5
    ]
)

if len(small_classes) > 0:

    print("\n" + "=" * 70)
    print("WARNING: VERY SMALL CLASSES")
    print("=" * 70)

    print(
        small_classes
    )

    print(
        "\nEach topic class should ideally contain "
        "many examples for reliable evaluation."
    )


# ============================================================
# 17. INPUT AND TARGET
# ============================================================

X = df["clean_text"]

y = df["topic"]


# ============================================================
# 18. TRAIN / VALIDATION / TEST SPLIT
# ============================================================

X_train, X_temp, y_train, y_temp = (
    train_test_split(
        X,
        y,
        test_size=0.30,
        random_state=RANDOM_STATE,
        stratify=y
    )
)


X_val, X_test, y_val, y_test = (
    train_test_split(
        X_temp,
        y_temp,
        test_size=0.50,
        random_state=RANDOM_STATE,
        stratify=y_temp
    )
)


print("\n" + "=" * 70)
print("DATA SPLIT")
print("=" * 70)

print(
    "Training samples  :",
    len(X_train)
)

print(
    "Validation samples:",
    len(X_val)
)

print(
    "Test samples      :",
    len(X_test)
)


# ============================================================
# 19. TF-IDF + LINEAR SVM
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
# 20. TRAIN TOPIC MODEL
# ============================================================

print("\n" + "=" * 70)
print("TRAINING TOPIC - LINEAR SVM ONLY")
print("=" * 70)

model.fit(
    X_train,
    y_train
)

print(
    "Training completed."
)


# ============================================================
# 21. VALIDATION PREDICTION
# ============================================================

y_val_pred = model.predict(
    X_val
)


# ============================================================
# 22. VALIDATION METRICS
# ============================================================

val_accuracy = accuracy_score(
    y_val,
    y_val_pred
)

val_precision = precision_score(
    y_val,
    y_val_pred,
    average="macro",
    zero_division=0
)

val_recall = recall_score(
    y_val,
    y_val_pred,
    average="macro",
    zero_division=0
)

val_f1 = f1_score(
    y_val,
    y_val_pred,
    average="macro",
    zero_division=0
)


print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(
    f"Accuracy : {val_accuracy:.4f}"
)

print(
    f"Precision: {val_precision:.4f}"
)

print(
    f"Recall   : {val_recall:.4f}"
)

print(
    f"Macro F1 : {val_f1:.4f}"
)


# ============================================================
# 23. FINAL TEST PREDICTION
# ============================================================

y_pred = model.predict(
    X_test
)


# ============================================================
# 24. FINAL TEST METRICS
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


print("\n" + "=" * 70)
print("TOPIC FINAL TEST RESULTS")
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
# 25. CLASSIFICATION REPORT
# ============================================================

print("\n" + "=" * 70)
print("CLASSIFICATION REPORT")
print("=" * 70)

print(
    classification_report(
        y_test,
        y_pred,
        zero_division=0
    )
)


# ============================================================
# 26. SAVE METRICS
# ============================================================

os.makedirs(
    os.path.dirname(METRICS_PATH),
    exist_ok=True
)

metrics = pd.DataFrame([
    {
        "model": "Linear SVM",

        "validation_accuracy":
            val_accuracy,

        "validation_precision_macro":
            val_precision,

        "validation_recall_macro":
            val_recall,

        "validation_f1_macro":
            val_f1,

        "test_accuracy":
            accuracy,

        "test_precision_macro":
            precision,

        "test_recall_macro":
            recall,

        "test_f1_macro":
            f1,

        "training_samples":
            len(X_train),

        "validation_samples":
            len(X_val),

        "test_samples":
            len(X_test)
    }
])

metrics.to_csv(
    METRICS_PATH,
    index=False
)


# ============================================================
# 27. CONFUSION MATRIX
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
    figsize=(12, 10)
)

sns.heatmap(
    cm,
    annot=True,
    fmt="d",
    xticklabels=labels,
    yticklabels=labels
)

plt.xlabel(
    "Predicted Topic"
)

plt.ylabel(
    "Actual Topic"
)

plt.title(
    "Topic Confusion Matrix - Linear SVM"
)

plt.tight_layout()

plt.savefig(
    CM_PATH,
    dpi=300
)

plt.close()


# ============================================================
# 28. SAVE MODEL
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
# 29. COMPLETE
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
    "\nTopic training completed successfully."
)