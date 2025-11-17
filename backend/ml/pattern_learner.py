"""
Pattern Learning Manager
Manages pattern learning lifecycle, storage, and performance tracking
"""

import json
import pickle
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import logging
from sqlalchemy.orm import Session

from ..models.database import SessionLocal, DiscoveredPattern, PatternPerformance

logger = logging.getLogger(__name__)


class PatternLearner:
    """
    Pattern Learning Manager
    
    Responsibilities:
    - Store discovered patterns in database
    - Track pattern performance over time
    - Update pattern confidence based on results
    - Prune underperforming patterns
    - Export/import patterns for backup
    """
    
    def __init__(self, storage_path: str = "data/ml_patterns"):
        """Initialize Pattern Learner"""
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("📚 Pattern Learner initialized")
    
    def save_pattern(
        self,
        pattern: Dict[str, Any],
        db: Session
    ) -> Optional[int]:
        """
        Save discovered pattern to database
        
        Args:
            pattern: Pattern dictionary from PatternDiscoveryEngine
            db: Database session
            
        Returns:
            Pattern ID or None if failed
        """
        try:
            # Create database record
            db_pattern = DiscoveredPattern(
                pattern_id=pattern['pattern_id'],
                pattern_type=pattern.get('type', 'ml_discovered'),
                cluster_id=pattern.get('cluster_id'),
                occurrences=pattern.get('occurrences', 0),
                confidence=pattern.get('confidence', 0.5),
                center_features=json.dumps(pattern.get('center', [])),
                discovered_at=datetime.fromisoformat(pattern['discovered_at']),
                is_active=True,
                success_count=0,
                failure_count=0,
                total_trades=0,
                avg_return=0.0
            )
            
            db.add(db_pattern)
            db.commit()
            db.refresh(db_pattern)
            
            logger.info(f"✅ Pattern {pattern['pattern_id']} saved to database")
            
            return db_pattern.id
            
        except Exception as e:
            logger.error(f"❌ Failed to save pattern: {e}")
            db.rollback()
            return None
    
    def update_pattern_performance(
        self,
        pattern_id: str,
        trade_result: Dict[str, Any],
        db: Session
    ) -> bool:
        """
        Update pattern performance after trade execution
        
        Args:
            pattern_id: Pattern identifier
            trade_result: Trade result with profit/loss
            db: Database session
            
        Returns:
            Success status
        """
        try:
            # Get pattern from database
            pattern = db.query(DiscoveredPattern).filter(
                DiscoveredPattern.pattern_id == pattern_id
            ).first()
            
            if not pattern:
                logger.warning(f"Pattern {pattern_id} not found")
                return False
            
            # Extract trade metrics
            profit_loss = trade_result.get('profit_loss', 0)
            is_success = profit_loss > 0
            
            # Update pattern statistics
            pattern.total_trades += 1
            if is_success:
                pattern.success_count += 1
            else:
                pattern.failure_count += 1
            
            # Update average return (exponential moving average)
            alpha = 0.3  # Weight for new data
            pattern.avg_return = (
                alpha * profit_loss + (1 - alpha) * pattern.avg_return
            )
            
            # Recalculate confidence based on performance
            success_rate = pattern.success_count / pattern.total_trades
            pattern.confidence = self._calculate_updated_confidence(
                success_rate,
                pattern.total_trades,
                pattern.avg_return
            )
            
            # Deactivate if performing poorly
            if pattern.total_trades >= 10 and success_rate < 0.4:
                pattern.is_active = False
                logger.warning(f"⚠️ Pattern {pattern_id} deactivated (poor performance)")
            
            # Create performance record
            performance = PatternPerformance(
                pattern_id=pattern.id,
                trade_id=trade_result.get('trade_id'),
                executed_at=datetime.now(),
                profit_loss=profit_loss,
                is_success=is_success,
                confidence_at_execution=trade_result.get('confidence', 0.5)
            )
            
            db.add(performance)
            db.commit()
            
            logger.info(f"✅ Pattern {pattern_id} performance updated (success_rate: {success_rate:.2%})")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update pattern performance: {e}")
            db.rollback()
            return False
    
    def get_active_patterns(self, db: Session) -> List[Dict[str, Any]]:
        """
        Get all active patterns from database
        
        Args:
            db: Database session
            
        Returns:
            List of active patterns
        """
        try:
            patterns = db.query(DiscoveredPattern).filter(
                DiscoveredPattern.is_active == True
            ).all()
            
            result = []
            for pattern in patterns:
                result.append({
                    'id': pattern.id,
                    'pattern_id': pattern.pattern_id,
                    'pattern_type': pattern.pattern_type,
                    'cluster_id': pattern.cluster_id,
                    'occurrences': pattern.occurrences,
                    'confidence': pattern.confidence,
                    'center': json.loads(pattern.center_features),
                    'discovered_at': pattern.discovered_at.isoformat(),
                    'total_trades': pattern.total_trades,
                    'success_count': pattern.success_count,
                    'failure_count': pattern.failure_count,
                    'success_rate': pattern.success_count / pattern.total_trades if pattern.total_trades > 0 else 0,
                    'avg_return': pattern.avg_return
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get active patterns: {e}")
            return []
    
    def get_pattern_performance_history(
        self,
        pattern_id: str,
        db: Session,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get performance history for a specific pattern
        
        Args:
            pattern_id: Pattern identifier
            db: Database session
            limit: Maximum number of records to return
            
        Returns:
            List of performance records
        """
        try:
            # Get pattern
            pattern = db.query(DiscoveredPattern).filter(
                DiscoveredPattern.pattern_id == pattern_id
            ).first()
            
            if not pattern:
                return []
            
            # Get performance records
            performances = db.query(PatternPerformance).filter(
                PatternPerformance.pattern_id == pattern.id
            ).order_by(
                PatternPerformance.executed_at.desc()
            ).limit(limit).all()
            
            result = []
            for perf in performances:
                result.append({
                    'trade_id': perf.trade_id,
                    'executed_at': perf.executed_at.isoformat(),
                    'profit_loss': perf.profit_loss,
                    'is_success': perf.is_success,
                    'confidence_at_execution': perf.confidence_at_execution
                })
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Failed to get pattern performance history: {e}")
            return []
    
    def prune_patterns(self, db: Session, min_trades: int = 20) -> int:
        """
        Remove underperforming patterns
        
        Args:
            db: Database session
            min_trades: Minimum trades before considering for pruning
            
        Returns:
            Number of patterns pruned
        """
        try:
            # Find underperforming patterns
            patterns = db.query(DiscoveredPattern).filter(
                DiscoveredPattern.is_active == True,
                DiscoveredPattern.total_trades >= min_trades
            ).all()
            
            pruned_count = 0
            
            for pattern in patterns:
                success_rate = pattern.success_count / pattern.total_trades
                
                # Prune if success rate < 40% or avg return < -2%
                if success_rate < 0.4 or pattern.avg_return < -0.02:
                    pattern.is_active = False
                    pruned_count += 1
                    logger.info(f"🗑️ Pruned pattern {pattern.pattern_id} (SR: {success_rate:.2%}, Avg Return: {pattern.avg_return:.2%})")
            
            db.commit()
            
            logger.info(f"✅ Pruned {pruned_count} underperforming patterns")
            
            return pruned_count
            
        except Exception as e:
            logger.error(f"❌ Failed to prune patterns: {e}")
            db.rollback()
            return 0
    
    def export_patterns(self, db: Session, filepath: Optional[str] = None) -> str:
        """
        Export all patterns to file for backup
        
        Args:
            db: Database session
            filepath: Optional custom filepath
            
        Returns:
            Path to exported file
        """
        try:
            if filepath is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = self.storage_path / f"patterns_export_{timestamp}.json"
            
            # Get all patterns
            patterns = db.query(DiscoveredPattern).all()
            
            export_data = {
                'exported_at': datetime.now().isoformat(),
                'total_patterns': len(patterns),
                'patterns': []
            }
            
            for pattern in patterns:
                export_data['patterns'].append({
                    'pattern_id': pattern.pattern_id,
                    'pattern_type': pattern.pattern_type,
                    'cluster_id': pattern.cluster_id,
                    'occurrences': pattern.occurrences,
                    'confidence': pattern.confidence,
                    'center_features': pattern.center_features,
                    'discovered_at': pattern.discovered_at.isoformat(),
                    'is_active': pattern.is_active,
                    'total_trades': pattern.total_trades,
                    'success_count': pattern.success_count,
                    'failure_count': pattern.failure_count,
                    'avg_return': pattern.avg_return
                })
            
            # Write to file
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"✅ Exported {len(patterns)} patterns to {filepath}")
            
            return str(filepath)
            
        except Exception as e:
            logger.error(f"❌ Failed to export patterns: {e}")
            return ""
    
    def import_patterns(self, filepath: str, db: Session) -> int:
        """
        Import patterns from backup file
        
        Args:
            filepath: Path to import file
            db: Database session
            
        Returns:
            Number of patterns imported
        """
        try:
            with open(filepath, 'r') as f:
                import_data = json.load(f)
            
            imported_count = 0
            
            for pattern_data in import_data['patterns']:
                # Check if pattern already exists
                existing = db.query(DiscoveredPattern).filter(
                    DiscoveredPattern.pattern_id == pattern_data['pattern_id']
                ).first()
                
                if existing:
                    logger.warning(f"Pattern {pattern_data['pattern_id']} already exists, skipping")
                    continue
                
                # Create new pattern
                pattern = DiscoveredPattern(
                    pattern_id=pattern_data['pattern_id'],
                    pattern_type=pattern_data['pattern_type'],
                    cluster_id=pattern_data.get('cluster_id'),
                    occurrences=pattern_data['occurrences'],
                    confidence=pattern_data['confidence'],
                    center_features=pattern_data['center_features'],
                    discovered_at=datetime.fromisoformat(pattern_data['discovered_at']),
                    is_active=pattern_data['is_active'],
                    total_trades=pattern_data['total_trades'],
                    success_count=pattern_data['success_count'],
                    failure_count=pattern_data['failure_count'],
                    avg_return=pattern_data['avg_return']
                )
                
                db.add(pattern)
                imported_count += 1
            
            db.commit()
            
            logger.info(f"✅ Imported {imported_count} patterns from {filepath}")
            
            return imported_count
            
        except Exception as e:
            logger.error(f"❌ Failed to import patterns: {e}")
            db.rollback()
            return 0
    
    def get_pattern_statistics(self, db: Session) -> Dict[str, Any]:
        """
        Get overall pattern statistics
        
        Args:
            db: Database session
            
        Returns:
            Statistics dictionary
        """
        try:
            # Count patterns
            total_patterns = db.query(DiscoveredPattern).count()
            active_patterns = db.query(DiscoveredPattern).filter(
                DiscoveredPattern.is_active == True
            ).count()
            
            # Get patterns with trades
            patterns_with_trades = db.query(DiscoveredPattern).filter(
                DiscoveredPattern.total_trades > 0
            ).all()
            
            if not patterns_with_trades:
                return {
                    'total_patterns': total_patterns,
                    'active_patterns': active_patterns,
                    'patterns_with_trades': 0,
                    'avg_success_rate': 0,
                    'avg_return': 0,
                    'total_trades': 0
                }
            
            # Calculate averages
            total_trades = sum(p.total_trades for p in patterns_with_trades)
            total_success = sum(p.success_count for p in patterns_with_trades)
            avg_success_rate = total_success / total_trades if total_trades > 0 else 0
            avg_return = sum(p.avg_return for p in patterns_with_trades) / len(patterns_with_trades)
            
            return {
                'total_patterns': total_patterns,
                'active_patterns': active_patterns,
                'patterns_with_trades': len(patterns_with_trades),
                'avg_success_rate': avg_success_rate,
                'avg_return': avg_return,
                'total_trades': total_trades
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get pattern statistics: {e}")
            return {}
    
    # ========================================
    # Helper Methods
    # ========================================
    
    def _calculate_updated_confidence(
        self,
        success_rate: float,
        total_trades: int,
        avg_return: float
    ) -> float:
        """
        Calculate updated confidence based on performance
        
        Formula combines:
        - Success rate (40% weight)
        - Average return (30% weight)
        - Sample size confidence (30% weight)
        """
        # Success rate component (0-1)
        success_component = success_rate
        
        # Return component (normalized to 0-1)
        # Assume -10% to +10% range maps to 0-1
        return_component = max(0, min(1, (avg_return + 0.1) / 0.2))
        
        # Sample size component (confidence increases with more trades)
        # Use sigmoid function: 1 / (1 + exp(-0.1 * (trades - 20)))
        import numpy as np
        sample_component = 1 / (1 + np.exp(-0.1 * (total_trades - 20)))
        
        # Weighted combination
        confidence = (
            0.4 * success_component +
            0.3 * return_component +
            0.3 * sample_component
        )
        
        return float(confidence)
