# 🚀 Alpha AI Autotrader

**World-Class Autonomous Cryptocurrency Trading System**

Powered by Master AI Brain, 9 specialized Alpha Agents, and multi-AI consensus for intelligent, automated crypto trading on MEXC exchange.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-brightgreen.svg)](https://www.docker.com/)

---

## ✨ Features

### **🧠 AI Intelligence**
- **Master AI Brain** - Orchestrates all decisions
- **9 Alpha Crypto Agents** - Specialized experts (Market Analysis, Sentiment, Risk, Strategy, Monitoring, Research, etc.)
- **Multi-AI Consensus** - DeepSeek R1, Gemini Flash Thinking, Qwen, Claude (cost-optimized)
- **Pattern Recognition** - 9 high-probability trading patterns
- **Machine Learning** - Continuous learning from results

### **📊 Data & Analysis**
- **LunarCrush Integration** - Social sentiment, AltRank, Galaxy Score
- **MEXC Market Data** - Real-time spot & futures data
- **Smart Filtering** - Reduces 1000+ coins to 5-10 top candidates (99% cost savings)
- **Web Surfing** - Agents research fundamentals when needed

### **💹 Trading**
- **Spot & Futures** - Trade both markets on MEXC
- **Auto-Execution** - Autonomous trade execution
- **Live Management** - Dynamic stop-loss, take-profit, break-even moves
- **Risk Management** - Position sizing, leverage control, portfolio optimization
- **Paper Trading** - Test mode before going live

### **🎨 Dashboard**
- **Modern UI** - TailwindCSS + Dark mode
- **Live Chat** - Ask AI anything in real-time
- **Real-time Updates** - WebSocket powered
- **Performance Metrics** - Win rate, profit factor, equity curve
- **Agent Status** - See what each agent is thinking

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    🌐 WEB DASHBOARD                         │
│         (TailwindCSS + Alpine.js + WebSocket)               │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                   ⚡ FASTAPI BACKEND                         │
│              (REST API + WebSocket Server)                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  🧠 MASTER AI BRAIN                          │
│         (Orchestrator + Decision Making Engine)             │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│              👥 9 ALPHA CRYPTO AGENTS                        │
│  Market | Sentiment | Risk | Strategy | Monitor             │
│  OnChain | Portfolio | Alert | Research                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                🤖 MULTI-AI CONSENSUS                         │
│   DeepSeek R1 | Gemini Flash | Qwen | Claude (optional)    │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  📊 DATA SOURCES                             │
│        LunarCrush (Social) + MEXC (Market Data)             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### **Prerequisites**
- Docker & Docker Compose
- API Keys:
  - [LunarCrush](https://lunarcrush.com)
  - [MEXC](https://www.mexc.com/user/openapi)
  - [OpenRouter](https://openrouter.ai)

### **Installation (5 Minutes)**

```bash
# 1. Clone repository
git clone https://github.com/klobi1987/alpha-ai-autotrader.git
cd alpha-ai-autotrader

# 2. Configure environment
cp .env.example .env
nano .env  # Add your API keys

# 3. Start system
docker-compose up -d

# 4. Access dashboard
open http://localhost:8000
```

**That's it!** 🎉

---

## ⚙️ Configuration

### **Required API Keys** (in `.env`)
```env
LUNARCRUSH_API_KEY=your_key_here
MEXC_API_KEY=your_key_here
MEXC_SECRET_KEY=your_secret_here
OPENROUTER_API_KEY=your_key_here
```

### **Trading Settings**
```env
TRADING_MODE=testing          # testing or live
ENABLE_AUTO_TRADING=false     # Set true to enable
MAX_POSITION_SIZE_USD=500     # Max $ per trade
MAX_CONCURRENT_POSITIONS=3    # Max open positions
MAX_LEVERAGE=5                # Max leverage (futures)
STOP_LOSS_PERCENT=2.0         # Default stop-loss %
MIN_CONFIDENCE_SCORE=7.5      # Min confidence to trade
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for full configuration guide.

---

## 📊 How It Works

### **Workflow**

1. **Data Collection** (Every 5 min)
   - Fetch top 1000 coins from LunarCrush (sorted by social volume)
   - Smart caching to minimize API calls

2. **Smart Filtering** (4 stages)
   - Social metrics (dominance, interactions, Galaxy Score)
   - Market metrics (market cap, volume, volatility)
   - Technical metrics (price action, momentum)
   - MEXC validation (liquidity, order book)
   - **Result**: 5-10 top candidates

3. **AI Analysis** (9 agents vote)
   - Each agent analyzes candidates
   - Votes: LONG/SHORT/WAIT + confidence + reasoning
   - Master Brain calculates consensus

4. **Multi-AI Validation** (If confidence >7.5)
   - Send to OpenRouter (DeepSeek R1 + Gemini Flash)
   - Get second opinion from thinking models
   - Compare with agent consensus

5. **Execution** (If confidence >7.5 & agreement >66%)
   - Risk Manager approves position size
   - Execute on MEXC (spot or futures)
   - Trade Monitor starts tracking

6. **Live Management** (Continuous)
   - Monitor positions every minute
   - Adjust stop-loss (move to break-even at +5%)
   - Trailing stop (at +10%)
   - Close on stop-loss/take-profit

---

## 💰 Cost Optimization

### **LunarCrush**
- Individual Plan: 1000 calls/day
- Our Usage: ~340 calls/day (34%)
- Cost: Free or $50/month

### **AI Models**
- Primary: DeepSeek R1 ($0.14/1M tokens) - 95% of requests
- Secondary: Gemini Flash Thinking (FREE)
- Premium: Claude 3.5 Sonnet (only for critical decisions)
- **Estimated Cost**: $5-10/month

### **Total Monthly Cost**
- LunarCrush: $0-50
- AI Models: $5-10
- MEXC: $0 (trading fees only)
- **Total**: $5-60/month

---

## 📚 Documentation

- **[DEPLOYMENT.md](DEPLOYMENT.md)** - Complete deployment guide
- **[API Docs](http://localhost:8000/api/docs)** - Interactive API documentation
- **Architecture** - See code comments for details

---

## 🛠️ Development

### **Project Structure**
```
alpha-ai-autotrader/
├── backend/
│   ├── agents/          # 9 Alpha Agents
│   ├── api/             # FastAPI routes & WebSocket
│   ├── core/            # Master Brain, filters, patterns
│   ├── integrations/    # LunarCrush, MEXC, OpenRouter
│   └── models/          # Database models
├── frontend/
│   ├── templates/       # HTML templates
│   └── static/          # CSS, JS, images
├── docker-compose.yml   # Docker deployment
├── Dockerfile           # Container image
└── .env.example         # Configuration template
```

### **Tech Stack**
- **Backend**: Python 3.11, FastAPI, SQLAlchemy, ccxt
- **Frontend**: HTML, TailwindCSS, Alpine.js, Chart.js
- **AI**: OpenRouter (DeepSeek R1, Gemini Flash, etc.)
- **Data**: LunarCrush API, MEXC SDK
- **Deployment**: Docker, Docker Compose

---

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## ⚠️ Disclaimer

**IMPORTANT**: Trading cryptocurrencies carries significant financial risk. This software is provided "as is" without warranty of any kind. Use at your own risk.

- ⚠️ **Start with Testing Mode** - Always test before going live
- 💰 **Use Small Amounts** - Never invest more than you can afford to lose
- 📊 **Monitor Regularly** - Check the system daily
- 🔒 **Secure Your Keys** - Never share API keys
- 📚 **Understand Risks** - Past performance ≠ future results

**By using this software, you acknowledge that you understand and accept these risks.**

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/klobi1987/alpha-ai-autotrader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/klobi1987/alpha-ai-autotrader/discussions)

---

## 🌟 Star History

If you find this project useful, please consider giving it a star! ⭐

---

**Made with ❤️ for the crypto community**

*Autonomous Trading. Intelligent Decisions. Maximum Gains.*
