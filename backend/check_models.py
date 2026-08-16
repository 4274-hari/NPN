from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"

model_files = [
    "sentiment_model.pkl",
    "emotion_model.pkl",
    "intent_model.pkl",
    "topic_model.pkl",
    "urgency_model.pkl"
]

for file_name in model_files:
    print("\n" + "=" * 60)
    print(file_name)

    model = joblib.load(MODELS_DIR / file_name)

    print("Type:", type(model))

    print("Has predict_proba:", hasattr(model, "predict_proba"))
    print("Has transform:", hasattr(model, "transform"))
    print("Has steps:", hasattr(model, "steps"))

    if hasattr(model, "steps"):
        print("Pipeline steps:")
        for name, step in model.steps:
            print("  ", name, "->", type(step))

    if hasattr(model, "classes_"):
        print("Classes:", model.classes_)