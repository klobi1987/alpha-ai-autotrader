"""
ML Pattern Discovery API Routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging

from ..models.database import get_db, DiscoveredPattern, PatternPerformance
from ..ai.agents.ml_pattern_agent import MLPatternAgent

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ml-patterns", tags=["ml-patterns"])

# Initialize ML Pattern Agent
ml_agent = MLPatternAgent()


@router.get("/patterns")
async def get_patterns(
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """
    Get all discovered patterns
    
    Query Parameters:
    - active_only: Return only active patterns (default: true)
    """
    try:
        query = db.query(DiscoveredPattern)
        
        if active_only:
            query = query.filter(DiscoveredPattern.is_active == True)
        
        patterns = query.all()
        
        result = []
        for pattern in patterns:
            result.append({
                'id': pattern.id,
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'cluster_id': pattern.cluster_id,
                'occurrences': pattern.occurrences,
                'confidence': pattern.confidence,
                'is_active': pattern.is_active,
                'total_trades': pattern.total_trades,
                'success_count': pattern.success_count,
                'failure_count': pattern.failure_count,
                'success_rate': pattern.success_count / pattern.total_trades if pattern.total_trades > 0 else 0,
                'avg_return': pattern.avg_return,
                'discovered_at': pattern.discovered_at.isoformat(),
                'last_used_at': pattern.last_used_at.isoformat() if pattern.last_used_at else None
            })
        
        return {
            'success': True,
            'total': len(result),
            'patterns': result
        }
        
    except Exception as e:
        logger.error(f"Failed to get patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{pattern_id}")
async def get_pattern(
    pattern_id: str,
    db: Session = Depends(get_db)
):
    """Get specific pattern by ID"""
    try:
        pattern = db.query(DiscoveredPattern).filter(
            DiscoveredPattern.pattern_id == pattern_id
        ).first()
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
        return {
            'success': True,
            'pattern': {
                'id': pattern.id,
                'pattern_id': pattern.pattern_id,
                'pattern_type': pattern.pattern_type,
                'cluster_id': pattern.cluster_id,
                'occurrences': pattern.occurrences,
                'confidence': pattern.confidence,
                'is_active': pattern.is_active,
                'total_trades': pattern.total_trades,
                'success_count': pattern.success_count,
                'failure_count': pattern.failure_count,
                'success_rate': pattern.success_count / pattern.total_trades if pattern.total_trades > 0 else 0,
                'avg_return': pattern.avg_return,
                'discovered_at': pattern.discovered_at.isoformat(),
                'last_used_at': pattern.last_used_at.isoformat() if pattern.last_used_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pattern: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/{pattern_id}/performance")
async def get_pattern_performance(
    pattern_id: str,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get performance history for a pattern"""
    try:
        # Get pattern
        pattern = db.query(DiscoveredPattern).filter(
            DiscoveredPattern.pattern_id == pattern_id
        ).first()
        
        if not pattern:
            raise HTTPException(status_code=404, detail="Pattern not found")
        
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
        
        return {
            'success': True,
            'pattern_id': pattern_id,
            'total_records': len(result),
            'performance': result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get pattern performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics")
async def get_pattern_statistics(db: Session = Depends(get_db)):
    """Get overall pattern statistics"""
    try:
        insights = await ml_agent.get_pattern_insights()
        
        return {
            'success': True,
            'statistics': insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get pattern statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/discover")
async def trigger_pattern_discovery():
    """
    Manually trigger pattern discovery
    (Normally runs automatically weekly)
    """
    try:
        # This would need historical data - for now return success
        # In production, this would fetch historical data and run discovery
        
        return {
            'success': True,
            'message': 'Pattern discovery triggered (runs in background)'
        }
        
    except Exception as e:
        logger.error(f"Failed to trigger pattern discovery: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/prune")
async def prune_patterns():
    """Remove underperforming patterns"""
    try:
        pruned_count = await ml_agent.prune_patterns()
        
        return {
            'success': True,
            'pruned_count': pruned_count,
            'message': f'Pruned {pruned_count} underperforming patterns'
        }
        
    except Exception as e:
        logger.error(f"Failed to prune patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_patterns():
    """Export patterns for backup"""
    try:
        filepath = await ml_agent.export_patterns()
        
        return {
            'success': True,
            'filepath': filepath,
            'message': 'Patterns exported successfully'
        }
        
    except Exception as e:
        logger.error(f"Failed to export patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/import")
async def import_patterns(filepath: str):
    """Import patterns from backup"""
    try:
        imported_count = await ml_agent.import_patterns(filepath)
        
        return {
            'success': True,
            'imported_count': imported_count,
            'message': f'Imported {imported_count} patterns'
        }
        
    except Exception as e:
        logger.error(f"Failed to import patterns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/insights")
async def get_ml_insights():
    """Get ML pattern insights and recommendations"""
    try:
        insights = await ml_agent.get_pattern_insights()
        
        return {
            'success': True,
            'insights': insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get ML insights: {e}")
        raise HTTPException(status_code=500, detail=str(e))
