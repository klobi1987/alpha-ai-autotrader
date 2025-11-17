"""
Pattern Visualization for ML Discovery
Generate charts and visualizations for discovered patterns
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
import os
import base64
from io import BytesIO

logger = logging.getLogger(__name__)

# Try to import plotting libraries (optional)
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib/Seaborn not available. Visualization features will be limited.")
    PLOTTING_AVAILABLE = False


class PatternVisualizer:
    """
    Pattern Visualization System

    Features:
    - Pattern cluster visualization
    - Performance charts
    - Feature importance plots
    - Pattern comparison
    - Heatmaps
    - Time series plots
    - Export to image/JSON
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Pattern Visualizer"""
        self.config = config or {}

        # Visualization settings
        self.figsize = self.config.get('figsize', (12, 8))
        self.dpi = self.config.get('dpi', 100)
        self.style = self.config.get('style', 'seaborn-v0_8-darkgrid')

        # Colors
        self.colors = self.config.get('colors', {
            'success': '#2ecc71',
            'failure': '#e74c3c',
            'neutral': '#95a5a6',
            'primary': '#3498db',
            'secondary': '#9b59b6'
        })

        # Output path
        self.output_path = self.config.get('output_path', 'static/charts')

        # Set style
        if PLOTTING_AVAILABLE:
            try:
                plt.style.use(self.style)
            except:
                logger.warning(f"Style '{self.style}' not available, using default")

    def plot_pattern_clusters(
        self,
        patterns: List[Dict[str, Any]],
        features_2d: Optional[np.ndarray] = None,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Visualize pattern clusters in 2D space

        Args:
            patterns: List of pattern dictionaries
            features_2d: 2D projection of features (e.g., from PCA)
            save_path: Path to save image (optional)

        Returns:
            Visualization result
        """
        if not PLOTTING_AVAILABLE:
            logger.error("Plotting library not available")
            return {}

        if features_2d is None or len(features_2d) != len(patterns):
            logger.error("Invalid features_2d provided")
            return {}

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Extract pattern data
        x = features_2d[:, 0]
        y = features_2d[:, 1]
        success_rates = [p.get('success_rate', 0.5) for p in patterns]
        labels = [p.get('label', f"P{i}") for i, p in enumerate(patterns)]

        # Color by success rate
        colors = [self.colors['success'] if sr > 0.6 else self.colors['failure'] if sr < 0.4 else self.colors['neutral'] for sr in success_rates]

        # Scatter plot
        scatter = ax.scatter(x, y, c=success_rates, s=200, alpha=0.6, cmap='RdYlGn', vmin=0, vmax=1)

        # Add labels
        for i, label in enumerate(labels):
            ax.annotate(label, (x[i], y[i]), fontsize=8, ha='center')

        # Colorbar
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Success Rate', rotation=270, labelpad=20)

        ax.set_xlabel('Component 1')
        ax.set_ylabel('Component 2')
        ax.set_title('Pattern Clusters (2D Projection)')
        ax.grid(True, alpha=0.3)

        # Save or return
        result = self._save_or_encode_figure(fig, save_path)
        plt.close(fig)

        return result

    def plot_pattern_performance(
        self,
        patterns: List[Dict[str, Any]],
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plot pattern performance comparison

        Args:
            patterns: List of pattern dictionaries
            save_path: Path to save image (optional)

        Returns:
            Visualization result
        """
        if not PLOTTING_AVAILABLE:
            logger.error("Plotting library not available")
            return {}

        # Sort patterns by success rate
        patterns = sorted(patterns, key=lambda p: p.get('success_rate', 0), reverse=True)

        # Take top 20
        patterns = patterns[:20]

        labels = [p.get('label', f"P{i}") for i, p in enumerate(patterns)]
        success_rates = [p.get('success_rate', 0) * 100 for p in patterns]
        avg_returns = [p.get('avg_return', 0) for p in patterns]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8), dpi=self.dpi)

        # Success rate bar chart
        colors_sr = [self.colors['success'] if sr > 60 else self.colors['failure'] if sr < 40 else self.colors['neutral'] for sr in success_rates]
        ax1.barh(labels, success_rates, color=colors_sr, alpha=0.7)
        ax1.set_xlabel('Success Rate (%)')
        ax1.set_title('Pattern Success Rates')
        ax1.axvline(x=50, color='gray', linestyle='--', alpha=0.5)
        ax1.grid(True, alpha=0.3)

        # Average return bar chart
        colors_ret = [self.colors['success'] if ret > 0 else self.colors['failure'] for ret in avg_returns]
        ax2.barh(labels, avg_returns, color=colors_ret, alpha=0.7)
        ax2.set_xlabel('Average Return (%)')
        ax2.set_title('Pattern Average Returns')
        ax2.axvline(x=0, color='gray', linestyle='--', alpha=0.5)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        result = self._save_or_encode_figure(fig, save_path)
        plt.close(fig)

        return result

    def plot_feature_importance(
        self,
        feature_importance: List[Dict[str, Any]],
        top_k: int = 15,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plot feature importance

        Args:
            feature_importance: List of dicts with 'name' and 'importance'
            top_k: Number of top features to show
            save_path: Path to save image (optional)

        Returns:
            Visualization result
        """
        if not PLOTTING_AVAILABLE:
            logger.error("Plotting library not available")
            return {}

        # Sort and take top k
        feature_importance = sorted(feature_importance, key=lambda x: x['importance'], reverse=True)[:top_k]

        names = [f['name'] for f in feature_importance]
        importance = [f['importance'] for f in feature_importance]

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        ax.barh(names, importance, color=self.colors['primary'], alpha=0.7)
        ax.set_xlabel('Importance')
        ax.set_title(f'Top {top_k} Feature Importance')
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        result = self._save_or_encode_figure(fig, save_path)
        plt.close(fig)

        return result

    def plot_correlation_heatmap(
        self,
        correlation_matrix: np.ndarray,
        feature_names: List[str],
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plot correlation heatmap

        Args:
            correlation_matrix: Correlation matrix
            feature_names: Feature names
            save_path: Path to save image (optional)

        Returns:
            Visualization result
        """
        if not PLOTTING_AVAILABLE:
            logger.error("Plotting library not available")
            return {}

        fig, ax = plt.subplots(figsize=(14, 12), dpi=self.dpi)

        # Heatmap
        sns.heatmap(
            correlation_matrix,
            xticklabels=feature_names,
            yticklabels=feature_names,
            cmap='coolwarm',
            center=0,
            annot=False,
            fmt='.2f',
            square=True,
            linewidths=0.5,
            cbar_kws={'shrink': 0.8},
            ax=ax
        )

        ax.set_title('Feature Correlation Heatmap')
        plt.tight_layout()

        result = self._save_or_encode_figure(fig, save_path)
        plt.close(fig)

        return result

    def plot_pattern_timeline(
        self,
        pattern_history: List[Dict[str, Any]],
        metric: str = 'success_rate',
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plot pattern performance over time

        Args:
            pattern_history: List of pattern performance records with timestamps
            metric: Metric to plot ('success_rate', 'avg_return', 'confidence')
            save_path: Path to save image (optional)

        Returns:
            Visualization result
        """
        if not PLOTTING_AVAILABLE:
            logger.error("Plotting library not available")
            return {}

        # Convert to DataFrame
        df = pd.DataFrame(pattern_history)

        if 'timestamp' not in df.columns or metric not in df.columns:
            logger.error(f"Missing required columns: timestamp or {metric}")
            return {}

        # Parse timestamps
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp')

        fig, ax = plt.subplots(figsize=self.figsize, dpi=self.dpi)

        # Plot each pattern
        for pattern_label in df['label'].unique():
            pattern_df = df[df['label'] == pattern_label]
            ax.plot(pattern_df['timestamp'], pattern_df[metric], marker='o', label=pattern_label, alpha=0.7)

        ax.set_xlabel('Time')
        ax.set_ylabel(metric.replace('_', ' ').title())
        ax.set_title(f'Pattern {metric.replace("_", " ").title()} Over Time')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        result = self._save_or_encode_figure(fig, save_path)
        plt.close(fig)

        return result

    def plot_model_comparison(
        self,
        model_results: List[Dict[str, Any]],
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Plot model comparison (e.g., from hyperparameter tuning)

        Args:
            model_results: List of model results with 'model_name' and 'best_score'
            save_path: Path to save image (optional)

        Returns:
            Visualization result
        """
        if not PLOTTING_AVAILABLE:
            logger.error("Plotting library not available")
            return {}

        model_names = [r['model_name'] for r in model_results]
        scores = [r['best_score'] for r in model_results]

        fig, ax = plt.subplots(figsize=(10, 6), dpi=self.dpi)

        colors_model = [self.colors['success'] if s > 0.6 else self.colors['neutral'] for s in scores]
        ax.bar(model_names, scores, color=colors_model, alpha=0.7)
        ax.set_ylabel('Best Score')
        ax.set_title('Model Comparison')
        ax.set_ylim(0, 1)
        ax.grid(True, alpha=0.3, axis='y')

        # Add value labels
        for i, (name, score) in enumerate(zip(model_names, scores)):
            ax.text(i, score + 0.02, f'{score:.3f}', ha='center', fontsize=10)

        plt.tight_layout()

        result = self._save_or_encode_figure(fig, save_path)
        plt.close(fig)

        return result

    def create_pattern_summary(
        self,
        pattern: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create summary visualization data for a single pattern

        Args:
            pattern: Pattern dictionary

        Returns:
            Summary data for visualization
        """
        return {
            'label': pattern.get('label', 'Unknown'),
            'success_rate': pattern.get('success_rate', 0),
            'avg_return': pattern.get('avg_return', 0),
            'confidence': pattern.get('confidence', 0),
            'trade_count': pattern.get('trade_count', 0),
            'win_count': pattern.get('win_count', 0),
            'loss_count': pattern.get('loss_count', 0),
            'last_seen': pattern.get('last_seen', datetime.now()).isoformat() if isinstance(pattern.get('last_seen'), datetime) else pattern.get('last_seen')
        }

    def _save_or_encode_figure(
        self,
        fig,
        save_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save figure to file or encode as base64

        Args:
            fig: Matplotlib figure
            save_path: Path to save (optional)

        Returns:
            Result dict with path or base64 data
        """
        if save_path:
            # Create directory if needed
            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Save figure
            fig.savefig(save_path, dpi=self.dpi, bbox_inches='tight')

            return {
                'type': 'file',
                'path': save_path,
                'url': f"/{save_path}"  # Relative URL
            }
        else:
            # Encode as base64
            buffer = BytesIO()
            fig.savefig(buffer, format='png', dpi=self.dpi, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()

            return {
                'type': 'base64',
                'data': f"data:image/png;base64,{image_base64}"
            }

    def generate_dashboard_data(
        self,
        patterns: List[Dict[str, Any]],
        performance_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Generate visualization data for dashboard

        Args:
            patterns: List of patterns
            performance_history: Performance history (optional)

        Returns:
            Dashboard visualization data
        """
        # Summary statistics
        success_rates = [p.get('success_rate', 0) for p in patterns]
        avg_returns = [p.get('avg_return', 0) for p in patterns]

        # Top patterns
        top_patterns = sorted(patterns, key=lambda p: p.get('success_rate', 0), reverse=True)[:10]

        # Performance distribution
        success_distribution = {
            'excellent': sum(1 for sr in success_rates if sr >= 0.7),
            'good': sum(1 for sr in success_rates if 0.6 <= sr < 0.7),
            'fair': sum(1 for sr in success_rates if 0.5 <= sr < 0.6),
            'poor': sum(1 for sr in success_rates if sr < 0.5)
        }

        dashboard_data = {
            'summary': {
                'total_patterns': len(patterns),
                'avg_success_rate': float(np.mean(success_rates)) if success_rates else 0.0,
                'avg_return': float(np.mean(avg_returns)) if avg_returns else 0.0,
                'best_success_rate': float(max(success_rates)) if success_rates else 0.0,
                'worst_success_rate': float(min(success_rates)) if success_rates else 0.0
            },
            'top_patterns': [self.create_pattern_summary(p) for p in top_patterns],
            'distribution': success_distribution,
            'charts_available': PLOTTING_AVAILABLE
        }

        # Add performance history if available
        if performance_history:
            dashboard_data['performance_history'] = performance_history

        return dashboard_data

    def get_visualizer_info(self) -> Dict[str, Any]:
        """Get visualizer information"""
        return {
            'plotting_available': PLOTTING_AVAILABLE,
            'figsize': self.figsize,
            'dpi': self.dpi,
            'style': self.style,
            'output_path': self.output_path,
            'supported_plots': [
                'pattern_clusters',
                'pattern_performance',
                'feature_importance',
                'correlation_heatmap',
                'pattern_timeline',
                'model_comparison'
            ]
        }
