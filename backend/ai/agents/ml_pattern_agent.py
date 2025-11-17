"""
ML Pattern Discovery Agent
Specialized agent for discovering and utilizing ML-discovered patterns
"""

import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from datetime import datetime, timedelta

from ...ml.pattern_discovery import PatternDiscoveryEngine
from ...ml.pattern_learner import PatternLearner
from ...models.database import SessionLocal

logger = logging.getLogger(__name__)


class MLPatternAgent:
    """
    ML Pattern Discovery Agent
    
    Responsibilities:
    - Discover new patterns from historical data
    - Match current market conditions to known patterns
    - Predict pattern success probability
    - Learn from pattern performance
    - Provide insights to Master Brain
    """
    
    def __init__(self):
        """Initialize ML Pattern Agent"""
        self.name = "ML Pattern Agent"
        self.pattern_engine = PatternDiscoveryEngine()
        self.pattern_learner = PatternLearner()
        self.last_discovery_run = None
        self.discovery_interval = timedelta(days=7)  # Run discovery weekly
        
        logger.info(f"🤖 {self.name} initialized")
    
    async def analyze(self, coin_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze coin using ML patterns
        
        Args:
            coin_data: Dictionary with coin information and historical data
            
        Returns:
            Analysis result with pattern matches and predictions
        """
        try:
            symbol = coin_data.get('symbol', 'UNKNOWN')
            historical_data = coin_data.get('historical_data')
            
            if historical_data is None or len(historical_data) < 50:
                return {
                    'agent': self.name,
                    'symbol': symbol,
                    'confidence': 0.5,
                    'recommendation': 'NEUTRAL',
                    'reasoning': 'Insufficient historical data for ML analysis',
                    'patterns_matched': [],
                    'success_probability': 0.5
                }
            
            # Convert to DataFrame if needed
            if not isinstance(historical_data, pd.DataFrame):
                historical_data = pd.DataFrame(historical_data)
            
            # Check if we need to run pattern discovery
            await self._check_and_run_discovery(historical_data)
            
            # Match current data against known patterns
            pattern_match = self.pattern_engine.match_pattern(historical_data)
            
            # Predict success probability
            success_prob = self.pattern_engine.predict_pattern_success(historical_data)
            
            # Get active patterns from database
            db = SessionLocal()
            try:
                active_patterns = self.pattern_learner.get_active_patterns(db)
            finally:
                db.close()
            
            # Determine recommendation based on pattern match and success probability
            if pattern_match and success_prob > 0.7:
                recommendation = 'LONG'
                confidence = min(0.9, success_prob * pattern_match.get('match_confidence', 0.5))
                reasoning = f"Strong ML pattern match detected (Pattern: {pattern_match['pattern_id']}, Success Prob: {success_prob:.2%})"
            elif pattern_match and success_prob > 0.6:
                recommendation = 'LONG'
                confidence = min(0.75, success_prob * pattern_match.get('match_confidence', 0.5))
                reasoning = f"Moderate ML pattern match (Pattern: {pattern_match['pattern_id']}, Success Prob: {success_prob:.2%})"
            elif success_prob < 0.4:
                recommendation = 'AVOID'
                confidence = 0.7
                reasoning = f"Low success probability detected ({success_prob:.2%}), recommend avoiding"
            else:
                recommendation = 'NEUTRAL'
                confidence = 0.5
                reasoning = f"No strong ML pattern signal (Success Prob: {success_prob:.2%})"
            
            return {
                'agent': self.name,
                'symbol': symbol,
                'confidence': float(confidence),
                'recommendation': recommendation,
                'reasoning': reasoning,
                'patterns_matched': [pattern_match] if pattern_match else [],
                'success_probability': float(success_prob),
                'total_active_patterns': len(active_patterns),
                'pattern_statistics': self._get_pattern_stats(active_patterns)
            }
            
        except Exception as e:
            logger.error(f"❌ {self.name} analysis failed: {e}")
            return {
                'agent': self.name,
                'symbol': coin_data.get('symbol', 'UNKNOWN'),
                'confidence': 0.5,
                'recommendation': 'NEUTRAL',
                'reasoning': f'ML analysis error: {str(e)}',
                'patterns_matched': [],
                'success_probability': 0.5
            }
    
    async def _check_and_run_discovery(self, historical_data: pd.DataFrame):
        """
        Check if pattern discovery should run and execute if needed
        
        Args:
            historical_data: Historical OHLCV data
        """
        # Check if enough time has passed since last discovery
        if self.last_discovery_run is not None:
            time_since_last = datetime.now() - self.last_discovery_run
            if time_since_last < self.discovery_interval:
                return
        
        logger.info("🔍 Running ML pattern discovery...")
        
        try:
            # Discover patterns
            patterns = self.pattern_engine.discover_patterns(historical_data)
            
            # Save patterns to database
            db = SessionLocal()
            try:
                for pattern in patterns:
                    self.pattern_learner.save_pattern(pattern, db)
            finally:
                db.close()
            
            self.last_discovery_run = datetime.now()
            
            logger.info(f"✅ Pattern discovery complete: {len(patterns)} patterns discovered")
            
        except Exception as e:
            logger.error(f"❌ Pattern discovery failed: {e}")
    
    async def update_pattern_performance(
        self,
        pattern_id: str,
        trade_result: Dict[str, Any]
    ):
        """
        Update pattern performance after trade execution
        
        Args:
            pattern_id: Pattern identifier
            trade_result: Trade result with profit/loss
        """
        db = SessionLocal()
        try:
            success = self.pattern_learner.update_pattern_performance(
                pattern_id,
                trade_result,
                db
            )
            
            if success:
                logger.info(f"✅ Updated performance for pattern {pattern_id}")
            else:
                logger.warning(f"⚠️ Failed to update performance for pattern {pattern_id}")
                
        finally:
            db.close()
    
    async def get_pattern_insights(self) -> Dict[str, Any]:
        """
        Get insights about discovered patterns
        
        Returns:
            Pattern insights and statistics
        """
        db = SessionLocal()
        try:
            # Get active patterns
            active_patterns = self.pattern_learner.get_active_patterns(db)
            
            # Get overall statistics
            stats = self.pattern_learner.get_pattern_statistics(db)
            
            # Get top performing patterns
            top_patterns = sorted(
                [p for p in active_patterns if p['total_trades'] >= 5],
                key=lambda x: x['success_rate'],
                reverse=True
            )[:5]
            
            return {
                'total_patterns': stats.get('total_patterns', 0),
                'active_patterns': stats.get('active_patterns', 0),
                'avg_success_rate': stats.get('avg_success_rate', 0),
                'avg_return': stats.get('avg_return', 0),
                'total_trades': stats.get('total_trades', 0),
                'top_patterns': top_patterns,
                'last_discovery_run': self.last_discovery_run.isoformat() if self.last_discovery_run else None
            }
            
        finally:
            db.close()
    
    async def prune_patterns(self) -> int:
        """
        Remove underperforming patterns
        
        Returns:
            Number of patterns pruned
        """
        db = SessionLocal()
        try:
            pruned_count = self.pattern_learner.prune_patterns(db, min_trades=20)
            logger.info(f"🗑️ Pruned {pruned_count} underperforming patterns")
            return pruned_count
        finally:
            db.close()
    
    async def export_patterns(self) -> str:
        """
        Export patterns for backup
        
        Returns:
            Path to exported file
        """
        db = SessionLocal()
        try:
            filepath = self.pattern_learner.export_patterns(db)
            logger.info(f"💾 Patterns exported to {filepath}")
            return filepath
        finally:
            db.close()
    
    async def import_patterns(self, filepath: str) -> int:
        """
        Import patterns from backup
        
        Args:
            filepath: Path to import file
            
        Returns:
            Number of patterns imported
        """
        db = SessionLocal()
        try:
            imported_count = self.pattern_learner.import_patterns(filepath, db)
            logger.info(f"📥 Imported {imported_count} patterns from {filepath}")
            return imported_count
        finally:
            db.close()
    
    def _get_pattern_stats(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate statistics from pattern list
        
        Args:
            patterns: List of pattern dictionaries
            
        Returns:
            Statistics dictionary
        """
        if not patterns:
            return {
                'total': 0,
                'avg_success_rate': 0,
                'avg_confidence': 0
            }
        
        patterns_with_trades = [p for p in patterns if p['total_trades'] > 0]
        
        if not patterns_with_trades:
            return {
                'total': len(patterns),
                'avg_success_rate': 0,
                'avg_confidence': sum(p['confidence'] for p in patterns) / len(patterns)
            }
        
        return {
            'total': len(patterns),
            'avg_success_rate': sum(p['success_rate'] for p in patterns_with_trades) / len(patterns_with_trades),
            'avg_confidence': sum(p['confidence'] for p in patterns) / len(patterns),
            'best_pattern': max(patterns_with_trades, key=lambda x: x['success_rate'])['pattern_id']
        }
