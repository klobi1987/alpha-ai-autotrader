"""
Alpha AI Autotrader - API Routes
REST API endpoints for the trading system with comprehensive input validation
"""
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, WebSocket, WebSocketDisconnect, Request
from typing import List, Dict, Optional
from loguru import logger
import json
from datetime import datetime
from sqlalchemy.orm import Session

from ..models.database import get_db, Signal, Position, Trade
from ..core.settings_manager import SettingsManager
from .schemas import (
    APIKeyConfig,
    TradingConfig,
    ChatMessage,
    ChatResponse,
    ClosePositionRequest,
    ManualTradeRequest,
    SignalResponse,
    PositionResponse,
    PerformanceResponse,
    TradingStatusResponse
)

# Create router
api_router = APIRouter()


# ==================== Request/Response Models ====================
# All models moved to backend/api/schemas/trading.py for better validation and reusability


# ==================== Configuration Endpoints ====================

@api_router.get("/config")
async def get_config(request: Request):
    """Get current configuration"""
    try:
        settings_mgr = SettingsManager()
        config = settings_mgr.get_trading_config()
        return config
    except Exception as e:
        logger.error(f"Failed to get config: {e}")
        # Fallback to defaults
        return {
            "trading_mode": "testing",
            "max_position_size_usd": 500,
            "max_concurrent_positions": 3,
            "enable_auto_trading": False
        }


@api_router.post("/config")
async def update_config(config: TradingConfig, request: Request):
    """Update configuration"""
    try:
        settings_mgr = SettingsManager()
        settings_mgr.save_trading_config(config.dict())
        
        # Update trading system if running
        if hasattr(request.app.state, 'trading_system'):
            trading_system = request.app.state.trading_system
            # Update settings dynamically
            # trading_system.update_config(config.dict())
        
        logger.info(f"Configuration updated: {config.dict()}")
        return {"status": "success", "message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Failed to update config: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== Trading Endpoints ====================

@api_router.get("/signals")
async def get_signals(request: Request, db: Session = Depends(get_db)):
    """Get current trading signals"""
    try:
        # Get recent signals from database
        signals = db.query(Signal).order_by(Signal.created_at.desc()).limit(20).all()
        
        return {
            "signals": [
                {
                    "id": sig.id,
                    "symbol": sig.symbol,
                    "decision": sig.decision,
                    "confidence": sig.confidence,
                    "reasoning": sig.reasoning,
                    "entry_price": sig.entry_price,
                    "stop_loss": sig.stop_loss,
                    "take_profit": sig.take_profit,
                    "leverage": sig.leverage,
                    "timestamp": sig.created_at.isoformat()
                }
                for sig in signals
            ]
        }
    except Exception as e:
        logger.error(f"Failed to get signals: {e}")
        return {"signals": []}


@api_router.get("/positions")
async def get_positions(request: Request, db: Session = Depends(get_db)):
    """Get open positions"""
    try:
        # Get open positions from database
        positions = db.query(Position).filter(Position.status == "open").all()
        
        # Get current prices from MEXC (if available)
        mexc_client = getattr(request.app.state, 'mexc_client', None)
        
        result_positions = []
        for pos in positions:
            pos_data = {
                "id": pos.id,
                "symbol": pos.symbol,
                "side": pos.side,
                "entry_price": pos.entry_price,
                "current_price": pos.current_price or pos.entry_price,
                "quantity": pos.quantity,
                "leverage": pos.leverage,
                "stop_loss": pos.stop_loss,
                "take_profit": pos.take_profit,
                "pnl_usd": pos.pnl_usd or 0,
                "pnl_pct": pos.pnl_pct or 0,
                "opened_at": pos.opened_at.isoformat()
            }
            
            # Try to get current price
            if mexc_client:
                try:
                    ticker = await mexc_client.get_ticker(pos.symbol)
                    current_price = ticker.get('last', pos.entry_price)
                    
                    # Calculate P&L
                    if pos.side == "LONG":
                        pnl_pct = ((current_price - pos.entry_price) / pos.entry_price) * 100 * pos.leverage
                    else:  # SHORT
                        pnl_pct = ((pos.entry_price - current_price) / pos.entry_price) * 100 * pos.leverage
                    
                    pnl_usd = (pos.quantity * pos.entry_price) * (pnl_pct / 100)
                    
                    pos_data["current_price"] = current_price
                    pos_data["pnl_pct"] = round(pnl_pct, 2)
                    pos_data["pnl_usd"] = round(pnl_usd, 2)
                except:
                    pass
            
            result_positions.append(pos_data)
        
        return {"positions": result_positions}
    except Exception as e:
        logger.error(f"Failed to get positions: {e}")
        return {"positions": []}


@api_router.post("/positions/{symbol}/close")
async def close_position(symbol: str, request: Request, db: Session = Depends(get_db)):
    """Close a position"""
    try:
        # Find position
        position = db.query(Position).filter(
            Position.symbol == symbol,
            Position.status == "open"
        ).first()
        
        if not position:
            raise HTTPException(status_code=404, detail=f"Position {symbol} not found")
        
        # Get MEXC client
        mexc_client = getattr(request.app.state, 'mexc_client', None)
        if not mexc_client:
            raise HTTPException(status_code=500, detail="MEXC client not available")
        
        # Close position on MEXC
        result = await mexc_client.close_position(
            symbol=symbol,
            side=position.side,
            quantity=position.quantity
        )
        
        # Update database
        position.status = "closed"
        position.closed_at = datetime.now()
        position.close_price = result.get('price', position.current_price)
        
        # Calculate final P&L
        if position.side == "LONG":
            pnl_pct = ((position.close_price - position.entry_price) / position.entry_price) * 100 * position.leverage
        else:
            pnl_pct = ((position.entry_price - position.close_price) / position.entry_price) * 100 * position.leverage
        
        position.pnl_pct = pnl_pct
        position.pnl_usd = (position.quantity * position.entry_price) * (pnl_pct / 100)
        
        db.commit()
        
        logger.info(f"✅ Position {symbol} closed: {position.pnl_pct:.2f}% ({position.pnl_usd:.2f} USD)")
        
        return {
            "status": "success",
            "message": f"Position {symbol} closed",
            "pnl_pct": position.pnl_pct,
            "pnl_usd": position.pnl_usd
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to close position {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/trading/start")
async def start_trading(request: Request):
    """Start auto-trading"""
    try:
        trading_system = getattr(request.app.state, 'trading_system', None)
        
        if not trading_system:
            raise HTTPException(status_code=500, detail="Trading system not initialized")
        
        # Start trading
        await trading_system.start()
        
        logger.info("✅ Auto-trading started")
        return {"status": "success", "message": "Auto-trading started"}
    
    except Exception as e:
        logger.error(f"Failed to start trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.post("/trading/stop")
async def stop_trading(request: Request):
    """Stop auto-trading"""
    try:
        trading_system = getattr(request.app.state, 'trading_system', None)
        
        if not trading_system:
            raise HTTPException(status_code=500, detail="Trading system not initialized")
        
        # Stop trading
        await trading_system.stop()
        
        logger.info("⏸️  Auto-trading stopped")
        return {"status": "success", "message": "Auto-trading stopped"}
    
    except Exception as e:
        logger.error(f"Failed to stop trading: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@api_router.get("/trading/status")
async def get_trading_status(request: Request):
    """Get trading system status"""
    try:
        trading_system = getattr(request.app.state, 'trading_system', None)
        
        if not trading_system:
            return {
                "status": "not_initialized",
                "running": False,
                "message": "Trading system not initialized"
            }
        
        return {
            "status": "running" if trading_system.is_running else "stopped",
            "running": trading_system.is_running,
            "last_scan": trading_system.last_scan_time.isoformat() if hasattr(trading_system, 'last_scan_time') else None,
            "total_scans": getattr(trading_system, 'total_scans', 0)
        }
    
    except Exception as e:
        logger.error(f"Failed to get trading status: {e}")
        return {"status": "error", "running": False, "message": str(e)}


# ==================== Performance Endpoints ====================

@api_router.get("/performance")
async def get_performance(db: Session = Depends(get_db)):
    """Get trading performance metrics"""
    try:
        # Get all closed trades
        trades = db.query(Trade).filter(Trade.status == "closed").all()
        
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "total_pnl_usd": 0,
                "total_pnl_pct": 0,
                "best_trade": None,
                "worst_trade": None
            }
        
        # Calculate metrics
        total_trades = len(trades)
        winning_trades = [t for t in trades if t.pnl_usd > 0]
        losing_trades = [t for t in trades if t.pnl_usd <= 0]
        
        win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
        
        total_profit = sum(t.pnl_usd for t in winning_trades)
        total_loss = abs(sum(t.pnl_usd for t in losing_trades))
        profit_factor = total_profit / total_loss if total_loss > 0 else 0
        
        total_pnl_usd = sum(t.pnl_usd for t in trades)
        total_pnl_pct = sum(t.pnl_pct for t in trades) / total_trades if total_trades > 0 else 0
        
        best_trade = max(trades, key=lambda t: t.pnl_pct)
        worst_trade = min(trades, key=lambda t: t.pnl_pct)
        
        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate, 2),
            "profit_factor": round(profit_factor, 2),
            "total_pnl_usd": round(total_pnl_usd, 2),
            "total_pnl_pct": round(total_pnl_pct, 2),
            "best_trade": {
                "symbol": best_trade.symbol,
                "pnl_pct": round(best_trade.pnl_pct, 2),
                "pnl_usd": round(best_trade.pnl_usd, 2)
            },
            "worst_trade": {
                "symbol": worst_trade.symbol,
                "pnl_pct": round(worst_trade.pnl_pct, 2),
                "pnl_usd": round(worst_trade.pnl_usd, 2)
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get performance: {e}")
        return {
            "total_trades": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "total_pnl_usd": 0,
            "total_pnl_pct": 0
        }


# ==================== AI Chat Endpoints ====================

@api_router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(message: ChatMessage, request: Request):
    """Chat with AI"""
    try:
        chat_handler = getattr(request.app.state, 'chat_handler', None)
        
        if not chat_handler:
            return ChatResponse(
                message="Chat handler not initialized. Please check configuration.",
                timestamp=datetime.now().isoformat()
            )
        
        # Send message to ChatHandler
        response = await chat_handler.handle_user_message(message.message)
        
        return ChatResponse(
            message=response.get("message", ""),
            timestamp=response.get("timestamp", datetime.now().isoformat())
        )
    
    except Exception as e:
        logger.error(f"Chat error: {e}")
        return ChatResponse(
            message=f"Sorry, I encountered an error: {str(e)}",
            timestamp=datetime.now().isoformat()
        )


@api_router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket, request: Request):
    """
    WebSocket endpoint for real-time chat with Claude
    Supports streaming responses
    """
    await websocket.accept()
    logger.info("✅ WebSocket chat connected")
    
    try:
        chat_handler = getattr(request.app.state, 'chat_handler', None)
        
        if not chat_handler:
            await websocket.send_json({
                "type": "error",
                "content": "Chat handler not initialized"
            })
            await websocket.close()
            return
        
        while True:
            # Receive message from user
            data = await websocket.receive_text()
            message_data = json.loads(data)
            user_message = message_data.get("message", "")
            
            logger.info(f"💬 User: {user_message}")
            
            # Stream response from Claude
            async for chunk in chat_handler.stream_response(user_message):
                await websocket.send_json({
                    "type": "chunk",
                    "content": chunk,
                    "timestamp": datetime.now().isoformat()
                })
            
            # Send completion signal
            await websocket.send_json({
                "type": "complete",
                "timestamp": datetime.now().isoformat()
            })
    
    except WebSocketDisconnect:
        logger.info("WebSocket chat disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass


# ==================== Agent Status Endpoints ====================

@api_router.get("/agents/status")
async def get_agents_status(request: Request):
    """Get status of all 9 agents"""
    try:
        master_brain = getattr(request.app.state, 'master_brain', None)
        
        if not master_brain:
            return {"agents": []}
        
        # Get agent status from master brain
        agents_status = master_brain.get_agents_status()
        
        return {"agents": agents_status}
    
    except Exception as e:
        logger.error(f"Failed to get agents status: {e}")
        return {"agents": []}


# ==================== Market Data Endpoints ====================

@api_router.get("/market/candidates")
async def get_candidates(request: Request):
    """Get filtered trading candidates"""
    try:
        trading_system = getattr(request.app.state, 'trading_system', None)
        
        if not trading_system:
            return {"candidates": []}
        
        # Get latest candidates
        candidates = trading_system.get_latest_candidates()
        
        return {"candidates": candidates}
    
    except Exception as e:
        logger.error(f"Failed to get candidates: {e}")
        return {"candidates": []}


@api_router.get("/market/lunarcrush/stats")
async def get_lunarcrush_stats(request: Request):
    """Get LunarCrush API usage statistics"""
    try:
        lunarcrush_client = getattr(request.app.state, 'lunarcrush_client', None)
        
        if not lunarcrush_client:
            return {
                "total_requests": 0,
                "cache_hits": 0,
                "cache_hit_rate": 0,
                "estimated_daily_calls": 0
            }
        
        stats = lunarcrush_client.get_stats()
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get LunarCrush stats: {e}")
        return {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_hit_rate": 0,
            "estimated_daily_calls": 0
        }


# ==================== System Endpoints ====================

@api_router.get("/system/stats")
async def get_system_stats(request: Request):
    """Get system statistics"""
    try:
        trading_system = getattr(request.app.state, 'trading_system', None)
        
        stats = {
            "uptime": "N/A",
            "total_decisions": 0,
            "ai_requests": 0,
            "estimated_ai_cost_usd": 0
        }
        
        if trading_system:
            stats.update(trading_system.get_stats())
        
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get system stats: {e}")
        return {
            "uptime": "N/A",
            "total_decisions": 0,
            "ai_requests": 0,
            "estimated_ai_cost_usd": 0
        }


@api_router.post("/system/scan")
async def trigger_scan(background_tasks: BackgroundTasks, request: Request):
    """Manually trigger a market scan"""
    try:
        trading_system = getattr(request.app.state, 'trading_system', None)
        
        if not trading_system:
            raise HTTPException(status_code=500, detail="Trading system not initialized")
        
        # Trigger scan in background
        background_tasks.add_task(trading_system.run_scan)
        
        logger.info("📊 Manual market scan triggered")
        
        return {"status": "success", "message": "Market scan started"}
    
    except Exception as e:
        logger.error(f"Failed to trigger scan: {e}")
        raise HTTPException(status_code=500, detail=str(e))
