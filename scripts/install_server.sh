#!/bin/bash
#
# Alpha AI Autotrader - Server Installation Script
# Installs all dependencies including Claude Agent SDK
#

set -e  # Exit on error

echo "🚀 Alpha AI Autotrader - Server Installation"
echo "=============================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}❌ Please do not run as root${NC}"
    exit 1
fi

# Detect OS
if [ -f /etc/os-release ]; then
    . /etc/os-release
    OS=$ID
    VER=$VERSION_ID
else
    echo -e "${RED}❌ Cannot detect OS${NC}"
    exit 1
fi

echo -e "${GREEN}✓${NC} Detected OS: $OS $VER"
echo ""

# Step 1: Update system
echo "📦 Step 1/8: Updating system packages..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get update -qq
    sudo apt-get upgrade -y -qq
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    sudo yum update -y -q
fi
echo -e "${GREEN}✓${NC} System updated"
echo ""

# Step 2: Install Python 3.11+
echo "🐍 Step 2/8: Installing Python 3.11..."
if [ "$OS" = "ubuntu" ] || [ "$OS" = "debian" ]; then
    sudo apt-get install -y -qq python3.11 python3.11-venv python3-pip
elif [ "$OS" = "centos" ] || [ "$OS" = "rhel" ]; then
    sudo yum install -y -q python311 python311-pip
fi

# Check Python version
PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION installed"
echo ""

# Step 3: Install Node.js (required for Claude Code CLI)
echo "📦 Step 3/8: Installing Node.js..."
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y -qq nodejs
fi

NODE_VERSION=$(node --version)
echo -e "${GREEN}✓${NC} Node.js $NODE_VERSION installed"
echo ""

# Step 4: Install Claude Code CLI
echo "🤖 Step 4/8: Installing Claude Code CLI..."
if ! command -v claude &> /dev/null; then
    sudo npm install -g @anthropic-ai/claude-code
fi

CLAUDE_VERSION=$(claude --version 2>&1 || echo "unknown")
echo -e "${GREEN}✓${NC} Claude Code CLI installed ($CLAUDE_VERSION)"
echo ""

# Step 5: Install Docker
echo "🐳 Step 5/8: Installing Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

DOCKER_VERSION=$(docker --version | awk '{print $3}' | tr -d ',')
echo -e "${GREEN}✓${NC} Docker $DOCKER_VERSION installed"
echo ""

# Step 6: Install Docker Compose
echo "🐳 Step 6/8: Installing Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

COMPOSE_VERSION=$(docker-compose --version | awk '{print $4}' | tr -d ',')
echo -e "${GREEN}✓${NC} Docker Compose $COMPOSE_VERSION installed"
echo ""

# Step 7: Create project directory
echo "📁 Step 7/8: Setting up project directory..."
PROJECT_DIR="$HOME/alpha-ai-autotrader"

if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${YELLOW}⚠${NC}  Project not found. Cloning from GitHub..."
    git clone https://github.com/klobi1987/alpha-ai-autotrader.git "$PROJECT_DIR"
fi

cd "$PROJECT_DIR"
echo -e "${GREEN}✓${NC} Project directory: $PROJECT_DIR"
echo ""

# Step 8: Install Python dependencies
echo "📦 Step 8/8: Installing Python dependencies..."
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip -q
pip install -r backend/requirements.txt -q

# Install Claude Agent SDK
pip install claude-agent-sdk -q

echo -e "${GREEN}✓${NC} Python dependencies installed"
echo ""

# Create .env if not exists
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo -e "${YELLOW}⚠${NC}  Please edit .env and add your API keys"
fi

# Summary
echo ""
echo "=============================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "=============================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Edit .env file with your API keys:"
echo "   nano .env"
echo ""
echo "2. Add these API keys:"
echo "   - ANTHROPIC_API_KEY (Claude Max subscription)"
echo "   - LUNARCRUSH_API_KEY"
echo "   - MEXC_API_KEY"
echo "   - MEXC_SECRET_KEY"
echo ""
echo "3. Start the system:"
echo "   docker-compose up -d"
echo ""
echo "4. Access dashboard:"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "5. View logs:"
echo "   docker-compose logs -f"
echo ""
echo -e "${YELLOW}⚠${NC}  Important: You may need to log out and log back in for Docker permissions to take effect."
echo ""
