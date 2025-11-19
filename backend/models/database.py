"""
Alpha AI Autotrader - Database Models
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
from passlib.context import CryptContext

Base = declarative_base()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class CoinData(Base):
    """LunarCrush coin data cache"""
    __tablename__ = "coin_data"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, index=True, nullable=False)
    name = Column(String)
    
    # Price data
    price = Column(Float)
    price_btc = Column(Float)
    volume_24h = Column(Float)
    volatility = Column(Float)
    
    # Market data
    market_cap = Column(Float)
    market_cap_rank = Column(Integer)
    market_dominance = Column(Float)
    
    # Social metrics
    alt_rank = Column(Integer, index=True)
    alt_rank_previous = Column(Integer)
    galaxy_score = Column(Float)
    galaxy_score_previous = Column(Float)
    sentiment = Column(Float)
    social_volume_24h = Column(Integer)
    social_dominance = Column(Float)
    interactions_24h = Column(Integer)
    
    # Metadata
    categories = Column(String)
    raw_data = Column(JSON)  # Full LunarCrush response
    
    # Timestamps
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, server_default=func.now())


class TradingSignal(Base):
    """AI-generated trading signals"""
    __tablename__ = "trading_signals"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, index=True, nullable=False)
    
    # Signal details
    signal_type = Column(String, nullable=False)  # e.g., "ALTRANK_SURGE", "SOCIAL_SURGE"
    direction = Column(String, nullable=False)  # "LONG" or "SHORT"
    confidence = Column(Float, nullable=False)
    
    # Price levels
    entry_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    
    # Risk/Reward
    risk_reward_ratio = Column(Float)
    position_size_usd = Column(Float)
    
    # Pattern info
    patterns_detected = Column(JSON)  # List of patterns that triggered
    confluence_count = Column(Integer)
    
    # Reasoning
    reason = Column(Text)
    technical_score = Column(Float)
    social_score = Column(Float)
    
    # Execution
    market_type = Column(String)  # "spot" or "futures"
    leverage = Column(Integer, default=1)
    executed = Column(Boolean, default=False)
    execution_time = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class Trade(Base):
    """Executed trades"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    signal_id = Column(Integer, nullable=True)  # Reference to TradingSignal
    
    # Trade details
    symbol = Column(String, index=True, nullable=False)
    side = Column(String, nullable=False)  # "buy" or "sell"
    market_type = Column(String, nullable=False)  # "spot" or "futures"
    
    # Order info
    order_id = Column(String, unique=True)
    order_type = Column(String)  # "market", "limit", etc.
    
    # Execution
    entry_price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    leverage = Column(Integer, default=1)
    
    # Exit (if closed)
    exit_price = Column(Float, nullable=True)
    exit_time = Column(DateTime, nullable=True)
    
    # PnL
    pnl_usd = Column(Float, nullable=True)
    pnl_percent = Column(Float, nullable=True)
    fees_usd = Column(Float, default=0.0)
    
    # Status
    status = Column(String, default="open")  # "open", "closed", "cancelled"
    result = Column(String, nullable=True)  # "win", "loss", "breakeven"
    
    # Stop-loss / Take-profit
    stop_loss = Column(Float, nullable=True)
    take_profit = Column(Float, nullable=True)
    
    # Timestamps
    entry_time = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PerformanceMetrics(Base):
    """Daily performance tracking"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime, unique=True, index=True, nullable=False)
    
    # Trading stats
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    win_rate = Column(Float, default=0.0)
    
    # PnL
    total_pnl_usd = Column(Float, default=0.0)
    total_fees_usd = Column(Float, default=0.0)
    net_pnl_usd = Column(Float, default=0.0)
    
    # Risk metrics
    max_drawdown = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    profit_factor = Column(Float, nullable=True)
    
    # Pattern stats
    best_pattern = Column(String, nullable=True)
    worst_pattern = Column(String, nullable=True)
    pattern_stats = Column(JSON, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


class PatternLibrary(Base):
    """ML-discovered patterns"""
    __tablename__ = "pattern_library"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Pattern info
    pattern_name = Column(String, unique=True, nullable=False)
    pattern_type = Column(String, nullable=False)  # "base" or "discovered"
    description = Column(Text)
    
    # Performance
    win_rate = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    avg_return = Column(Float, default=0.0)
    total_trades = Column(Integer, default=0)
    
    # Confidence
    confidence_score = Column(Float, default=5.0)
    enabled = Column(Boolean, default=True)
    
    # Pattern definition
    conditions = Column(JSON)  # Pattern detection logic
    
    # Timestamps
    discovered_at = Column(DateTime, server_default=func.now())
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SystemLog(Base):
    """System events and errors"""
    __tablename__ = "system_logs"

    id = Column(Integer, primary_key=True, index=True)
    level = Column(String, nullable=False)  # "INFO", "WARNING", "ERROR"
    module = Column(String)
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, server_default=func.now())


class User(Base):
    """User accounts for authentication"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    # Profile
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)

    # Settings & preferences
    preferences = Column(JSON, nullable=True)  # User-specific settings

    # Security
    last_login = Column(DateTime, nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def verify_password(self, plain_password: str) -> bool:
        """Verify a password against the hash"""
        return pwd_context.verify(plain_password, self.hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password for storing"""
        return pwd_context.hash(password)


# Aliases for convenience
Signal = TradingSignal
Position = Trade  # Trade model represents both open and closed positions


class DiscoveredPattern(Base):
    """ML-discovered trading patterns"""
    __tablename__ = "discovered_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(String, unique=True, index=True, nullable=False)
    pattern_type = Column(String, nullable=False)  # "ml_discovered", "manual", etc.
    cluster_id = Column(Integer, nullable=True)
    
    # Pattern characteristics
    occurrences = Column(Integer, default=0)
    confidence = Column(Float, default=0.5)
    center_features = Column(Text)  # JSON string of feature values
    
    # Performance tracking
    is_active = Column(Boolean, default=True)
    total_trades = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_return = Column(Float, default=0.0)
    
    # Timestamps
    discovered_at = Column(DateTime, nullable=False)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class PatternPerformance(Base):
    """Performance history for discovered patterns"""
    __tablename__ = "pattern_performance"
    
    id = Column(Integer, primary_key=True, index=True)
    pattern_id = Column(Integer, nullable=False)  # FK to DiscoveredPattern
    trade_id = Column(Integer, nullable=True)  # FK to Trade
    
    # Execution details
    executed_at = Column(DateTime, nullable=False)
    profit_loss = Column(Float, nullable=False)
    is_success = Column(Boolean, nullable=False)
    confidence_at_execution = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, server_default=func.now())


# Database setup
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLSession
from typing import Generator
import os

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/alpha_autotrader.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database (create tables)"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[SQLSession, None, None]:
    """Get database session (for FastAPI Depends)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
