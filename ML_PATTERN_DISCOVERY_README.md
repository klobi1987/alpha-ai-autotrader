# 🧠 Advanced ML Pattern Discovery

## Overview

The **Advanced ML Pattern Discovery** feature uses machine learning to automatically discover, learn, and adapt trading patterns from historical market data. This system continuously improves by tracking pattern performance and adjusting confidence scores based on real-world results.

---

## 🎯 Key Features

### 1. **Automatic Pattern Detection**
- **K-Means Clustering** - Groups similar market conditions into patterns
- **20+ Technical Features** - RSI, MACD, Bollinger Bands, momentum, volume, volatility
- **PCA Dimensionality Reduction** - Reduces noise and improves pattern recognition
- **Configurable Clusters** - Default 20 patterns, adjustable based on needs

### 2. **Pattern Success Prediction**
- **Random Forest Classifier** - Predicts probability of pattern success
- **Historical Learning** - Trains on past trade outcomes
- **Real-time Scoring** - Evaluates current market conditions against learned patterns
- **Confidence Scoring** - Dynamic confidence based on pattern performance

### 3. **Anomaly Detection**
- **Isolation Forest** - Detects unusual market conditions
- **Early Warning System** - Identifies potential market regime changes
- **Risk Management** - Avoids trading during anomalous conditions

### 4. **Performance Tracking**
- **Success Rate Monitoring** - Tracks win/loss ratio per pattern
- **Average Return Tracking** - Monitors profitability of each pattern
- **Confidence Updates** - Adjusts pattern confidence based on performance
- **Automatic Pruning** - Removes underperforming patterns (< 40% success rate)

### 5. **Pattern Learning Lifecycle**
```
Discovery → Storage → Matching → Execution → Performance Update → Confidence Adjustment
```

---

## 🏗️ Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│              PatternDiscoveryEngine                          │
│  - K-Means Clustering                                        │
│  - Random Forest Prediction                                  │
│  - Isolation Forest Anomaly Detection                        │
│  - Feature Engineering (20+ indicators)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                PatternLearner                                │
│  - Database Storage                                          │
│  - Performance Tracking                                      │
│  - Confidence Updates                                        │
│  - Pattern Pruning                                           │
│  - Export/Import                                             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                MLPatternAgent                                │
│  - Integrates with Master Brain                              │
│  - Provides pattern insights                                 │
│  - Updates pattern performance                               │
│  - Triggers discovery runs                                   │
└─────────────────────────────────────────────────────────────┘
```

### Database Schema

#### DiscoveredPattern
```sql
CREATE TABLE discovered_patterns (
    id INTEGER PRIMARY KEY,
    pattern_id VARCHAR UNIQUE,
    pattern_type VARCHAR,
    cluster_id INTEGER,
    occurrences INTEGER,
    confidence FLOAT,
    center_features TEXT,  -- JSON
    is_active BOOLEAN,
    total_trades INTEGER,
    success_count INTEGER,
    failure_count INTEGER,
    avg_return FLOAT,
    discovered_at DATETIME,
    last_used_at DATETIME,
    created_at DATETIME
);
```

#### PatternPerformance
```sql
CREATE TABLE pattern_performance (
    id INTEGER PRIMARY KEY,
    pattern_id INTEGER,  -- FK to DiscoveredPattern
    trade_id INTEGER,    -- FK to Trade
    executed_at DATETIME,
    profit_loss FLOAT,
    is_success BOOLEAN,
    confidence_at_execution FLOAT,
    created_at DATETIME
);
```

---

## 📊 Feature Engineering

### Technical Indicators (20+ Features)

**Price Momentum:**
- 5, 10, 20, 50 period returns
- 5, 10, 20, 50 period momentum

**Volume Analysis:**
- Volume ratio vs 20-period MA
- Volume momentum (10-period)

**Volatility Metrics:**
- 10, 20 period volatility
- Average True Range (ATR)

**Technical Indicators:**
- RSI (14-period)
- MACD + Signal Line
- Bollinger Bands (position)

**Price Position:**
- Price vs 20-period MA
- Price vs 50-period MA
- High/Low ratio
- Close position in daily range

---

## 🚀 Usage

### Dashboard UI

Access the **ML Patterns** tab in the dashboard:

**Statistics Cards:**
- Total Patterns
- Active Patterns
- Average Success Rate
- Average Return

**Actions:**
- 🔍 **Discover New Patterns** - Manually trigger pattern discovery
- 🗑️ **Prune Underperforming** - Remove patterns with < 40% success rate
- 💾 **Export Patterns** - Backup patterns to JSON file
- 🔄 **Refresh** - Reload patterns from database

**Patterns Table:**
- Pattern ID
- Type (ml_discovered, manual)
- Confidence Score
- Total Trades
- Success Rate
- Average Return
- Status (Active/Inactive)
- Discovery Date

### API Endpoints

#### Get All Patterns
```bash
GET /api/ml-patterns/patterns?active_only=true
```

**Response:**
```json
{
  "success": true,
  "total": 15,
  "patterns": [
    {
      "id": 1,
      "pattern_id": "ML_PATTERN_0",
      "pattern_type": "ml_discovered",
      "cluster_id": 0,
      "occurrences": 45,
      "confidence": 0.78,
      "is_active": true,
      "total_trades": 23,
      "success_count": 18,
      "failure_count": 5,
      "success_rate": 0.783,
      "avg_return": 0.0342,
      "discovered_at": "2025-11-17T10:30:00Z",
      "last_used_at": "2025-11-17T15:45:00Z"
    }
  ]
}
```

#### Get Pattern Performance History
```bash
GET /api/ml-patterns/patterns/{pattern_id}/performance?limit=100
```

**Response:**
```json
{
  "success": true,
  "pattern_id": "ML_PATTERN_0",
  "total_records": 23,
  "performance": [
    {
      "trade_id": 456,
      "executed_at": "2025-11-17T15:45:00Z",
      "profit_loss": 0.0542,
      "is_success": true,
      "confidence_at_execution": 0.78
    }
  ]
}
```

#### Get Statistics
```bash
GET /api/ml-patterns/statistics
```

**Response:**
```json
{
  "success": true,
  "statistics": {
    "total_patterns": 15,
    "active_patterns": 12,
    "patterns_with_trades": 8,
    "avg_success_rate": 0.72,
    "avg_return": 0.0285,
    "total_trades": 156,
    "top_patterns": [
      {
        "pattern_id": "ML_PATTERN_3",
        "success_rate": 0.85,
        "total_trades": 20
      }
    ],
    "last_discovery_run": "2025-11-17T10:30:00Z"
  }
}
```

#### Trigger Pattern Discovery
```bash
POST /api/ml-patterns/discover
```

**Response:**
```json
{
  "success": true,
  "message": "Pattern discovery triggered (runs in background)"
}
```

#### Prune Patterns
```bash
POST /api/ml-patterns/prune
```

**Response:**
```json
{
  "success": true,
  "pruned_count": 3,
  "message": "Pruned 3 underperforming patterns"
}
```

#### Export Patterns
```bash
POST /api/ml-patterns/export
```

**Response:**
```json
{
  "success": true,
  "filepath": "/data/ml_patterns/patterns_export_20251117_153000.json",
  "message": "Patterns exported successfully"
}
```

#### Import Patterns
```bash
POST /api/ml-patterns/import
Content-Type: application/json

{
  "filepath": "/data/ml_patterns/patterns_export_20251117_153000.json"
}
```

**Response:**
```json
{
  "success": true,
  "imported_count": 15,
  "message": "Imported 15 patterns"
}
```

---

## 🔄 Pattern Discovery Workflow

### 1. **Data Collection**
```python
# Collect historical OHLCV data
historical_data = fetch_historical_data(symbol, lookback=100)
```

### 2. **Feature Extraction**
```python
# Extract 20+ technical features
features = pattern_engine.extract_features(historical_data)
```

### 3. **Pattern Discovery**
```python
# K-Means clustering
patterns = pattern_engine.discover_patterns(historical_data)
```

### 4. **Pattern Storage**
```python
# Save to database
for pattern in patterns:
    pattern_learner.save_pattern(pattern, db)
```

### 5. **Pattern Matching**
```python
# Match current market against known patterns
pattern_match = pattern_engine.match_pattern(current_data)
```

### 6. **Success Prediction**
```python
# Predict success probability
success_prob = pattern_engine.predict_pattern_success(current_data)
```

### 7. **Trade Execution**
```python
# Execute trade if confidence high enough
if pattern_match and success_prob > 0.7:
    execute_trade(symbol, pattern_match)
```

### 8. **Performance Update**
```python
# Update pattern performance after trade
pattern_learner.update_pattern_performance(
    pattern_id,
    trade_result,
    db
)
```

---

## ⚙️ Configuration

### Pattern Discovery Settings

```python
# In PatternDiscoveryEngine.__init__()
config = {
    'n_clusters': 20,                    # Number of patterns to discover
    'min_pattern_occurrences': 5,        # Minimum occurrences to save pattern
    'min_success_rate': 0.6,             # Minimum success rate to keep pattern
    'lookback_period': 100               # Historical data lookback period
}
```

### Discovery Schedule

```python
# In MLPatternAgent.__init__()
self.discovery_interval = timedelta(days=7)  # Run discovery weekly
```

### Pruning Criteria

```python
# In PatternLearner.prune_patterns()
min_trades = 20                          # Minimum trades before pruning
min_success_rate = 0.4                   # Prune if < 40% success rate
min_avg_return = -0.02                   # Prune if < -2% avg return
```

---

## 📈 Performance Metrics

### Pattern Confidence Formula

```python
confidence = (
    0.4 * success_rate +              # 40% weight
    0.3 * normalized_return +          # 30% weight
    0.3 * sample_size_confidence       # 30% weight
)
```

Where:
- `success_rate` = success_count / total_trades
- `normalized_return` = (avg_return + 0.1) / 0.2  (maps -10% to +10% → 0 to 1)
- `sample_size_confidence` = 1 / (1 + exp(-0.1 * (trades - 20)))  (sigmoid)

### Pattern Pruning Conditions

A pattern is **deactivated** if:
1. `total_trades >= 20` AND
2. (`success_rate < 0.4` OR `avg_return < -0.02`)

---

## 🧪 Testing

### Manual Testing

1. **Access Dashboard:**
   ```
   http://localhost:8000
   ```

2. **Navigate to ML Patterns Tab**

3. **Trigger Discovery:**
   - Click "Discover New Patterns"
   - Wait 5-10 seconds
   - Click "Refresh"

4. **Verify Patterns:**
   - Check patterns table
   - Verify statistics cards updated

### API Testing

```bash
# Get patterns
curl http://localhost:8000/api/ml-patterns/patterns

# Get statistics
curl http://localhost:8000/api/ml-patterns/statistics

# Trigger discovery
curl -X POST http://localhost:8000/api/ml-patterns/discover

# Prune patterns
curl -X POST http://localhost:8000/api/ml-patterns/prune
```

---

## 🔧 Troubleshooting

### Issue: No patterns discovered

**Cause:** Insufficient historical data

**Solution:**
- Ensure `historical_data` has at least 100 data points
- Check `min_pattern_occurrences` setting
- Verify feature extraction is working

### Issue: All patterns pruned

**Cause:** Patterns performing poorly

**Solution:**
- Review `min_success_rate` threshold (default 0.4)
- Check if market conditions changed
- Retrain patterns with recent data

### Issue: Pattern confidence always 0.5

**Cause:** No trades executed yet

**Solution:**
- Patterns need trade history to update confidence
- Initial confidence is based on occurrence frequency
- Execute trades to build performance history

---

## 📚 Dependencies

```txt
scikit-learn==1.4.0
joblib==1.3.2
pandas==2.2.0
numpy==1.26.3
```

Install with:
```bash
pip install -r backend/requirements.txt
```

---

## 🎓 How It Works

### K-Means Clustering

1. Extract features from historical data
2. Normalize features (StandardScaler)
3. Apply PCA for dimensionality reduction
4. Cluster similar market conditions (K-Means)
5. Save cluster centers as patterns

### Random Forest Prediction

1. Train on historical features + labels (success/failure)
2. Predict success probability for new data
3. Use probability to adjust trading confidence
4. Retrain periodically with new data

### Isolation Forest Anomaly Detection

1. Train on normal market conditions
2. Detect outliers (anomalies)
3. Flag unusual market conditions
4. Avoid trading during anomalies

---

## 🚀 Future Enhancements

- [ ] **LSTM Neural Networks** - For sequence pattern detection
- [ ] **Ensemble Methods** - Combine multiple ML models
- [ ] **Feature Selection** - Automatic feature importance ranking
- [ ] **Hyperparameter Tuning** - Grid search for optimal parameters
- [ ] **Online Learning** - Continuous model updates
- [ ] **Pattern Visualization** - Chart pattern representations
- [ ] **Pattern Similarity Search** - Find similar historical patterns
- [ ] **Multi-timeframe Patterns** - Patterns across different timeframes

---

## 📝 Notes

- Pattern discovery runs **automatically every 7 days**
- Patterns are **pruned automatically** if success rate < 40%
- Pattern confidence **updates after each trade**
- Export patterns regularly for **backup**
- Monitor pattern statistics to **track ML performance**

---

## 🤝 Integration with Master Brain

The ML Pattern Agent is integrated into the Master Brain as the **10th specialized agent**:

```python
# In Master Brain V2
agents = [
    MarketAnalyzer(),
    SentimentAnalyzer(),
    RiskManager(),
    StrategyAgent(),
    TradeMonitor(),
    PatternDetector(),
    NewsAnalyzer(),
    WhaleTracker(),
    MLResearcher(),
    MLPatternAgent()  # ← NEW!
]
```

The ML Pattern Agent provides:
- Pattern match confidence
- Success probability prediction
- Pattern-based recommendations
- Performance insights

---

## 📊 Example Output

### Pattern Discovery
```
🔍 Discovering patterns from 1000 data points...
✅ Discovered 20 patterns
```

### Pattern Match
```python
{
    'pattern_id': 'ML_PATTERN_5',
    'cluster_id': 5,
    'match_distance': 0.23,
    'match_confidence': 0.81,
    'success_probability': 0.76
}
```

### Pattern Performance Update
```
✅ Pattern ML_PATTERN_5 performance updated (success_rate: 78.3%)
```

---

## 🎉 Conclusion

The **Advanced ML Pattern Discovery** feature brings **machine learning intelligence** to Alpha AI Autotrader, enabling:

- ✅ Automatic pattern discovery
- ✅ Continuous learning from results
- ✅ Dynamic confidence adjustment
- ✅ Performance-based pruning
- ✅ Real-time pattern matching

This creates a **self-improving trading system** that adapts to changing market conditions!

---

**Made with ❤️ by klobi1987**  
**Date:** November 17, 2025
