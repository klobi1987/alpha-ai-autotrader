"""
Alpha AI Autotrader - FastAPI Main Application
REST API + WebSocket server for the trading system
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import List, Dict, Optional
import os
import json
from loguru import logger
from pathlib import Path

from ..core.config import get_settings
from .routes import api_router
from .settings_routes import router as settings_router
from .ml_patterns_routes import router as ml_patterns_router
from .websocket import ConnectionManager
from .chat_handler import ChatHandler

# Get settings
settings = get_settings()

# Configure logging
logger.add(
    settings.LOG_FILE,
    rotation=settings.LOG_ROTATION,
    retention=settings.LOG_RETENTION,
    level=settings.LOG_LEVEL
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup/shutdown events
    """
    # Startup
    logger.info("🚀 Alpha AI Autotrader starting up...")
    
    # Initialize database
    from ..models.database import init_db
    init_db()
    logger.info("✅ Database initialized")
    
    # Initialize WebSocket manager
    app.state.ws_manager = ConnectionManager()
    logger.info("✅ WebSocket manager initialized")
    
    # Initialize ChatHandler
    from ..integrations.claude_agent_client import ClaudeAgentClient
    from ..core.master_brain_v2 import MasterAIBrain
    
    claude_client = ClaudeAgentClient()
    master_brain = MasterAIBrain(claude_client=claude_client)
    app.state.chat_handler = ChatHandler(claude_client, master_brain)
    logger.info("✅ Chat Handler initialized")
    
    # Initialize trading system (if enabled)
    if settings.ENABLE_AUTO_TRADING:
        from ..core.trading_system import TradingSystem
        app.state.trading_system = TradingSystem(settings)
        await app.state.trading_system.start()
        logger.info("✅ Trading system started")
    
    logger.info("🎉 Alpha AI Autotrader ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 Alpha AI Autotrader shutting down...")
    
    if hasattr(app.state, "trading_system"):
        await app.state.trading_system.stop()
        logger.info("✅ Trading system stopped")
    
    logger.info("👋 Goodbye!")


# Create FastAPI app
app = FastAPI(
    title="Alpha AI Autotrader",
    description="World-Class Autonomous Cryptocurrency Trading System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")
app.include_router(settings_router)
app.include_router(ml_patterns_router)

# Serve static files
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir / "static")), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main dashboard"""
    index_file = frontend_dir / "templates" / "index.html"
    
    if index_file.exists():
        return FileResponse(index_file)
    
    # Fallback if frontend not built yet
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Alpha AI Autotrader</title>
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100vh;
                margin: 0;
            }
            .container {
                text-align: center;
                padding: 40px;
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            h1 { font-size: 3em; margin: 0; }
            p { font-size: 1.2em; opacity: 0.9; }
            .status { 
                display: inline-block;
                padding: 10px 20px;
                background: rgba(76, 175, 80, 0.3);
                border-radius: 20px;
                margin-top: 20px;
            }
            a {
                color: #fff;
                text-decoration: none;
                padding: 12px 24px;
                background: rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                display: inline-block;
                margin-top: 20px;
                transition: all 0.3s;
            }
            a:hover {
                background: rgba(255, 255, 255, 0.3);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Alpha AI Autotrader</h1>
            <p>World-Class Autonomous Crypto Trading System</p>
            <div class="status">✅ Backend Running</div>
            <br>
            <a href="/api/docs">📚 API Documentation</a>
            <a href="/api/health">🏥 Health Check</a>
        </div>
    </body>
    </html>
    """)


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "Alpha AI Autotrader"
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates
    
    Messages format:
    {
        "type": "subscribe" | "unsubscribe" | "message" | "command",
        "channel": "signals" | "positions" | "chat" | "alerts",
        "data": {...}
    }
    """
    manager: ConnectionManager = app.state.ws_manager
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type")
            channel = message.get("channel")
            msg_data = message.get("data", {})
            
            # Handle different message types
            if msg_type == "subscribe":
                await manager.subscribe(websocket, channel)
                await websocket.send_json({
                    "type": "subscribed",
                    "channel": channel,
                    "message": f"Subscribed to {channel}"
                })
            
            elif msg_type == "unsubscribe":
                await manager.unsubscribe(websocket, channel)
                await websocket.send_json({
                    "type": "unsubscribed",
                    "channel": channel,
                    "message": f"Unsubscribed from {channel}"
                })
            
            elif msg_type == "message":
                # Handle chat messages
                if channel == "chat":
                    # Process with AI
                    response = await process_chat_message(msg_data.get("message", ""))
                    await websocket.send_json({
                        "type": "chat_response",
                        "data": response
                    })
            
            elif msg_type == "command":
                # Handle commands (start/stop trading, etc.)
                response = await process_command(msg_data)
                await websocket.send_json({
                    "type": "command_response",
                    "data": response
                })
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info("WebSocket client disconnected")
    
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def process_chat_message(message: str) -> Dict:
    """Process chat message with AI"""
    chat_handler: ChatHandler = app.state.chat_handler
    response = await chat_handler.handle_user_message(message)
    return response


async def process_command(data: Dict) -> Dict:
    """Process command from client"""
    command = data.get("command")
    
    if command == "start_trading":
        return {"status": "success", "message": "Trading started"}
    
    elif command == "stop_trading":
        return {"status": "success", "message": "Trading stopped"}
    
    elif command == "get_status":
        return {
            "status": "success",
            "data": {
                "trading_active": False,
                "open_positions": 0,
                "balance": 10000
            }
        }
    
    return {"status": "error", "message": "Unknown command"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
