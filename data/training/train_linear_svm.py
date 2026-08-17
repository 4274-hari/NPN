"""
Linear SVM Model Training Module
Trains all 5 classification models using LinearSVC for optimal performance
"""

import pickle
import os
import time
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.svm import LinearSVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.calibration import CalibratedClassifierCV
from preprocessing import preprocess_data, create_ml_pipeline, balance_dataset
from tqdm import tqdm
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class LinearSVMTrainer:
    """
    Trainer for 5-model sentiment analysis pipeline using Linear SVM
    
    Why Linear SVM?
    - Highly efficient for high-dimensional text data (TF-IDF)
    - Better generalization with good regularization
    - Faster training than non-linear kernels
    - Excellent for multi-class classification
    - Lower memory footprint
    """
    
    def __init__(self, data_path, output_dir='models', random_state=42, max_iter=2000):
        """
        Initialize trainer
        
        Args:
            data_path (str): Path to CSV dataset
            output_dir (str): Directory to save models
            random_state (int): Random state for reproducibility
            max_iter (int): Maximum iterations for SVM (higher = better convergence)
        """
        self.data_path = data_path
        self.output_dir = output_dir
        self.random_state = random_state
        self.max_iter = max_iter
        self.models = {}
        self.pipelines = {}
        self.evaluation_results = {}
        self.X_train = None
        self.X_test = None
        self.y_train = None
        self.y_test = None
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        print("⚙️  Linear SVM Configuration:")
        print(f"   - Algorithm: Linear SVC (One-vs-Rest for multi-class)")
        print(f"   - Max Iterations: {self.max_iter}")
        print(f"   - Regularization: Tuned per target (C=0.5, 1.0, 2.0)")
        print(f"   - Loss: Squared Hinge")
        print(f"   - Features: Word TF-IDF + character n-gram TF-IDF")
        print(f"   - Dual: False (n_features > n_samples)")
        print()
    
    def load_and_prepare_data(self):
        """
        Load CSV and prepare data for training
        """
        print("📥 Loading dataset...")
        df = pd.read_csv(self.data_path)
        df.columns = df.columns.str.strip().str.lower()
        print(f"   Dataset size: {len(df)} rows")
        
        # Preprocess text
        df = preprocess_data(df, text_column='text')
        
        return df
    
    def split_data(self, df, test_size=0.2):
        """
        Split data into train and test sets
        
        Args:
            df (pd.DataFrame): Preprocessed dataframe
            test_size (float): Test set size
        """
        print(f"✂️  Splitting data ({int((1-test_size)*100)}% train, {int(test_size*100)}% test)...")
        
        stratify = df['intent'] if 'intent' in df.columns else None

        # Store indices for target variables and fit vectorizer on train only.
        train_indices, test_indices = train_test_split(
            df.index,
            test_size=test_size,
            random_state=self.random_state,
            stratify=stratify,
        )
        
        self.df_train = df.loc[train_indices]
        self.df_test = df.loc[test_indices]

        pipeline = create_ml_pipeline()
        self.X_train = pipeline.fit_transform(self.df_train['text'])
        self.X_test = pipeline.transform(self.df_test['text'])
        self.pipeline = pipeline
        
        print(f"   Train set: {self.X_train.shape[0]} samples")
        print(f"   Test set: {self.X_test.shape[0]} samples")
        print(f"   Feature dimension: {self.X_train.shape[1]}")

    def _make_svm(self, c_value=1.0, class_weight=None):
        """Create a LinearSVC with the selected hyperparameters."""
        return LinearSVC(
            max_iter=self.max_iter,
            random_state=self.random_state,
            dual=False,
            loss='squared_hinge',
            C=c_value,
            class_weight=class_weight,
            verbose=0
        )

    def _select_best_svm_params(self, model_name, y_train):
        """
        Tune a small LinearSVC grid on a validation split.

        Accuracy is the primary objective because the user-facing request is
        accuracy improvement; weighted F1 is used as a tie-breaker.
        """
        y_train = y_train.reset_index(drop=True)
        X_for_tuning = self.X_train
        y_for_tuning = y_train

        max_tuning_samples = 120000
        if X_for_tuning.shape[0] > max_tuning_samples:
            positions = np.arange(X_for_tuning.shape[0])
            try:
                sample_positions, _ = train_test_split(
                    positions,
                    train_size=max_tuning_samples,
                    random_state=self.random_state,
                    stratify=y_for_tuning,
                )
            except ValueError:
                sample_positions, _ = train_test_split(
                    positions,
                    train_size=max_tuning_samples,
                    random_state=self.random_state,
                )
            X_for_tuning = X_for_tuning[sample_positions]
            y_for_tuning = y_for_tuning.iloc[sample_positions].reset_index(drop=True)

        try:
            X_fit, X_val, y_fit, y_val = train_test_split(
                X_for_tuning,
                y_for_tuning,
                test_size=0.2,
                random_state=self.random_state,
                stratify=y_for_tuning,
            )
        except ValueError:
            X_fit, X_val, y_fit, y_val = train_test_split(
                X_for_tuning,
                y_for_tuning,
                test_size=0.2,
                random_state=self.random_state,
            )

        candidates = [
            {'C': 0.5, 'class_weight': None},
            {'C': 1.0, 'class_weight': None},
            {'C': 2.0, 'class_weight': None},
            {'C': 0.5, 'class_weight': 'balanced'},
            {'C': 1.0, 'class_weight': 'balanced'},
            {'C': 2.0, 'class_weight': 'balanced'},
        ]

        best_params = candidates[0]
        best_score = (-1.0, -1.0)

        print("   Tuning LinearSVC hyperparameters...")
        for params in candidates:
            svm = self._make_svm(
                c_value=params['C'],
                class_weight=params['class_weight'],
            )
            svm.fit(X_fit, y_fit)
            y_pred = svm.predict(X_val)
            score = (
                accuracy_score(y_val, y_pred),
                f1_score(y_val, y_pred, average='weighted', zero_division=0),
            )
            print(
                f"      C={params['C']:<3} class_weight={str(params['class_weight']):<8} "
                f"accuracy={score[0]:.4f} f1={score[1]:.4f}"
            )
            if score > best_score:
                best_score = score
                best_params = params

        print(
            f"   Best for {model_name}: C={best_params['C']}, "
            f"class_weight={best_params['class_weight']} "
            f"(validation accuracy={best_score[0]:.4f})"
        )
        return best_params

    def train_target_model(self, model_name):
        """Train one target classifier with tuned Linear SVM settings."""
        print(f"\nðŸ¤– Training {model_name.upper()} Model (Tuned Linear SVM)...")
        start_time = time.time()

        y_train = self.df_train[model_name].reset_index(drop=True)
        y_test = self.df_test[model_name].reset_index(drop=True)

        unique_classes = sorted(y_train.unique())
        print(f"   Classes: {unique_classes}")
        print(f"   Class distribution:")
        for cls, count in y_train.value_counts().items():
            pct = count / len(y_train) * 100
            print(f"      {cls:20}: {count:7} ({pct:5.2f}%)")

        best_params = self._select_best_svm_params(model_name, y_train)

        svm = self._make_svm(
            c_value=best_params['C'],
            class_weight=best_params['class_weight'],
        )
        model = CalibratedClassifierCV(svm, cv=3)

        print("   Training final calibrated model...")
        model.fit(self.X_train, y_train)

        y_pred = model.predict(self.X_test)
        self._evaluate_model(model_name, y_test, y_pred)
        self.evaluation_results[model_name]['best_params'] = best_params

        self.models[model_name] = model
        setattr(self, f'y_test_{model_name}', y_test)

        elapsed = time.time() - start_time
        print(f"   âœ… Training completed in {elapsed:.2f}s")
    
    def train_intent_model(self):
        """Train INTENT classifier with Linear SVM"""
        print("\n🤖 Training INTENT Model (Linear SVM)...")
        start_time = time.time()
        
        y_train = self.df_train['intent']
        y_test = self.df_test['intent']
        
        unique_classes = sorted(y_train.unique())
        print(f"   Classes: {unique_classes}")
        print(f"   Class distribution:")
        for cls, count in y_train.value_counts().items():
            pct = count / len(y_train) * 100
            print(f"      {cls:12}: {count:7} ({pct:5.2f}%)")
        
        # Create Linear SVM with calibration for probability
        svm = LinearSVC(
            max_iter=self.max_iter,
            random_state=self.random_state,
            dual=False,
            loss='squared_hinge',
            C=1.0,
            class_weight='balanced',  # Handle class imbalance
            verbose=0
        )
        
        # Calibrate for probability estimates
        model = CalibratedClassifierCV(svm, cv=5)
        
        print("   Training...")
        model.fit(self.X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        self._evaluate_model('intent', y_test, y_pred)
        
        self.models['intent'] = model
        self.y_test_intent = y_test
        
        elapsed = time.time() - start_time
        print(f"   ✅ Training completed in {elapsed:.2f}s")
    
    def train_sentiment_model(self):
        """Train SENTIMENT classifier with Linear SVM"""
        print("\n🤖 Training SENTIMENT Model (Linear SVM)...")
        start_time = time.time()
        
        y_train = self.df_train['sentiment']
        y_test = self.df_test['sentiment']
        
        unique_classes = sorted(y_train.unique())
        print(f"   Classes: {unique_classes}")
        print(f"   Class distribution:")
        for cls, count in y_train.value_counts().items():
            pct = count / len(y_train) * 100
            print(f"      {cls:12}: {count:7} ({pct:5.2f}%)")
        
        svm = LinearSVC(
            max_iter=self.max_iter,
            random_state=self.random_state,
            dual=False,
            loss='squared_hinge',
            C=1.0,
            class_weight='balanced',
            verbose=0
        )
        
        model = CalibratedClassifierCV(svm, cv=5)
        
        print("   Training...")
        model.fit(self.X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        self._evaluate_model('sentiment', y_test, y_pred)
        
        self.models['sentiment'] = model
        self.y_test_sentiment = y_test
        
        elapsed = time.time() - start_time
        print(f"   ✅ Training completed in {elapsed:.2f}s")
    
    def train_emotion_model(self):
        """Train EMOTION classifier with Linear SVM"""
        print("\n🤖 Training EMOTION Model (Linear SVM)...")
        start_time = time.time()
        
        y_train = self.df_train['emotion']
        y_test = self.df_test['emotion']
        
        unique_classes = sorted(y_train.unique())
        print(f"   Classes: {unique_classes}")
        print(f"   Class distribution:")
        for cls, count in y_train.value_counts().items():
            pct = count / len(y_train) * 100
            print(f"      {cls:12}: {count:7} ({pct:5.2f}%)")
        
        svm = LinearSVC(
            max_iter=self.max_iter,
            random_state=self.random_state,
            dual=False,
            loss='squared_hinge',
            C=1.0,
            class_weight='balanced',
            verbose=0
        )
        
        model = CalibratedClassifierCV(svm, cv=5)
        
        print("   Training...")
        model.fit(self.X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        self._evaluate_model('emotion', y_test, y_pred)
        
        self.models['emotion'] = model
        self.y_test_emotion = y_test
        
        elapsed = time.time() - start_time
        print(f"   ✅ Training completed in {elapsed:.2f}s")
    
    def train_urgency_model(self):
        """Train URGENCY classifier with Linear SVM"""
        print("\n🤖 Training URGENCY Model (Linear SVM)...")
        start_time = time.time()
        
        y_train = self.df_train['urgency']
        y_test = self.df_test['urgency']
        
        unique_classes = sorted(y_train.unique())
        print(f"   Classes: {unique_classes}")
        print(f"   Class distribution:")
        for cls, count in y_train.value_counts().items():
            pct = count / len(y_train) * 100
            print(f"      {cls:12}: {count:7} ({pct:5.2f}%)")
        
        svm = LinearSVC(
            max_iter=self.max_iter,
            random_state=self.random_state,
            dual=False,
            loss='squared_hinge',
            C=1.0,
            class_weight='balanced',
            verbose=0
        )
        
        model = CalibratedClassifierCV(svm, cv=5)
        
        print("   Training...")
        model.fit(self.X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        self._evaluate_model('urgency', y_test, y_pred)
        
        self.models['urgency'] = model
        self.y_test_urgency = y_test
        
        elapsed = time.time() - start_time
        print(f"   ✅ Training completed in {elapsed:.2f}s")
    
    def train_topic_model(self):
        """Train TOPIC classifier with Linear SVM"""
        print("\n🤖 Training TOPIC Model (Linear SVM)...")
        start_time = time.time()
        
        y_train = self.df_train['topic']
        y_test = self.df_test['topic']
        
        unique_classes = sorted(y_train.unique())
        print(f"   Classes: {unique_classes}")
        print(f"   Class distribution:")
        for cls, count in y_train.value_counts().items():
            pct = count / len(y_train) * 100
            print(f"      {cls:12}: {count:7} ({pct:5.2f}%)")
        
        svm = LinearSVC(
            max_iter=self.max_iter,
            random_state=self.random_state,
            dual=False,
            loss='squared_hinge',
            C=1.0,
            class_weight='balanced',
            verbose=0
        )
        
        model = CalibratedClassifierCV(svm, cv=5)
        
        print("   Training...")
        model.fit(self.X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(self.X_test)
        self._evaluate_model('topic', y_test, y_pred)
        
        self.models['topic'] = model
        self.y_test_topic = y_test
        
        elapsed = time.time() - start_time
        print(f"   ✅ Training completed in {elapsed:.2f}s")
    
    def _evaluate_model(self, model_name, y_test, y_pred):
        """
        Evaluate model performance
        
        Args:
            model_name (str): Name of the model
            y_test: True labels
            y_pred: Predicted labels
        """
        accuracy = accuracy_score(y_test, y_pred)
        precision = precision_score(y_test, y_pred, average='weighted', zero_division=0)
        recall = recall_score(y_test, y_pred, average='weighted', zero_division=0)
        f1 = f1_score(y_test, y_pred, average='weighted', zero_division=0)
        
        self.evaluation_results[model_name] = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'classification_report': classification_report(y_test, y_pred, zero_division=0)
        }
        
        print(f"   📊 Evaluation Results:")
        print(f"      Accuracy:  {accuracy:.4f}")
        print(f"      Precision: {precision:.4f}")
        print(f"      Recall:    {recall:.4f}")
        print(f"      F1-Score:  {f1:.4f}")
    
    def save_models(self):
        """Save all trained models"""
        print("\n💾 Saving models...")
        
        for model_name, model in self.models.items():
            path = os.path.join(self.output_dir, f'{model_name}_model.pkl')
            with open(path, 'wb') as f:
                pickle.dump(model, f)
            
            # Get file size
            size = os.path.getsize(path)
            print(f"   ✅ {model_name}_model.pkl ({size/1024:.1f} KB)")
        
        # Save pipeline
        pipeline_path = os.path.join(self.output_dir, 'tfidf_pipeline.pkl')
        with open(pipeline_path, 'wb') as f:
            pickle.dump(self.pipeline, f)
        
        size = os.path.getsize(pipeline_path)
        print(f"   ✅ tfidf_pipeline.pkl ({size/1024:.1f} KB)")
    
    def save_evaluation_report(self):
        """Save evaluation report"""
        print("\n📊 Saving evaluation report...")
        
        report_path = os.path.join(self.output_dir, '../evaluation_report.txt')
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        
        with open(report_path, 'w') as f:
            f.write("=" * 80 + "\n")
            f.write("LINEAR SVM - SENTIMENT ANALYSIS PIPELINE - EVALUATION REPORT\n")
            f.write("=" * 80 + "\n")
            f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Algorithm: LinearSVC (One-vs-Rest Multi-class)\n")
            f.write(f"Max Iterations: {self.max_iter}\n")
            f.write(f"Loss: Squared Hinge\n")
            f.write(f"Kernel: Linear\n\n")
            
            for model_name, results in self.evaluation_results.items():
                f.write(f"\n{'='*80}\n")
                f.write(f"MODEL: {model_name.upper()}\n")
                f.write(f"{'='*80}\n")
                f.write(f"Accuracy:  {results['accuracy']:.4f}\n")
                f.write(f"Precision: {results['precision']:.4f}\n")
                f.write(f"Recall:    {results['recall']:.4f}\n")
                f.write(f"F1-Score:  {results['f1']:.4f}\n\n")
                if 'best_params' in results:
                    params = results['best_params']
                    f.write(f"Best C: {params['C']}\n")
                    f.write(f"Best class_weight: {params['class_weight']}\n\n")
                f.write("Classification Report:\n")
                f.write(results['classification_report'])
                f.write("\n")
        
        print(f"   ✅ evaluation_report.txt")
    
    def train_all_models(self):
        """Train all 5 models"""
        print("\n" + "="*80)
        print("LINEAR SVM SENTIMENT ANALYSIS PIPELINE")
        print("="*80)
        
        start_time = time.time()
        
        # Load and prepare data
        df = self.load_and_prepare_data()
        
        # Split data
        self.split_data(df)
        
        # Train all models with per-target hyperparameter tuning.
        for model_name in ['intent', 'sentiment', 'emotion', 'urgency', 'topic']:
            self.train_target_model(model_name)
        
        # Save everything
        self.save_models()
        self.save_evaluation_report()
        
        total_time = time.time() - start_time
        print("\n" + "="*80)
        print(f"✅ ALL MODELS TRAINED IN {total_time:.2f}s")
        print("="*80)
        
        # Print summary
        print("\n📊 SUMMARY:")
        print("-" * 80)
        for model_name, results in self.evaluation_results.items():
            print(f"   {model_name.upper():12} - Accuracy: {results['accuracy']:.4f}, F1: {results['f1']:.4f}")
        
        print("\n💡 Linear SVM Advantages:")
        print("   ✅ Fast training on high-dimensional data (TF-IDF)")
        print("   ✅ Better generalization with regularization")
        print("   ✅ Lower memory footprint")
        print("   ✅ Excellent for text classification")
        print("   ✅ Consistent performance across models")


if __name__ == "__main__":
    trainer = LinearSVMTrainer('data/final_npn_ds.csv', max_iter=2000)
    trainer.train_all_models()
