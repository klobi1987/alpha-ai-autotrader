"""
Ensemble Methods for ML Pattern Discovery
Combines multiple models for improved prediction accuracy
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sklearn.ensemble import (
    VotingClassifier, VotingRegressor,
    StackingClassifier, StackingRegressor,
    RandomForestClassifier, GradientBoostingClassifier,
    RandomForestRegressor, GradientBoostingRegressor,
    AdaBoostClassifier, BaggingClassifier
)
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.svm import SVC, SVR
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import cross_val_score
from sklearn.preprocessing import StandardScaler
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class EnsembleMethods:
    """
    Ensemble Methods for Pattern Prediction

    Features:
    - Voting Classifier (hard/soft voting)
    - Stacking Classifier
    - Bagging ensemble
    - Boosting methods (AdaBoost, Gradient Boosting)
    - Model diversity analysis
    - Cross-validation scoring
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Ensemble Methods"""
        self.config = config or {}

        # Ensemble type
        self.ensemble_type = self.config.get('ensemble_type', 'voting')  # voting, stacking
        self.voting_type = self.config.get('voting_type', 'soft')  # hard, soft
        self.n_estimators = self.config.get('n_estimators', 100)

        # Models
        self.base_models = []
        self.ensemble_model = None
        self.scaler = StandardScaler()

        # Training state
        self.is_trained = False
        self.model_scores = {}

        # Model path
        self.model_path = self.config.get('model_path', 'models/ensemble_model.pkl')

    def build_base_models_classifier(self) -> List[Tuple[str, Any]]:
        """Build base classifiers for ensemble"""
        base_models = [
            ('rf', RandomForestClassifier(
                n_estimators=self.n_estimators,
                max_depth=10,
                min_samples_split=5,
                min_samples_leaf=2,
                random_state=42,
                n_jobs=-1
            )),
            ('gb', GradientBoostingClassifier(
                n_estimators=self.n_estimators,
                learning_rate=0.1,
                max_depth=5,
                min_samples_split=5,
                random_state=42
            )),
            ('svc', SVC(
                kernel='rbf',
                C=1.0,
                gamma='scale',
                probability=True,
                random_state=42
            )),
            ('ada', AdaBoostClassifier(
                n_estimators=50,
                learning_rate=1.0,
                random_state=42
            )),
            ('nb', GaussianNB())
        ]

        logger.info(f"Built {len(base_models)} base classifiers")
        return base_models

    def build_voting_classifier(self) -> VotingClassifier:
        """Build voting classifier ensemble"""
        base_models = self.build_base_models_classifier()

        ensemble = VotingClassifier(
            estimators=base_models,
            voting=self.voting_type,
            n_jobs=-1
        )

        logger.info(f"Built voting classifier: {self.voting_type} voting, {len(base_models)} models")
        return ensemble

    def build_stacking_classifier(self) -> StackingClassifier:
        """Build stacking classifier ensemble"""
        base_models = self.build_base_models_classifier()

        # Meta-learner
        meta_learner = LogisticRegression(
            C=1.0,
            max_iter=1000,
            random_state=42
        )

        ensemble = StackingClassifier(
            estimators=base_models,
            final_estimator=meta_learner,
            cv=5,
            n_jobs=-1
        )

        logger.info(f"Built stacking classifier: {len(base_models)} base models + LogisticRegression meta-learner")
        return ensemble

    def build_bagging_classifier(self) -> BaggingClassifier:
        """Build bagging classifier ensemble"""
        base_estimator = DecisionTreeClassifier(
            max_depth=10,
            min_samples_split=5,
            random_state=42
        )

        ensemble = BaggingClassifier(
            base_estimator=base_estimator,
            n_estimators=self.n_estimators,
            max_samples=0.8,
            max_features=0.8,
            bootstrap=True,
            n_jobs=-1,
            random_state=42
        )

        logger.info(f"Built bagging classifier: {self.n_estimators} estimators")
        return ensemble

    def build_ensemble(self, task: str = 'classification') -> Any:
        """
        Build ensemble model

        Args:
            task: 'classification' or 'regression'

        Returns:
            Ensemble model
        """
        if task == 'classification':
            if self.ensemble_type == 'voting':
                return self.build_voting_classifier()
            elif self.ensemble_type == 'stacking':
                return self.build_stacking_classifier()
            elif self.ensemble_type == 'bagging':
                return self.build_bagging_classifier()
            else:
                logger.warning(f"Unknown ensemble type: {self.ensemble_type}, using voting")
                return self.build_voting_classifier()
        else:
            # TODO: Add regression ensemble methods if needed
            logger.error("Regression ensembles not yet implemented")
            return None

    def train(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        task: str = 'classification'
    ) -> Dict[str, Any]:
        """
        Train ensemble model

        Args:
            X_train: Training features
            y_train: Training targets
            task: 'classification' or 'regression'

        Returns:
            Training results
        """
        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Build ensemble
        self.ensemble_model = self.build_ensemble(task)

        # Train ensemble
        logger.info(f"Training {self.ensemble_type} ensemble...")
        self.ensemble_model.fit(X_train_scaled, y_train)

        # Evaluate individual models (if voting ensemble)
        if hasattr(self.ensemble_model, 'estimators_'):
            logger.info("Evaluating individual models...")
            for name, model in zip(
                [name for name, _ in self.ensemble_model.estimators],
                self.ensemble_model.estimators_
            ):
                if hasattr(model, 'score'):
                    score = model.score(X_train_scaled, y_train)
                    self.model_scores[name] = float(score)
                    logger.info(f"  {name}: {score:.4f}")

        # Overall score
        overall_score = self.ensemble_model.score(X_train_scaled, y_train)
        self.model_scores['ensemble'] = float(overall_score)

        self.is_trained = True
        logger.info(f"Ensemble training complete. Score: {overall_score:.4f}")

        return {
            'ensemble_type': self.ensemble_type,
            'n_models': len(self.ensemble_model.estimators_) if hasattr(self.ensemble_model, 'estimators_') else 1,
            'model_scores': self.model_scores,
            'overall_score': overall_score
        }

    def cross_validate(
        self,
        X: np.ndarray,
        y: np.ndarray,
        cv: int = 5
    ) -> Dict[str, Any]:
        """
        Cross-validation evaluation

        Args:
            X: Features
            y: Targets
            cv: Number of folds

        Returns:
            Cross-validation scores
        """
        if self.ensemble_model is None:
            logger.error("Ensemble model not built")
            return {}

        X_scaled = self.scaler.transform(X)

        # Cross-validation
        scores = cross_val_score(
            self.ensemble_model,
            X_scaled,
            y,
            cv=cv,
            scoring='accuracy',
            n_jobs=-1
        )

        return {
            'cv_scores': scores.tolist(),
            'mean_score': float(np.mean(scores)),
            'std_score': float(np.std(scores)),
            'min_score': float(np.min(scores)),
            'max_score': float(np.max(scores))
        }

    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict with ensemble

        Args:
            X: Input features

        Returns:
            Predictions
        """
        if not self.is_trained or self.ensemble_model is None:
            logger.error("Ensemble model not trained")
            return np.array([])

        X_scaled = self.scaler.transform(X)
        predictions = self.ensemble_model.predict(X_scaled)

        return predictions

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """
        Predict probabilities with ensemble

        Args:
            X: Input features

        Returns:
            Class probabilities
        """
        if not self.is_trained or self.ensemble_model is None:
            logger.error("Ensemble model not trained")
            return np.array([])

        if not hasattr(self.ensemble_model, 'predict_proba'):
            logger.error("Ensemble model does not support probability prediction")
            return np.array([])

        X_scaled = self.scaler.transform(X)
        probabilities = self.ensemble_model.predict_proba(X_scaled)

        return probabilities

    def predict_with_confidence(self, X: np.ndarray) -> Dict[str, Any]:
        """
        Predict with confidence estimation

        Args:
            X: Input features

        Returns:
            Predictions with confidence scores
        """
        predictions = self.predict(X)
        probabilities = self.predict_proba(X)

        if len(probabilities) == 0:
            return {
                'predictions': predictions.tolist(),
                'confidence': [0.5] * len(predictions)
            }

        # Confidence = max probability
        confidence = np.max(probabilities, axis=1)

        return {
            'predictions': predictions.tolist(),
            'probabilities': probabilities.tolist(),
            'confidence': confidence.tolist(),
            'mean_confidence': float(np.mean(confidence)),
            'std_confidence': float(np.std(confidence))
        }

    def get_model_diversity(self) -> Dict[str, Any]:
        """
        Analyze diversity of base models

        Returns:
            Diversity metrics
        """
        if not self.is_trained or not hasattr(self.ensemble_model, 'estimators_'):
            logger.error("Cannot compute diversity: model not trained or no base estimators")
            return {}

        # Model scores
        scores = list(self.model_scores.values())

        # Score diversity
        diversity = {
            'n_models': len(scores),
            'mean_score': float(np.mean(scores)),
            'std_score': float(np.std(scores)),
            'min_score': float(np.min(scores)),
            'max_score': float(np.max(scores)),
            'score_range': float(np.max(scores) - np.min(scores)),
            'model_scores': self.model_scores
        }

        return diversity

    def get_feature_importance(self, feature_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get feature importance from ensemble

        Args:
            feature_names: Names of features (optional)

        Returns:
            Feature importance dict
        """
        if not self.is_trained:
            logger.error("Model not trained")
            return {}

        importance_dict = {}

        # Try to get importance from base models
        if hasattr(self.ensemble_model, 'estimators_'):
            for name, model in zip(
                [name for name, _ in self.ensemble_model.estimators],
                self.ensemble_model.estimators_
            ):
                if hasattr(model, 'feature_importances_'):
                    importance = model.feature_importances_
                    importance_dict[name] = importance.tolist()

        # Aggregate importance
        if importance_dict:
            all_importance = np.array(list(importance_dict.values()))
            mean_importance = np.mean(all_importance, axis=0)
            std_importance = np.std(all_importance, axis=0)

            # Create feature importance DataFrame
            n_features = len(mean_importance)
            if feature_names is None:
                feature_names = [f"feature_{i}" for i in range(n_features)]

            importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': mean_importance,
                'std': std_importance
            }).sort_values('importance', ascending=False)

            return {
                'model_importances': importance_dict,
                'mean_importance': mean_importance.tolist(),
                'std_importance': std_importance.tolist(),
                'top_features': importance_df.head(10).to_dict('records')
            }

        return {}

    def save_model(self, path: Optional[str] = None) -> bool:
        """Save ensemble model to file"""
        if self.ensemble_model is None:
            logger.error("No model to save")
            return False

        path = path or self.model_path

        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save model and metadata
            model_data = {
                'ensemble_model': self.ensemble_model,
                'scaler': self.scaler,
                'config': self.config,
                'is_trained': self.is_trained,
                'model_scores': self.model_scores
            }

            with open(path, 'wb') as f:
                pickle.dump(model_data, f)

            logger.info(f"Ensemble model saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving model: {e}")
            return False

    def load_model(self, path: Optional[str] = None) -> bool:
        """Load ensemble model from file"""
        path = path or self.model_path

        try:
            with open(path, 'rb') as f:
                model_data = pickle.load(f)

            self.ensemble_model = model_data['ensemble_model']
            self.scaler = model_data['scaler']
            self.config = model_data.get('config', self.config)
            self.is_trained = model_data.get('is_trained', True)
            self.model_scores = model_data.get('model_scores', {})

            logger.info(f"Ensemble model loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """Get ensemble model information"""
        if self.ensemble_model is None:
            return {
                'available': False,
                'error': 'Ensemble model not built'
            }

        info = {
            'available': True,
            'is_trained': self.is_trained,
            'ensemble_type': self.ensemble_type,
            'voting_type': self.voting_type if self.ensemble_type == 'voting' else None,
            'n_estimators': self.n_estimators
        }

        # Add base models info
        if hasattr(self.ensemble_model, 'estimators_'):
            info['base_models'] = [name for name, _ in self.ensemble_model.estimators]
            info['n_base_models'] = len(self.ensemble_model.estimators_)

        # Add scores
        if self.model_scores:
            info['model_scores'] = self.model_scores

        return info
