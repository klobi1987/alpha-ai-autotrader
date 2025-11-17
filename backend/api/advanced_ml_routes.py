"""
Advanced ML API Routes
API endpoints for all 8 advanced ML features
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
import logging

# Import all ML modules
from backend.ml.lstm_network import LSTMNetwork, KERAS_AVAILABLE
from backend.ml.ensemble_methods import EnsembleMethods
from backend.ml.feature_selector import FeatureSelector
from backend.ml.hyperparameter_tuner import HyperparameterTuner
from backend.ml.online_learner import OnlineLearner
from backend.ml.pattern_visualizer import PatternVisualizer, PLOTTING_AVAILABLE
from backend.ml.similarity_search import SimilaritySearch
from backend.ml.multi_timeframe import MultiTimeframeAnalyzer, Timeframe

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/advanced-ml", tags=["advanced-ml"])

# Global instances (singleton pattern)
_lstm_network = None
_ensemble_methods = None
_feature_selector = None
_hyperparameter_tuner = None
_online_learner = None
_pattern_visualizer = None
_similarity_search = None
_multi_timeframe_analyzer = None


def get_lstm_network() -> LSTMNetwork:
    """Get or create LSTM network instance"""
    global _lstm_network
    if _lstm_network is None:
        _lstm_network = LSTMNetwork()
    return _lstm_network


def get_ensemble_methods() -> EnsembleMethods:
    """Get or create ensemble methods instance"""
    global _ensemble_methods
    if _ensemble_methods is None:
        _ensemble_methods = EnsembleMethods()
    return _ensemble_methods


def get_feature_selector() -> FeatureSelector:
    """Get or create feature selector instance"""
    global _feature_selector
    if _feature_selector is None:
        _feature_selector = FeatureSelector()
    return _feature_selector


def get_hyperparameter_tuner() -> HyperparameterTuner:
    """Get or create hyperparameter tuner instance"""
    global _hyperparameter_tuner
    if _hyperparameter_tuner is None:
        _hyperparameter_tuner = HyperparameterTuner()
    return _hyperparameter_tuner


def get_online_learner() -> OnlineLearner:
    """Get or create online learner instance"""
    global _online_learner
    if _online_learner is None:
        _online_learner = OnlineLearner()
    return _online_learner


def get_pattern_visualizer() -> PatternVisualizer:
    """Get or create pattern visualizer instance"""
    global _pattern_visualizer
    if _pattern_visualizer is None:
        _pattern_visualizer = PatternVisualizer()
    return _pattern_visualizer


def get_similarity_search() -> SimilaritySearch:
    """Get or create similarity search instance"""
    global _similarity_search
    if _similarity_search is None:
        _similarity_search = SimilaritySearch()
    return _similarity_search


def get_multi_timeframe_analyzer() -> MultiTimeframeAnalyzer:
    """Get or create multi-timeframe analyzer instance"""
    global _multi_timeframe_analyzer
    if _multi_timeframe_analyzer is None:
        _multi_timeframe_analyzer = MultiTimeframeAnalyzer()
    return _multi_timeframe_analyzer


# ===== LSTM Neural Network Endpoints =====

@router.get("/lstm/info")
async def lstm_info():
    """Get LSTM network information"""
    try:
        lstm = get_lstm_network()
        info = lstm.get_model_info()
        info['keras_available'] = KERAS_AVAILABLE
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting LSTM info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lstm/predict")
async def lstm_predict(sequence: List[List[float]]):
    """Predict with LSTM network"""
    try:
        lstm = get_lstm_network()

        if not KERAS_AVAILABLE:
            raise HTTPException(status_code=400, detail="Keras not available")

        # Convert to numpy array
        X = np.array(sequence)

        # Predict
        result = lstm.predict(X, return_confidence=True)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error in LSTM prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/lstm/forecast")
async def lstm_forecast(sequence: List[List[float]], n_steps: int = 10):
    """Multi-step ahead forecasting with LSTM"""
    try:
        lstm = get_lstm_network()

        if not KERAS_AVAILABLE:
            raise HTTPException(status_code=400, detail="Keras not available")

        # Convert to numpy array
        initial_sequence = np.array(sequence)

        # Forecast
        forecasts = lstm.forecast_multi_step(initial_sequence, n_steps=n_steps)

        return {
            "success": True,
            "data": {
                "forecasts": forecasts.tolist(),
                "n_steps": n_steps
            }
        }
    except Exception as e:
        logger.error(f"Error in LSTM forecast: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Ensemble Methods Endpoints =====

@router.get("/ensemble/info")
async def ensemble_info():
    """Get ensemble methods information"""
    try:
        ensemble = get_ensemble_methods()
        info = ensemble.get_model_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting ensemble info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ensemble/predict")
async def ensemble_predict(features: List[List[float]]):
    """Predict with ensemble model"""
    try:
        ensemble = get_ensemble_methods()

        if not ensemble.is_trained:
            raise HTTPException(status_code=400, detail="Ensemble model not trained")

        # Convert to numpy array
        X = np.array(features)

        # Predict
        result = ensemble.predict_with_confidence(X)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error in ensemble prediction: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Feature Selection Endpoints =====

@router.get("/features/info")
async def feature_selection_info():
    """Get feature selector information"""
    try:
        selector = get_feature_selector()
        info = selector.get_selector_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting feature selector info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/features/top")
async def get_top_features(k: int = 10):
    """Get top k features by score"""
    try:
        selector = get_feature_selector()
        top_features = selector.get_top_features(k=k)
        return {"success": True, "data": top_features}
    except Exception as e:
        logger.error(f"Error getting top features: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Hyperparameter Tuning Endpoints =====

@router.get("/tuning/info")
async def tuning_info():
    """Get hyperparameter tuner information"""
    try:
        tuner = get_hyperparameter_tuner()
        info = tuner.get_tuner_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting tuner info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tuning/history")
async def tuning_history():
    """Get tuning history"""
    try:
        tuner = get_hyperparameter_tuner()
        return {
            "success": True,
            "data": {
                "history": tuner.tuning_history,
                "n_runs": len(tuner.tuning_history)
            }
        }
    except Exception as e:
        logger.error(f"Error getting tuning history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Online Learning Endpoints =====

@router.get("/online/info")
async def online_learning_info():
    """Get online learner information"""
    try:
        learner = get_online_learner()
        info = learner.get_learner_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting online learner info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/online/add-sample")
async def add_online_sample(features: List[float], label: int, metadata: Optional[Dict[str, Any]] = None):
    """Add a sample to online learner buffer"""
    try:
        learner = get_online_learner()

        # Convert to numpy array
        X = np.array(features)

        # Add sample
        learner.add_sample(X, label, metadata)

        return {
            "success": True,
            "data": {
                "buffer_size": len(learner.sample_buffer),
                "should_update": learner.should_update()
            }
        }
    except Exception as e:
        logger.error(f"Error adding sample: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/online/update")
async def update_online_model(background_tasks: BackgroundTasks):
    """Update online learning model"""
    try:
        learner = get_online_learner()

        if not learner.is_initialized:
            raise HTTPException(status_code=400, detail="Online learner not initialized")

        # Update model
        result = learner.update_model()

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error updating online model: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/online/performance")
async def online_performance():
    """Get online learner performance statistics"""
    try:
        learner = get_online_learner()
        stats = learner.get_performance_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Error getting online performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Pattern Visualization Endpoints =====

@router.get("/visualization/info")
async def visualization_info():
    """Get pattern visualizer information"""
    try:
        visualizer = get_pattern_visualizer()
        info = visualizer.get_visualizer_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting visualizer info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/visualization/dashboard-data")
async def generate_dashboard_data(patterns: List[Dict[str, Any]]):
    """Generate dashboard visualization data"""
    try:
        visualizer = get_pattern_visualizer()
        dashboard_data = visualizer.generate_dashboard_data(patterns)
        return {"success": True, "data": dashboard_data}
    except Exception as e:
        logger.error(f"Error generating dashboard data: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Similarity Search Endpoints =====

@router.get("/similarity/info")
async def similarity_info():
    """Get similarity search information"""
    try:
        search = get_similarity_search()
        info = search.get_search_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting similarity search info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity/find")
async def find_similar_patterns(query_features: List[float], k: int = 5, threshold: float = 0.8):
    """Find similar patterns to query"""
    try:
        search = get_similarity_search()

        # Convert to numpy array
        query = np.array(query_features)

        # Find similar
        similar_patterns = search.find_similar_patterns(query, k=k, threshold=threshold)

        return {"success": True, "data": similar_patterns}
    except Exception as e:
        logger.error(f"Error finding similar patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/similarity/predict")
async def predict_from_similar(query_features: List[float], k: int = 5):
    """Predict outcome based on similar patterns"""
    try:
        search = get_similarity_search()

        # Convert to numpy array
        query = np.array(query_features)

        # Predict
        result = search.predict_from_similar(query, k=k)

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Error predicting from similar: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Multi-timeframe Analysis Endpoints =====

@router.get("/multi-timeframe/info")
async def multi_timeframe_info():
    """Get multi-timeframe analyzer information"""
    try:
        analyzer = get_multi_timeframe_analyzer()
        info = analyzer.get_analyzer_info()
        return {"success": True, "data": info}
    except Exception as e:
        logger.error(f"Error getting multi-timeframe info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/multi-timeframe/analyze")
async def analyze_multi_timeframe():
    """Analyze all timeframes and generate signal"""
    try:
        analyzer = get_multi_timeframe_analyzer()

        # Analyze all timeframes
        timeframe_features = analyzer.analyze_all_timeframes()

        if not timeframe_features:
            raise HTTPException(status_code=400, detail="No timeframe data available")

        # Generate signal
        signal = analyzer.generate_multi_timeframe_signal(timeframe_features)

        return {"success": True, "data": signal}
    except Exception as e:
        logger.error(f"Error analyzing multi-timeframe: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/multi-timeframe/confluence")
async def get_trend_confluence():
    """Get trend confluence across timeframes"""
    try:
        analyzer = get_multi_timeframe_analyzer()

        # Analyze timeframes
        timeframe_features = analyzer.analyze_all_timeframes()

        if not timeframe_features:
            raise HTTPException(status_code=400, detail="No timeframe data available")

        # Detect confluence
        confluence = analyzer.detect_trend_confluence(timeframe_features)

        return {"success": True, "data": confluence}
    except Exception as e:
        logger.error(f"Error getting confluence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ===== Status & Health Endpoints =====

@router.get("/status")
async def advanced_ml_status():
    """Get status of all advanced ML features"""
    try:
        status = {
            "lstm": {
                "available": KERAS_AVAILABLE,
                "initialized": _lstm_network is not None
            },
            "ensemble": {
                "available": True,
                "initialized": _ensemble_methods is not None,
                "trained": _ensemble_methods.is_trained if _ensemble_methods else False
            },
            "feature_selection": {
                "available": True,
                "initialized": _feature_selector is not None
            },
            "hyperparameter_tuning": {
                "available": True,
                "initialized": _hyperparameter_tuner is not None
            },
            "online_learning": {
                "available": True,
                "initialized": _online_learner is not None,
                "trained": _online_learner.is_initialized if _online_learner else False
            },
            "visualization": {
                "available": PLOTTING_AVAILABLE,
                "initialized": _pattern_visualizer is not None
            },
            "similarity_search": {
                "available": True,
                "initialized": _similarity_search is not None,
                "n_patterns": len(_similarity_search.historical_patterns) if _similarity_search else 0
            },
            "multi_timeframe": {
                "available": True,
                "initialized": _multi_timeframe_analyzer is not None
            }
        }

        return {"success": True, "data": status}
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def advanced_ml_health():
    """Health check for advanced ML system"""
    return {
        "success": True,
        "data": {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "features_available": 8,
            "keras_available": KERAS_AVAILABLE,
            "plotting_available": PLOTTING_AVAILABLE
        }
    }
