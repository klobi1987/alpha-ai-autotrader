"""
Similarity Search for Pattern Matching
Find similar historical patterns using various distance metrics
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sklearn.metrics.pairwise import (
    cosine_similarity,
    euclidean_distances,
    manhattan_distances
)
from sklearn.preprocessing import StandardScaler
from scipy.spatial.distance import cdist
from scipy.stats import pearsonr, spearmanr
import logging

logger = logging.getLogger(__name__)


class SimilaritySearch:
    """
    Similarity Search for Pattern Matching

    Features:
    - Multiple distance metrics (cosine, euclidean, manhattan, correlation)
    - K-nearest neighbors search
    - Pattern matching with confidence scoring
    - Historical pattern lookup
    - Anomaly detection (dissimilarity)
    - Weighted feature similarity
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Similarity Search"""
        self.config = config or {}

        # Search parameters
        self.metric = self.config.get('metric', 'cosine')  # cosine, euclidean, manhattan, correlation
        self.k_neighbors = self.config.get('k_neighbors', 5)
        self.similarity_threshold = self.config.get('similarity_threshold', 0.8)

        # Feature weights (optional)
        self.feature_weights = self.config.get('feature_weights', None)

        # Historical patterns storage
        self.historical_patterns = []
        self.pattern_features = None
        self.scaler = StandardScaler()

    def add_historical_pattern(
        self,
        features: np.ndarray,
        metadata: Dict[str, Any]
    ) -> None:
        """
        Add a historical pattern to the database

        Args:
            features: Feature vector
            metadata: Pattern metadata (timestamp, label, outcome, etc.)
        """
        pattern = {
            'features': features,
            'metadata': metadata,
            'timestamp': metadata.get('timestamp', datetime.now())
        }

        self.historical_patterns.append(pattern)

        logger.debug(f"Historical pattern added. Total patterns: {len(self.historical_patterns)}")

    def build_pattern_database(
        self,
        patterns: List[Dict[str, Any]]
    ) -> None:
        """
        Build pattern database from list of patterns

        Args:
            patterns: List of pattern dicts with 'features' and 'metadata'
        """
        self.historical_patterns = patterns

        # Extract feature matrix
        if self.historical_patterns:
            self.pattern_features = np.array([p['features'] for p in self.historical_patterns])

            # Fit scaler
            self.scaler.fit(self.pattern_features)

        logger.info(f"Pattern database built: {len(self.historical_patterns)} patterns")

    def compute_similarity(
        self,
        query: np.ndarray,
        reference: np.ndarray,
        metric: Optional[str] = None
    ) -> float:
        """
        Compute similarity between query and reference

        Args:
            query: Query feature vector
            reference: Reference feature vector
            metric: Distance metric (default: self.metric)

        Returns:
            Similarity score (higher = more similar)
        """
        metric = metric or self.metric

        # Reshape if needed
        if query.ndim == 1:
            query = query.reshape(1, -1)
        if reference.ndim == 1:
            reference = reference.reshape(1, -1)

        # Apply feature weights if available
        if self.feature_weights is not None:
            query = query * self.feature_weights
            reference = reference * self.feature_weights

        if metric == 'cosine':
            similarity = cosine_similarity(query, reference)[0, 0]
        elif metric == 'euclidean':
            distance = euclidean_distances(query, reference)[0, 0]
            # Convert distance to similarity (0-1 range)
            similarity = 1.0 / (1.0 + distance)
        elif metric == 'manhattan':
            distance = manhattan_distances(query, reference)[0, 0]
            similarity = 1.0 / (1.0 + distance)
        elif metric == 'correlation':
            # Pearson correlation
            if query.size == reference.size:
                similarity, _ = pearsonr(query.flatten(), reference.flatten())
            else:
                similarity = 0.0
        else:
            logger.warning(f"Unknown metric: {metric}, using cosine")
            similarity = cosine_similarity(query, reference)[0, 0]

        return float(similarity)

    def find_similar_patterns(
        self,
        query_features: np.ndarray,
        k: Optional[int] = None,
        threshold: Optional[float] = None,
        return_scores: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Find k most similar patterns to query

        Args:
            query_features: Query feature vector
            k: Number of neighbors to return (default: self.k_neighbors)
            threshold: Minimum similarity threshold (default: self.similarity_threshold)
            return_scores: Whether to include similarity scores

        Returns:
            List of similar patterns with scores
        """
        if not self.historical_patterns:
            logger.warning("No historical patterns in database")
            return []

        k = k or self.k_neighbors
        threshold = threshold or self.similarity_threshold

        # Scale query
        query_scaled = self.scaler.transform(query_features.reshape(1, -1))

        # Compute similarities
        similarities = []
        for i, pattern in enumerate(self.historical_patterns):
            pattern_features = pattern['features'].reshape(1, -1)
            pattern_scaled = self.scaler.transform(pattern_features)

            similarity = self.compute_similarity(query_scaled, pattern_scaled)

            similarities.append({
                'index': i,
                'similarity': similarity,
                'pattern': pattern
            })

        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)

        # Filter by threshold
        similarities = [s for s in similarities if s['similarity'] >= threshold]

        # Take top k
        top_k = similarities[:k]

        # Format results
        results = []
        for item in top_k:
            result = {
                'pattern': item['pattern']['metadata'],
                'features': item['pattern']['features'].tolist()
            }

            if return_scores:
                result['similarity'] = item['similarity']

            results.append(result)

        logger.info(f"Found {len(results)} similar patterns (k={k}, threshold={threshold})")

        return results

    def find_most_similar(
        self,
        query_features: np.ndarray
    ) -> Optional[Dict[str, Any]]:
        """
        Find most similar pattern to query

        Args:
            query_features: Query feature vector

        Returns:
            Most similar pattern or None
        """
        results = self.find_similar_patterns(query_features, k=1, threshold=0.0)

        if results:
            return results[0]
        else:
            return None

    def is_anomaly(
        self,
        query_features: np.ndarray,
        threshold: Optional[float] = None
    ) -> bool:
        """
        Check if query is an anomaly (dissimilar to all patterns)

        Args:
            query_features: Query feature vector
            threshold: Maximum similarity threshold for anomaly (default: 0.3)

        Returns:
            True if anomaly, False otherwise
        """
        threshold = threshold or 0.3

        most_similar = self.find_most_similar(query_features)

        if most_similar is None:
            return True

        return most_similar['similarity'] < threshold

    def get_pattern_neighborhood(
        self,
        pattern_index: int,
        k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get k nearest neighbors of a pattern in the database

        Args:
            pattern_index: Index of pattern in database
            k: Number of neighbors (default: self.k_neighbors)

        Returns:
            List of neighboring patterns
        """
        if pattern_index < 0 or pattern_index >= len(self.historical_patterns):
            logger.error(f"Invalid pattern index: {pattern_index}")
            return []

        pattern = self.historical_patterns[pattern_index]
        query_features = pattern['features']

        # Find similar (excluding the pattern itself)
        all_similar = self.find_similar_patterns(query_features, k=k + 1, threshold=0.0)

        # Remove the pattern itself (should be first with similarity=1.0)
        neighbors = [s for s in all_similar if s['similarity'] < 0.999]

        return neighbors[:k or self.k_neighbors]

    def cluster_similar_patterns(
        self,
        similarity_threshold: float = 0.9
    ) -> List[List[int]]:
        """
        Cluster patterns by similarity

        Args:
            similarity_threshold: Minimum similarity for same cluster

        Returns:
            List of clusters (each cluster is a list of pattern indices)
        """
        if not self.historical_patterns:
            return []

        n_patterns = len(self.historical_patterns)
        visited = [False] * n_patterns
        clusters = []

        for i in range(n_patterns):
            if visited[i]:
                continue

            # Start new cluster
            cluster = [i]
            visited[i] = True

            # Find similar patterns
            pattern_features = self.historical_patterns[i]['features']
            similar = self.find_similar_patterns(
                pattern_features,
                k=n_patterns,
                threshold=similarity_threshold,
                return_scores=False
            )

            # Add to cluster
            for sim_pattern in similar:
                # Find index in historical_patterns
                for j, p in enumerate(self.historical_patterns):
                    if not visited[j] and np.array_equal(p['features'], sim_pattern['features']):
                        cluster.append(j)
                        visited[j] = True
                        break

            clusters.append(cluster)

        logger.info(f"Clustered {n_patterns} patterns into {len(clusters)} clusters")

        return clusters

    def get_pattern_statistics(
        self,
        pattern_indices: List[int]
    ) -> Dict[str, Any]:
        """
        Get statistics for a group of patterns

        Args:
            pattern_indices: List of pattern indices

        Returns:
            Pattern statistics
        """
        if not pattern_indices:
            return {}

        patterns = [self.historical_patterns[i] for i in pattern_indices if i < len(self.historical_patterns)]

        # Extract metadata statistics
        success_rates = [p['metadata'].get('success_rate', 0) for p in patterns if 'success_rate' in p['metadata']]
        returns = [p['metadata'].get('return', 0) for p in patterns if 'return' in p['metadata']]

        stats = {
            'n_patterns': len(patterns),
            'avg_success_rate': float(np.mean(success_rates)) if success_rates else None,
            'avg_return': float(np.mean(returns)) if returns else None,
            'std_success_rate': float(np.std(success_rates)) if success_rates else None,
            'std_return': float(np.std(returns)) if returns else None
        }

        return stats

    def predict_from_similar(
        self,
        query_features: np.ndarray,
        k: Optional[int] = None,
        weighted: bool = True
    ) -> Dict[str, Any]:
        """
        Predict outcome based on similar patterns

        Args:
            query_features: Query feature vector
            k: Number of similar patterns to use (default: self.k_neighbors)
            weighted: Whether to weight by similarity (default: True)

        Returns:
            Prediction results
        """
        similar_patterns = self.find_similar_patterns(query_features, k=k)

        if not similar_patterns:
            return {
                'prediction': None,
                'confidence': 0.0,
                'n_similar': 0
            }

        # Extract outcomes
        outcomes = []
        weights = []

        for pattern in similar_patterns:
            metadata = pattern['pattern']
            outcome = metadata.get('outcome', None)  # 1 = success, 0 = failure
            similarity = pattern.get('similarity', 1.0)

            if outcome is not None:
                outcomes.append(outcome)
                weights.append(similarity if weighted else 1.0)

        if not outcomes:
            return {
                'prediction': None,
                'confidence': 0.0,
                'n_similar': len(similar_patterns)
            }

        # Weighted average
        weights = np.array(weights)
        weights = weights / weights.sum()  # Normalize

        prediction = np.average(outcomes, weights=weights)

        # Confidence = average similarity of patterns used
        confidence = float(np.mean([p['similarity'] for p in similar_patterns]))

        return {
            'prediction': float(prediction),
            'confidence': confidence,
            'n_similar': len(outcomes),
            'similar_patterns': similar_patterns[:3]  # Top 3
        }

    def get_search_info(self) -> Dict[str, Any]:
        """Get similarity search information"""
        return {
            'metric': self.metric,
            'k_neighbors': self.k_neighbors,
            'similarity_threshold': self.similarity_threshold,
            'n_historical_patterns': len(self.historical_patterns),
            'feature_weights_enabled': self.feature_weights is not None,
            'supported_metrics': ['cosine', 'euclidean', 'manhattan', 'correlation']
        }
