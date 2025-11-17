"""
Feature Selection for ML Pattern Discovery
Automatically selects best features for pattern recognition
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_selection import (
    SelectKBest, SelectPercentile,
    f_classif, mutual_info_classif, chi2,
    RFE, RFECV,
    VarianceThreshold
)
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from scipy.stats import pearsonr, spearmanr
import logging
import pickle
import os

logger = logging.getLogger(__name__)


class FeatureSelector:
    """
    Feature Selection for Pattern Discovery

    Features:
    - SelectKBest (Mutual Information, F-classif, Chi2)
    - RFE (Recursive Feature Elimination)
    - RFECV (with cross-validation)
    - Variance Threshold
    - Correlation analysis
    - Feature importance ranking
    - Feature redundancy detection
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Feature Selector"""
        self.config = config or {}

        # Selection method
        self.method = self.config.get('method', 'mutual_info')  # mutual_info, f_classif, rfe, rfecv
        self.k_features = self.config.get('k_features', 10)
        self.percentile = self.config.get('percentile', 50)

        # Thresholds
        self.variance_threshold = self.config.get('variance_threshold', 0.01)
        self.correlation_threshold = self.config.get('correlation_threshold', 0.95)

        # Models
        self.selector = None
        self.scaler = StandardScaler()

        # Selected features
        self.selected_features = []
        self.feature_scores = {}
        self.feature_names = []

        # Model path
        self.model_path = self.config.get('model_path', 'models/feature_selector.pkl')

    def fit(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Fit feature selector

        Args:
            X: Feature matrix
            y: Target vector
            feature_names: Names of features (optional)

        Returns:
            Selection results
        """
        n_features = X.shape[1]

        if feature_names is None:
            feature_names = [f"feature_{i}" for i in range(n_features)]

        self.feature_names = feature_names

        # Scale features
        X_scaled = self.scaler.fit_transform(X)

        # Select features based on method
        if self.method == 'mutual_info':
            result = self._select_mutual_info(X_scaled, y)
        elif self.method == 'f_classif':
            result = self._select_f_classif(X_scaled, y)
        elif self.method == 'chi2':
            result = self._select_chi2(X, y)  # Chi2 requires non-negative features
        elif self.method == 'rfe':
            result = self._select_rfe(X_scaled, y)
        elif self.method == 'rfecv':
            result = self._select_rfecv(X_scaled, y)
        elif self.method == 'variance':
            result = self._select_variance(X_scaled)
        else:
            logger.warning(f"Unknown method: {self.method}, using mutual_info")
            result = self._select_mutual_info(X_scaled, y)

        # Store selected features
        self.selected_features = [
            feature_names[i] for i in range(n_features)
            if self.selector.get_support()[i]
        ]

        result['selected_features'] = self.selected_features
        result['n_selected'] = len(self.selected_features)
        result['n_total'] = n_features

        logger.info(f"Feature selection complete: {len(self.selected_features)}/{n_features} features selected")

        return result

    def _select_mutual_info(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Select features using mutual information"""
        self.selector = SelectKBest(
            score_func=mutual_info_classif,
            k=min(self.k_features, X.shape[1])
        )
        self.selector.fit(X, y)

        # Store scores
        scores = self.selector.scores_
        for i, name in enumerate(self.feature_names):
            self.feature_scores[name] = float(scores[i])

        return {
            'method': 'mutual_info',
            'scores': scores.tolist(),
            'feature_scores': self.feature_scores
        }

    def _select_f_classif(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Select features using F-classif (ANOVA F-value)"""
        self.selector = SelectKBest(
            score_func=f_classif,
            k=min(self.k_features, X.shape[1])
        )
        self.selector.fit(X, y)

        # Store scores
        scores = self.selector.scores_
        for i, name in enumerate(self.feature_names):
            self.feature_scores[name] = float(scores[i])

        return {
            'method': 'f_classif',
            'scores': scores.tolist(),
            'feature_scores': self.feature_scores
        }

    def _select_chi2(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Select features using Chi-squared test"""
        # Make features non-negative
        X_positive = X - X.min(axis=0)

        self.selector = SelectKBest(
            score_func=chi2,
            k=min(self.k_features, X.shape[1])
        )
        self.selector.fit(X_positive, y)

        # Store scores
        scores = self.selector.scores_
        for i, name in enumerate(self.feature_names):
            self.feature_scores[name] = float(scores[i])

        return {
            'method': 'chi2',
            'scores': scores.tolist(),
            'feature_scores': self.feature_scores
        }

    def _select_rfe(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Select features using Recursive Feature Elimination"""
        # Base estimator
        estimator = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        self.selector = RFE(
            estimator=estimator,
            n_features_to_select=min(self.k_features, X.shape[1]),
            step=1
        )
        self.selector.fit(X, y)

        # Store ranking
        ranking = self.selector.ranking_
        for i, name in enumerate(self.feature_names):
            self.feature_scores[name] = float(1.0 / ranking[i])  # Inverse ranking as score

        return {
            'method': 'rfe',
            'ranking': ranking.tolist(),
            'feature_scores': self.feature_scores
        }

    def _select_rfecv(self, X: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
        """Select features using RFE with cross-validation"""
        # Base estimator
        estimator = RandomForestClassifier(
            n_estimators=50,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )

        self.selector = RFECV(
            estimator=estimator,
            step=1,
            cv=5,
            scoring='accuracy',
            n_jobs=-1
        )
        self.selector.fit(X, y)

        # Store ranking
        ranking = self.selector.ranking_
        for i, name in enumerate(self.feature_names):
            self.feature_scores[name] = float(1.0 / ranking[i])

        return {
            'method': 'rfecv',
            'ranking': ranking.tolist(),
            'n_features': self.selector.n_features_,
            'cv_scores': self.selector.cv_results_['mean_test_score'].tolist(),
            'feature_scores': self.feature_scores
        }

    def _select_variance(self, X: np.ndarray) -> Dict[str, Any]:
        """Select features using variance threshold"""
        self.selector = VarianceThreshold(threshold=self.variance_threshold)
        self.selector.fit(X)

        # Store variances
        variances = self.selector.variances_
        for i, name in enumerate(self.feature_names):
            self.feature_scores[name] = float(variances[i])

        return {
            'method': 'variance',
            'variances': variances.tolist(),
            'feature_scores': self.feature_scores
        }

    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        Transform features using fitted selector

        Args:
            X: Feature matrix

        Returns:
            Selected features
        """
        if self.selector is None:
            logger.error("Feature selector not fitted")
            return X

        X_scaled = self.scaler.transform(X)
        X_selected = self.selector.transform(X_scaled)

        return X_selected

    def fit_transform(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """
        Fit selector and transform features

        Args:
            X: Feature matrix
            y: Target vector
            feature_names: Names of features (optional)

        Returns:
            X_selected: Selected features
            result: Selection results
        """
        result = self.fit(X, y, feature_names)
        X_selected = self.transform(X)

        return X_selected, result

    def get_top_features(self, k: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get top k features by score

        Args:
            k: Number of top features (default: all selected)

        Returns:
            List of feature dicts with name and score
        """
        if not self.feature_scores:
            logger.warning("No feature scores available")
            return []

        # Sort by score
        sorted_features = sorted(
            self.feature_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        k = k or len(sorted_features)
        top_features = [
            {'name': name, 'score': score}
            for name, score in sorted_features[:k]
        ]

        return top_features

    def analyze_correlation(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze feature correlation

        Args:
            X: Feature matrix
            feature_names: Names of features (optional)

        Returns:
            Correlation analysis results
        """
        if feature_names is None:
            feature_names = self.feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Compute correlation matrix
        df = pd.DataFrame(X, columns=feature_names)
        corr_matrix = df.corr()

        # Find highly correlated pairs
        high_corr_pairs = []
        n_features = len(feature_names)

        for i in range(n_features):
            for j in range(i + 1, n_features):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > self.correlation_threshold:
                    high_corr_pairs.append({
                        'feature1': feature_names[i],
                        'feature2': feature_names[j],
                        'correlation': float(corr_value)
                    })

        # Identify redundant features
        redundant_features = set()
        for pair in high_corr_pairs:
            # Keep feature with higher score (if available)
            feat1 = pair['feature1']
            feat2 = pair['feature2']

            score1 = self.feature_scores.get(feat1, 0)
            score2 = self.feature_scores.get(feat2, 0)

            if score1 > score2:
                redundant_features.add(feat2)
            else:
                redundant_features.add(feat1)

        return {
            'correlation_matrix': corr_matrix.values.tolist(),
            'feature_names': feature_names,
            'high_correlation_pairs': high_corr_pairs,
            'n_high_corr_pairs': len(high_corr_pairs),
            'redundant_features': list(redundant_features),
            'n_redundant': len(redundant_features)
        }

    def remove_redundant_features(
        self,
        X: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> Tuple[np.ndarray, List[str]]:
        """
        Remove redundant (highly correlated) features

        Args:
            X: Feature matrix
            feature_names: Names of features (optional)

        Returns:
            X_reduced: Feature matrix without redundant features
            kept_features: Names of kept features
        """
        corr_analysis = self.analyze_correlation(X, feature_names)
        redundant = set(corr_analysis['redundant_features'])

        if feature_names is None:
            feature_names = self.feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Keep non-redundant features
        keep_indices = [
            i for i, name in enumerate(feature_names)
            if name not in redundant
        ]

        X_reduced = X[:, keep_indices]
        kept_features = [feature_names[i] for i in keep_indices]

        logger.info(f"Removed {len(redundant)} redundant features, kept {len(kept_features)}")

        return X_reduced, kept_features

    def get_feature_importance_from_model(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get feature importance using Random Forest

        Args:
            X: Feature matrix
            y: Target vector
            feature_names: Names of features (optional)

        Returns:
            Feature importance list
        """
        if feature_names is None:
            feature_names = self.feature_names or [f"feature_{i}" for i in range(X.shape[1])]

        # Train Random Forest
        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        rf.fit(X, y)

        # Get importance
        importance = rf.feature_importances_

        # Create importance list
        importance_list = [
            {'name': name, 'importance': float(imp)}
            for name, imp in zip(feature_names, importance)
        ]

        # Sort by importance
        importance_list.sort(key=lambda x: x['importance'], reverse=True)

        return importance_list

    def save_selector(self, path: Optional[str] = None) -> bool:
        """Save feature selector to file"""
        if self.selector is None:
            logger.error("No selector to save")
            return False

        path = path or self.model_path

        try:
            # Create directory if needed
            os.makedirs(os.path.dirname(path), exist_ok=True)

            # Save selector and metadata
            selector_data = {
                'selector': self.selector,
                'scaler': self.scaler,
                'config': self.config,
                'selected_features': self.selected_features,
                'feature_scores': self.feature_scores,
                'feature_names': self.feature_names
            }

            with open(path, 'wb') as f:
                pickle.dump(selector_data, f)

            logger.info(f"Feature selector saved to {path}")
            return True

        except Exception as e:
            logger.error(f"Error saving selector: {e}")
            return False

    def load_selector(self, path: Optional[str] = None) -> bool:
        """Load feature selector from file"""
        path = path or self.model_path

        try:
            with open(path, 'rb') as f:
                selector_data = pickle.load(f)

            self.selector = selector_data['selector']
            self.scaler = selector_data['scaler']
            self.config = selector_data.get('config', self.config)
            self.selected_features = selector_data.get('selected_features', [])
            self.feature_scores = selector_data.get('feature_scores', {})
            self.feature_names = selector_data.get('feature_names', [])

            logger.info(f"Feature selector loaded from {path}")
            return True

        except Exception as e:
            logger.error(f"Error loading selector: {e}")
            return False

    def get_selector_info(self) -> Dict[str, Any]:
        """Get feature selector information"""
        if self.selector is None:
            return {
                'available': False,
                'error': 'Feature selector not fitted'
            }

        return {
            'available': True,
            'method': self.method,
            'n_features_total': len(self.feature_names),
            'n_features_selected': len(self.selected_features),
            'selected_features': self.selected_features,
            'top_features': self.get_top_features(k=10),
            'feature_scores': self.feature_scores
        }
