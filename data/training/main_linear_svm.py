"""
Main orchestrator script for Linear SVM sentiment analysis pipeline
Runs complete pipeline: data preparation -> Linear SVM training -> prediction
"""

import os
import sys
import time
from pathlib import Path

# Create necessary directories
os.makedirs('data', exist_ok=True)
os.makedirs('models', exist_ok=True)
os.makedirs('output', exist_ok=True)
os.makedirs('evaluation', exist_ok=True)

# Import modules
from train_linear_svm import LinearSVMTrainer
from predict_linear_svm import LinearSVMPredictor


def main():
    """
    Main execution pipeline for Linear SVM
    """
    
    print("\n" + "="*80)
    print(" "*20 + "🚀 LINEAR SVM SENTIMENT ANALYSIS 🚀")
    print("="*80)
    print(f"Start time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    start_time = time.time()
    
    # Step 1: Train Models with Linear SVM
    print("\n" + "█"*80)
    print("STEP 1: TRAINING LINEAR SVM MODELS")
    print("█"*80)
    
    if not os.path.exists('data/final_npn_ds.csv'):
        print("❌ Dataset not found at data/final_npn_ds.csv")
        print("   Please add the CSV file and try again")
        return
    
    trainer = LinearSVMTrainer('data/final_npn_ds.csv', max_iter=2000)
    trainer.train_all_models()
    
    # Step 2: Generate Predictions
    print("\n" + "█"*80)
    print("STEP 2: GENERATING PREDICTIONS (Linear SVM)")
    print("█"*80)
    
    predictor = LinearSVMPredictor(models_dir='models')
    
    if not predictor.models:
        print("❌ Failed to load models")
        return
    
    # Generate predictions on sample
    print("\n🔮 Generating predictions on 100 samples...\n")
    predictions = predictor.predict_and_save_sample(
        csv_path='data/final_npn_ds.csv',
        num_samples=100,
        text_column='text',
        output_path='output/prediction.json'
    )
    
    # Step 3: Display Results
    print("\n" + "█"*80)
    print("STEP 3: RESULTS SUMMARY")
    print("█"*80)
    
    print("\n✅ PIPELINE COMPLETED SUCCESSFULLY!\n")
    
    print("📊 Linear SVM Evaluation Results:")
    print("-" * 80)
    for model_name, results in trainer.evaluation_results.items():
        print(f"{model_name.upper():12} - Accuracy: {results['accuracy']:.4f}, F1: {results['f1']:.4f}")
    
    print("\n📁 Generated Files:")
    print("-" * 80)
    
    files_created = [
        'models/intent_model.pkl',
        'models/sentiment_model.pkl',
        'models/emotion_model.pkl',
        'models/urgency_model.pkl',
        'models/topic_model.pkl',
        'models/tfidf_pipeline.pkl',
        'output/prediction.json',
        'evaluation_report.txt'
    ]
    
    for file in files_created:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ✅ {file:<40} ({size:>10} bytes)")
        else:
            print(f"   ❌ {file:<40} (NOT FOUND)")
    
    print("\n📊 Sample Predictions (First 3 - Linear SVM):")
    print("-" * 80)
    
    if predictions:
        for i, pred in enumerate(predictions[:3], 1):
            print(f"\n{i}. TEXT: {pred['text'][:75]}{'...' if len(pred['text']) > 75 else ''}")
            print(f"   Intent:    {pred['intent']:20} | Confidence: {pred['confidence_scores']['intent']:.4f}")
            print(f"   Sentiment: {pred['sentiment']:20} | Confidence: {pred['confidence_scores']['sentiment']:.4f}")
            print(f"   Emotion:   {pred['emotion']:20} | Confidence: {pred['confidence_scores']['emotion']:.4f}")
            print(f"   Urgency:   {pred['urgency']:20} | Confidence: {pred['confidence_scores']['urgency']:.4f}")
            print(f"   Topic:     {pred['topic']:20} | Confidence: {pred['confidence_scores']['topic']:.4f}")
    
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    print(f"✅ TOTAL EXECUTION TIME: {total_time:.2f} seconds")
    print("="*80)
    
    print("\n💡 Why Linear SVM?")
    print("   ✅ Fast training on high-dimensional TF-IDF vectors")
    print("   ✅ Better generalization with L2 regularization")
    print("   ✅ Excellent for text classification tasks")
    print("   ✅ Lower memory footprint than non-linear kernels")
    print("   ✅ Class-weight balancing for imbalanced data")
    print("   ✅ CalibratedClassifierCV for probability estimates")
    
    print("\n💡 Next Steps:")
    print("   1. Check output/prediction.json for full results")
    print("   2. Review evaluation_report.txt for detailed metrics")
    print("   3. Share models/ folder with your team")
    print("   4. Use predict_linear_svm.py for inference on new data\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
