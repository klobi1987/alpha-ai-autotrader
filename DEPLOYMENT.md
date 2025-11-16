# 🚀 Alpha AI Autotrader - Deployment Guide

Complete guide for deploying the Alpha AI Autotrader on your server.

---

## 📋 Prerequisites

### **Required**
- Docker & Docker Compose installed
- Git
- Server with at least 2GB RAM
- API Keys:
  - LunarCrush API Key ([Get here](https://lunarcrush.com))
  - MEXC API Key + Secret ([Get here](https://www.mexc.com/user/openapi))
  - OpenRouter API Key ([Get here](https://openrouter.ai))

### **Optional**
- Claude API Key (for premium AI decisions)
- Telegram Bot Token (for alerts)

---

## 🎯 Quick Start (5 Minutes)

### **Step 1: Clone Repository**
```bash
git clone https://github.com/klobi1987/alpha-ai-autotrader.git
cd alpha-ai-autotrader
```

### **Step 2: Configure Environment**
```bash
# Copy environment template
cp .env.example .env

# Edit .env file
nano .env
```

**Required settings in `.env`:**
```env
# API Keys (REQUIRED)
LUNARCRUSH_API_KEY=your_lunarcrush_key_here
MEXC_API_KEY=your_mexc_api_key_here
MEXC_SECRET_KEY=your_mexc_secret_key_here
OPENROUTER_API_KEY=your_openrouter_key_here

# Trading Mode (IMPORTANT!)
TRADING_MODE=testing  # Use 'testing' first, then 'live'
ENABLE_AUTO_TRADING=false  # Set to 'true' to enable auto-trading

# Risk Management
MAX_POSITION_SIZE_USD=500
MAX_CONCURRENT_POSITIONS=3
MAX_LEVERAGE=5
STOP_LOSS_PERCENT=2.0
MIN_CONFIDENCE_SCORE=7.5
```

### **Step 3: Start the System**
```bash
# Build and start
docker-compose up -d

# Check logs
docker-compose logs -f
```

### **Step 4: Access Dashboard**
Open your browser and navigate to:
```
http://your-server-ip:8000
```

**That's it!** 🎉 The system is running!

---

## ⚙️ Configuration

### **Trading Modes**

#### **Testing Mode** (Recommended First)
```env
TRADING_MODE=testing
ENABLE_AUTO_TRADING=false
```
- Paper trading only
- No real money at risk
- Test strategies safely

#### **Live Mode** (After Testing)
```env
TRADING_MODE=live
ENABLE_AUTO_TRADING=true
```
- Real trading with real money
- ⚠️ **Use with caution!**
- Start with small position sizes

### **Risk Management Settings**

```env
# Position Sizing
MAX_POSITION_SIZE_USD=500      # Max $ per trade
MAX_CONCURRENT_POSITIONS=3     # Max open positions

# Leverage
MAX_LEVERAGE=5                 # Max leverage (futures)

# Stop Loss
STOP_LOSS_PERCENT=2.0          # Default stop-loss %

# Signal Filtering
MIN_CONFIDENCE_SCORE=7.5       # Min confidence to trade (0-10)
```

### **AI Configuration**

```env
# Multi-AI Consensus
ENABLE_MULTI_AI_CONSENSUS=true

# AI Models (via OpenRouter)
OPENROUTER_API_KEY=your_key

# Optional: Claude for critical decisions
CLAUDE_API_KEY=your_claude_key
```

### **Scanning Configuration**

```env
# Scan Frequency
SCAN_INTERVAL=300              # Scan every 5 minutes (300 seconds)

# Coins to Scan
TOP_COINS_TO_SCAN=1000         # Top 1000 by social volume
```

### **Notifications** (Optional)

```env
# Telegram Alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

---

## 🔧 Management Commands

### **Start System**
```bash
docker-compose up -d
```

### **Stop System**
```bash
docker-compose down
```

### **Restart System**
```bash
docker-compose restart
```

### **View Logs**
```bash
# All logs
docker-compose logs -f

# Last 100 lines
docker-compose logs --tail=100

# Specific service
docker-compose logs -f alpha-autotrader
```

### **Update System**
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### **Backup Data**
```bash
# Backup database and logs
tar -czf backup-$(date +%Y%m%d).tar.gz data/ logs/

# Restore from backup
tar -xzf backup-20240101.tar.gz
```

---

## 📊 Monitoring

### **Health Check**
```bash
curl http://localhost:8000/api/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "Alpha AI Autotrader"
}
```

### **System Stats**
```bash
curl http://localhost:8000/api/system/stats
```

### **Container Stats**
```bash
docker stats alpha-ai-autotrader
```

---

## 🐛 Troubleshooting

### **Problem: Container won't start**

**Check logs:**
```bash
docker-compose logs
```

**Common causes:**
- Missing API keys in `.env`
- Port 8000 already in use
- Insufficient permissions

**Solution:**
```bash
# Check if port is in use
sudo lsof -i :8000

# Kill process using port
sudo kill -9 <PID>

# Restart
docker-compose up -d
```

### **Problem: API connection errors**

**Check API keys:**
```bash
# Verify .env file
cat .env | grep API_KEY
```

**Test API keys:**
```bash
# LunarCrush
curl "https://lunarcrush.com/api4/public/coins/list/v1?limit=1" \
  -H "Authorization: Bearer YOUR_KEY"

# MEXC (check on their website)
```

### **Problem: Database errors**

**Reset database:**
```bash
# Stop system
docker-compose down

# Remove database
rm -rf data/

# Restart (will recreate database)
docker-compose up -d
```

### **Problem: High memory usage**

**Check memory:**
```bash
docker stats
```

**Reduce memory usage:**
```env
# In .env, reduce scanning frequency
SCAN_INTERVAL=600  # Scan every 10 minutes instead of 5

# Reduce coins to scan
TOP_COINS_TO_SCAN=500
```

---

## 🔒 Security Best Practices

### **1. Protect API Keys**
```bash
# Never commit .env to Git
echo ".env" >> .gitignore

# Set proper permissions
chmod 600 .env
```

### **2. Use Firewall**
```bash
# Allow only specific IPs to access dashboard
sudo ufw allow from YOUR_IP to any port 8000

# Or use reverse proxy (Nginx)
```

### **3. Enable HTTPS**
Use Nginx reverse proxy with Let's Encrypt:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### **4. Regular Backups**
```bash
# Add to crontab
crontab -e

# Backup daily at 2 AM
0 2 * * * cd /path/to/alpha-ai-autotrader && tar -czf backup-$(date +\%Y\%m\%d).tar.gz data/ logs/
```

---

## 📈 Performance Optimization

### **1. Adjust Scanning Frequency**
```env
# Less frequent scans = lower API usage
SCAN_INTERVAL=600  # 10 minutes
```

### **2. Reduce Candidate Count**
```env
# Fewer candidates = faster analysis
TOP_COINS_TO_SCAN=500
```

### **3. Disable Multi-AI Consensus** (if needed)
```env
# Saves AI API costs
ENABLE_MULTI_AI_CONSENSUS=false
```

### **4. Use Caching**
LunarCrush data is cached for 5 minutes by default. Adjust if needed:
```env
LUNARCRUSH_CACHE_TTL=300  # 5 minutes
```

---

## 🆘 Support

### **Documentation**
- [README.md](README.md) - Overview
- [API Documentation](http://localhost:8000/api/docs) - API reference

### **Community**
- GitHub Issues: [Report bugs](https://github.com/klobi1987/alpha-ai-autotrader/issues)
- Discussions: [Ask questions](https://github.com/klobi1987/alpha-ai-autotrader/discussions)

---

## ⚠️ Important Warnings

1. **Start with Testing Mode** - Always test strategies before going live
2. **Use Small Position Sizes** - Start with minimal amounts
3. **Monitor Regularly** - Check dashboard daily
4. **Understand Risks** - Crypto trading is highly risky
5. **Backup Regularly** - Don't lose your data
6. **Secure Your Server** - Use firewall and HTTPS
7. **Keep API Keys Secret** - Never share or commit them

---

## 📝 License

MIT License - See [LICENSE](LICENSE) for details.

---

**Happy Trading! 🚀**

*Remember: Past performance does not guarantee future results. Trade responsibly.*
