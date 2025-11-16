"""
Alpha AI Autotrader - WebSocket Connection Manager
Manages WebSocket connections and broadcasts
"""
from fastapi import WebSocket
from typing import List, Dict, Set, Optional
from loguru import logger
import json


class ConnectionManager:
    """
    Manages WebSocket connections and message broadcasting
    
    Features:
    - Multiple concurrent connections
    - Channel-based subscriptions
    - Broadcast to specific channels
    - Connection lifecycle management
    """
    
    def __init__(self):
        # Active connections
        self.active_connections: List[WebSocket] = []
        
        # Channel subscriptions: {websocket: set(channels)}
        self.subscriptions: Dict[WebSocket, Set[str]] = {}
        
        # Available channels
        self.channels = {
            "signals",      # Trading signals
            "positions",    # Open positions updates
            "chat",         # AI chat messages
            "alerts",       # System alerts
            "performance",  # Performance metrics
            "agents"        # Agent status updates
        }
    
    async def connect(self, websocket: WebSocket):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = set()
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")
    
    async def subscribe(self, websocket: WebSocket, channel: str):
        """Subscribe a connection to a channel"""
        if channel in self.channels:
            self.subscriptions[websocket].add(channel)
            logger.debug(f"WebSocket subscribed to channel: {channel}")
        else:
            logger.warning(f"Unknown channel: {channel}")
    
    async def unsubscribe(self, websocket: WebSocket, channel: str):
        """Unsubscribe a connection from a channel"""
        if websocket in self.subscriptions:
            self.subscriptions[websocket].discard(channel)
            logger.debug(f"WebSocket unsubscribed from channel: {channel}")
    
    async def send_personal_message(self, message: Dict, websocket: WebSocket):
        """Send a message to a specific connection"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict, channel: Optional[str] = None):
        """
        Broadcast a message to all connections (or specific channel)
        
        Args:
            message: Message dict to send
            channel: Optional channel filter
        """
        disconnected = []
        
        for connection in self.active_connections:
            # Check if connection is subscribed to channel
            if channel and channel not in self.subscriptions.get(connection, set()):
                continue
            
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
    
    async def broadcast_signal(self, signal: Dict):
        """Broadcast a trading signal"""
        await self.broadcast({
            "type": "signal",
            "channel": "signals",
            "data": signal
        }, channel="signals")
    
    async def broadcast_position_update(self, position: Dict):
        """Broadcast a position update"""
        await self.broadcast({
            "type": "position_update",
            "channel": "positions",
            "data": position
        }, channel="positions")
    
    async def broadcast_alert(self, alert: Dict):
        """Broadcast an alert"""
        await self.broadcast({
            "type": "alert",
            "channel": "alerts",
            "data": alert
        }, channel="alerts")
    
    async def broadcast_agent_status(self, agent_status: Dict):
        """Broadcast agent status update"""
        await self.broadcast({
            "type": "agent_status",
            "channel": "agents",
            "data": agent_status
        }, channel="agents")
    
    async def broadcast_performance(self, performance: Dict):
        """Broadcast performance metrics"""
        await self.broadcast({
            "type": "performance",
            "channel": "performance",
            "data": performance
        }, channel="performance")
    
    def get_stats(self) -> Dict:
        """Get connection statistics"""
        return {
            "total_connections": len(self.active_connections),
            "subscriptions_by_channel": {
                channel: sum(
                    1 for subs in self.subscriptions.values()
                    if channel in subs
                )
                for channel in self.channels
            }
        }
