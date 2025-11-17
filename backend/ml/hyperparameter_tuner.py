"""
Hyperparameter Tuning for ML Models
Automatic optimization of model parameters using Grid Search and Random Search
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from sklearn.model_selection import (
    GridSearchCV, RandomizedSearchCV,
    cross_val_score, KFold
)
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.metrics import make_scorer, accuracy_score, f1_score, roc_auc_score
import logging
import pickle
import os
import json

logger = logging.getLogger(__name__)


class HyperparameterTuner:
    """
    Hyperparameter Tuning for ML Models

    Features:
    - Grid Search for exhaustive parameter search
    - Random Search for efficient parameter search
    - Cross-validation scoring
    - Best parameter selection
    - Performance comparison
    - Tuning history tracking
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Hyperparameter Tuner"""
        self.config = config or {}

        # Tuning method
        self.method = self.config.get('method', 'grid')  # grid, random
        self.cv_folds = self.config.get('cv_folds', 5)
        self.n_iter = self.config.get('n_iter', 50)  # for random search
        self.scoring = self.config.get('scoring', 'accuracy')
        self.n_jobs = self.config.get('n_jobs', -1)

        # Best model and parameters
        self.best_model = None
        self.best_params = {}
        self.best_score = 0.0

        # Tuning history
        self.tuning_history = []

        # Results path
        self.results_path = self.config.get('results_path', 'models/tuning_results.json')

    def get_param_grid_rf(self) -> Dict[str, List[Any]]:
        """Get parameter grid for Random Forest"""
        return {
            'n_estimators': [50, 100, 200, 300],
            'max_depth': [5, 10, 15, 20, None],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'max_features': ['sqrt', 'log2', None],
            'bootstrap': [True, False]
        }

    def get_param_grid_gb(self) -> Dict[str, List[Any]]:
        """Get parameter grid for Gradient Boosting"""
        return {
            'n_estimators': [50, 100, 200],
            'learning_rate': [0.01, 0.05, 0.1, 0.2],
            'max_depth': [3, 5, 7, 10],
            'min_samples_split': [2, 5, 10],
            'min_samples_leaf': [1, 2, 4],
            'subsample': [0.8, 0.9, 1.0]
        }

    def get_param_grid_svc(self) -> Dict[str, List[Any]]:
        """Get parameter grid for SVM"""
        return {
            'C': [0.1, 1, 10, 100],
            'gamma': ['scale', 'auto', 0.001, 0.01, 0.1],
            'kernel': ['rbf', 'poly', 'sigmoid']
        }

    def get_param_distributions_rf(self) -> Dict[str, Any]:
        """Get parameter distributions for Random Forest (random search)"""
        from scipy.stats import randint, uniform

        return {
            'n_estimators': randint(50, 500),
            'max_depth': [5, 10, 15, 20, 25, None],
            'min_samples_split': randint(2, 20),
            'min_samples_leaf': randint(1, 10),
            'max_features': ['sqrt', 'log2', None],
            'bootstrap': [True, False]
        }

    def tune_random_forest(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Optional[Dict[str, List[Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tune Random Forest classifier

        Args:
            X: Training features
            y: Training targets
            param_grid: Custom parameter grid (optional)

        Returns:
            Tuning results
        """
        if param_grid is None:
            if self.method == 'grid':
                param_grid = self.get_param_grid_rf()
            else:
                param_grid = self.get_param_distributions_rf()

        # Base model
        base_model = RandomForestClassifier(random_state=42, n_jobs=-1)

        # Perform search
        result = self._perform_search(base_model, X, y, param_grid, 'RandomForest')

        return result

    def tune_gradient_boosting(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Optional[Dict[str, List[Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tune Gradient Boosting classifier

        Args:
            X: Training features
            y: Training targets
            param_grid: Custom parameter grid (optional)

        Returns:
            Tuning results
        """
        if param_grid is None:
            param_grid = self.get_param_grid_gb()

        # Base model
        base_model = GradientBoostingClassifier(random_state=42)

        # Perform search
        result = self._perform_search(base_model, X, y, param_grid, 'GradientBoosting')

        return result

    def tune_svc(
        self,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Optional[Dict[str, List[Any]]] = None
    ) -> Dict[str, Any]:
        """
        Tune SVM classifier

        Args:
            X: Training features
            y: Training targets
            param_grid: Custom parameter grid (optional)

        Returns:
            Tuning results
        """
        if param_grid is None:
            param_grid = self.get_param_grid_svc()

        # Base model
        base_model = SVC(random_state=42, probability=True)

        # Perform search
        result = self._perform_search(base_model, X, y, param_grid, 'SVC')

        return result

    def _perform_search(
        self,
        base_model: Any,
        X: np.ndarray,
        y: np.ndarray,
        param_grid: Dict[str, Any],
        model_name: str
    ) -> Dict[str, Any]:
        """
        Perform hyperparameter search

        Args:
            base_model: Base ML model
            X: Training features
            y: Training targets
            param_grid: Parameter grid/distributions
            model_name: Name of the model

        Returns:
            Search results
        """
        logger.info(f"Starting {self.method} search for {model_name}...")

        start_time = datetime.now()

        if self.method == 'grid':
            search = GridSearchCV(
                estimator=base_model,
                param_grid=param_grid,
                cv=self.cv_folds,
                scoring=self.scoring,
                n_jobs=self.n_jobs,
                verbose=1,
                return_train_score=True
            )
        else:  # random
            search = RandomizedSearchCV(
                estimator=base_model,
                param_distributions=param_grid,
                n_iter=self.n_iter,
                cv=self.cv_folds,
                scoring=self.scoring,
                n_jobs=self.n_jobs,
                verbose=1,
                random_state=42,
                return_train_score=True
            )

        # Fit search
        search.fit(X, y)

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        # Extract results
        self.best_model = search.best_estimator_
        self.best_params = search.best_params_
        self.best_score = search.best_score_

        # Get CV results
        cv_results = pd.DataFrame(search.cv_results_)

        # Top 10 parameter combinations
        top_params = cv_results.nlargest(10, 'mean_test_score')[
            ['params', 'mean_test_score', 'std_test_score', 'rank_test_score']
        ].to_dict('records')

        result = {
            'model_name': model_name,
            'method': self.method,
            'best_params': self.best_params,
            'best_score': float(self.best_score),
            'best_train_score': float(search.cv_results_['mean_train_score'][search.best_index_]),
            'n_combinations_tried': len(cv_results),
            'duration_seconds': duration,
            'top_params': top_params,
            'cv_folds': self.cv_folds,
            'scoring': self.scoring
        }

        # Add to history
        self.tuning_history.append({
            'timestamp': datetime.now().isoformat(),
            'model_name': model_name,
            'best_score': self.best_score,
            'best_params': self.best_params
        })

        logger.info(f"{model_name} tuning complete. Best score: {self.best_score:.4f}")
        logger.info(f"Best params: {self.best_params}")
        logger.info(f"Duration: {duration:.2f} seconds")

        return result

    def compare_models(
        self,
        X: np.ndarray,
        y: np.ndarray,
        models: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple models with hyperparameter tuning

        Args:
            X: Training features
            y: Training targets
            models: List of model names to compare (default: ['rf', 'gb', 'svc'])

        Returns:
            Comparison results
        """
        if models is None:
            models = ['rf', 'gb']  # Skip SVC by default (slow)

        results = []

        for model_name in models:
            logger.info(f"\n{'='*50}")
            logger.info(f"Tuning {model_name.upper()}...")
            logger.info(f"{'='*50}\n")

            if model_name.lower() in ['rf', 'randomforest']:
                result = self.tune_random_forest(X, y)
            elif model_name.lower() in ['gb', 'gradientboosting']:
                result = self.tune_gradient_boosting(X, y)
            elif model_name.lower() in ['svc', 'svm']:
                result = self.tune_svc(X, y)
            else:
                logger.warning(f"Unknown model: {model_name}, skipping...")
                continue

            results.append(result)

        # Sort by best score
        results.sort(key=lambda x: x['best_score'], reverse=True)

        # Summary
        comparison = {
            'n_models': len(results),
            'results': results,
            'best_model': results[0]['model_name'] if results else None,
            'best_score': results[0]['best_score'] if results else 0.0,
            'best_params': results[0]['best_params'] if results else {}
        }

        logger.info(f"\n{'='*50}")
        logger.info("MODEL COMPARISON SUMMARY")
        logger.info(f"{'='*50}")
        for i, res in enumerate(results, 1):
            logger.info(f"{i}. {res['model_name']}: {res['best_score']:.4f}")
        logger.info(f"{'='*50}\n")

        return comparison

    def get_feature_importance(self, feature_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Get feature importance from best model

        Args:
            feature_names: Names of features (optional)

        Returns:
            Feature importance list
        """
        if self.best_model is None:
            logger.error("No model available")
            return []

        if not hasattr(self.best_model, 'feature_importances_'):
            logger.error("Model does not have feature importances")
            return []

        importance = self.best_model.feature_importances_
        n_features = len(importance)

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]

        importance_list = [
            {'name': name, 'importance': float(imp)}
            for name, imp in zip(feature_names, importance)
        ]

        # Sort by importance
        importance_list.sort(key=lambda x: x['importance'], reverse=True)

        return importance_list

    def evaluate_best_model(
        self,
        X_test: np.ndarray,
        y_test: np.ndarray
    ) -> Dict[str, Any]:
        """
        Evaluate best model on test set

        Args:
            X_test: Test features
            y_test: Test targets

        Returns:
            Evaluation metrics
        """
        if self.best_model is None:
            logger.error("No model available")
            return {}

        # Predictions
        y_pred = self.best_model.predict(X_test)

        # Metrics
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred, average='weighted')

        # Probabilities (if available)
        if hasattr(self.best_model, 'predict_proba'):
            y_proba = self.best_model.predict_proba(X_test)
            try:
                auc = roc_auc_score(y_test, y_proba[:, 1])
            except:
                auc = None
        else:
            y_proba = None
            auc = None

        return {
            'accuracy': float(accuracy),
            'f1_score': float(f1),
            'auc': float(auc) if auc is not None else None,
            'n_samples': len(y_test),
            'best_params': self.best_params,
            'best_cv_score': self.best_score
        }

    def save_results(self, path: Optional[str] = None) -> bool:
        """Save tuning results to file"""
        path = path or self.results_path

        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save results
            results = {
                'config': self.config,
                'best_params': self.best_params,
                'best_score': self.best_score,
                'tuning_history': self.tuning_history
            }

            with open(path, 'w') as f:
                json.dump(results, f, indent=2)

            # Save best model
            if self.best_model is not None:
                model_path = path.replace('.json', '_model.pkl')
                with open(model_path, 'wb') as f:
                    pickle.dump(self.best_model, f)

            logger.info(f"Tuning results saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving results: {e}")
            return False

    def load_results(self, path: Optional[str] = None) -> bool:
        """Load tuning results from file"""
        path = path or self.results_path

        try:
            # Load results
            with open(path, 'r') as f:
                results = json.load(f)

            self.config = results.get('config', self.config)
            self.best_params = results.get('best_params', {})
            self.best_score = results.get('best_score', 0.0)
            self.tuning_history = results.get('tuning_history', [])

            # Load best model
            model_path = path.replace('.json', '_model.pkl')
            if os.path.exists(model_path):
                with open(model_path, 'rb') as f:
                    self.best_model = pickle.load(f)

            logger.info(f"Tuning results loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Error loading results: {e}")
            return False

    def get_tuner_info(self) -> Dict[str, Any]:
        """Get tuner information"""
        return {
            'method': self.method,
            'cv_folds': self.cv_folds,
            'n_iter': self.n_iter if self.method == 'random' else None,
            'scoring': self.scoring,
            'best_score': self.best_score,
            'best_params': self.best_params,
            'n_tuning_runs': len(self.tuning_history),
            'tuning_history': self.tuning_history[-5:]  # Last 5 runs
        }
