/**
 * Alpha AI Autotrader - Frontend Application
 * Alpine.js + WebSocket integration
 */

// Alpine.js app
function app() {
    return {
        // State
        darkMode: localStorage.getItem('darkMode') === 'true' || false,
        currentView: 'dashboard',
        tradingActive: false,
        
        // Chat
        chatInput: '',
        chatMessages: [
            {
                id: 1,
                role: 'assistant',
                content: 'Hello! I\'m your Alpha AI assistant. Ask me anything about trading, signals, or system status.',
                timestamp: new Date().toLocaleTimeString()
            }
        ],
        
        // Stats
        portfolioValue: 10000,
        openPositions: 0,
        totalPnL: 0,
        winRate: 0,
        
        // Signals
        latestSignals: [],
        
        // Agents
        agentsStatus: [
            { name: 'Market Analyzer', status: 'active', confidence: 7.5 },
            { name: 'Sentiment Analyzer', status: 'active', confidence: 8.2 },
            { name: 'Risk Manager', status: 'active', confidence: 7.0 },
            { name: 'Strategy Agent', status: 'active', confidence: 8.5 },
            { name: 'Trade Monitor', status: 'active', confidence: 7.8 }
        ],
        
        // WebSocket
        ws: null,
        wsConnected: false,
        
        // Initialize
        init() {
            console.log('🚀 Alpha AI Autotrader initialized');
            
            // Watch dark mode
            this.$watch('darkMode', value => {
                localStorage.setItem('darkMode', value);
            });
            
            // Connect WebSocket
            this.connectWebSocket();
            
            // Fetch initial data
            this.fetchData();
            
            // Auto-refresh every 30 seconds
            setInterval(() => {
                if (this.wsConnected) {
                    this.fetchData();
                }
            }, 30000);
        },
        
        // WebSocket connection
        connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}/ws`;
            
            console.log('🔌 Connecting to WebSocket:', wsUrl);
            
            this.ws = new WebSocket(wsUrl);
            
            this.ws.onopen = () => {
                console.log('✅ WebSocket connected');
                this.wsConnected = true;
                
                // Subscribe to channels
                this.subscribeToChannel('signals');
                this.subscribeToChannel('positions');
                this.subscribeToChannel('chat');
                this.subscribeToChannel('alerts');
                this.subscribeToChannel('agents');
            };
            
            this.ws.onmessage = (event) => {
                const message = JSON.parse(event.data);
                this.handleWebSocketMessage(message);
            };
            
            this.ws.onerror = (error) => {
                console.error('❌ WebSocket error:', error);
            };
            
            this.ws.onclose = () => {
                console.log('🔌 WebSocket disconnected');
                this.wsConnected = false;
                
                // Reconnect after 5 seconds
                setTimeout(() => {
                    console.log('🔄 Reconnecting...');
                    this.connectWebSocket();
                }, 5000);
            };
        },
        
        // Subscribe to WebSocket channel
        subscribeToChannel(channel) {
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'subscribe',
                    channel: channel
                }));
            }
        },
        
        // Handle WebSocket messages
        handleWebSocketMessage(message) {
            console.log('📨 WebSocket message:', message);
            
            switch (message.type) {
                case 'signal':
                    this.handleSignal(message.data);
                    break;
                
                case 'position_update':
                    this.handlePositionUpdate(message.data);
                    break;
                
                case 'chat_response':
                    this.handleChatResponse(message.data);
                    break;
                
                case 'alert':
                    this.handleAlert(message.data);
                    break;
                
                case 'agent_status':
                    this.handleAgentStatus(message.data);
                    break;
                
                case 'subscribed':
                    console.log(`✅ Subscribed to ${message.channel}`);
                    break;
            }
        },
        
        // Handle signal
        handleSignal(signal) {
            console.log('🎯 New signal:', signal);
            
            // Add to latest signals
            this.latestSignals.unshift({
                id: Date.now(),
                ...signal,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // Keep only last 10
            if (this.latestSignals.length > 10) {
                this.latestSignals.pop();
            }
            
            // Show notification
            this.showNotification(`New ${signal.decision} signal for ${signal.symbol}`, 'success');
        },
        
        // Handle position update
        handlePositionUpdate(position) {
            console.log('💼 Position update:', position);
            // Update positions list
        },
        
        // Handle chat response
        handleChatResponse(data) {
            this.chatMessages.push({
                id: Date.now(),
                role: 'assistant',
                content: data.message,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // Scroll to bottom
            this.$nextTick(() => {
                const container = this.$refs.chatContainer;
                container.scrollTop = container.scrollHeight;
            });
        },
        
        // Handle alert
        handleAlert(alert) {
            console.log('🚨 Alert:', alert);
            this.showNotification(alert.message, alert.type || 'info');
        },
        
        // Handle agent status
        handleAgentStatus(status) {
            console.log('🤖 Agent status:', status);
            // Update agents status
        },
        
        // Send chat message
        async sendMessage() {
            if (!this.chatInput.trim()) return;
            
            const message = this.chatInput.trim();
            this.chatInput = '';
            
            // Add user message to chat
            this.chatMessages.push({
                id: Date.now(),
                role: 'user',
                content: message,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // Scroll to bottom
            this.$nextTick(() => {
                const container = this.$refs.chatContainer;
                container.scrollTop = container.scrollHeight;
            });
            
            // Send via WebSocket
            if (this.ws && this.ws.readyState === WebSocket.OPEN) {
                this.ws.send(JSON.stringify({
                    type: 'message',
                    channel: 'chat',
                    data: { message }
                }));
            } else {
                // Fallback to HTTP
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message })
                    });
                    
                    const data = await response.json();
                    this.handleChatResponse(data);
                } catch (error) {
                    console.error('Failed to send message:', error);
                    this.showNotification('Failed to send message', 'error');
                }
            }
        },
        
        // Fetch data from API
        async fetchData() {
            try {
                // Fetch signals
                const signalsRes = await fetch('/api/signals');
                const signalsData = await signalsRes.json();
                if (signalsData.signals) {
                    this.latestSignals = signalsData.signals.map(s => ({
                        ...s,
                        id: Date.now() + Math.random()
                    }));
                }
                
                // Fetch positions
                const positionsRes = await fetch('/api/positions');
                const positionsData = await positionsRes.json();
                this.openPositions = positionsData.positions?.length || 0;
                
                // Fetch performance
                const perfRes = await fetch('/api/performance');
                const perfData = await perfRes.json();
                this.totalPnL = perfData.total_pnl_pct || 0;
                this.winRate = perfData.win_rate || 0;
                
                // Fetch config
                const configRes = await fetch('/api/config');
                const configData = await configRes.json();
                this.tradingActive = configData.enable_auto_trading || false;
                
            } catch (error) {
                console.error('Failed to fetch data:', error);
            }
        },
        
        // Show notification
        showNotification(message, type = 'info') {
            // Simple console log for now
            // In production, use a proper notification library
            console.log(`[${type.toUpperCase()}] ${message}`);
            
            // You can integrate with libraries like:
            // - Toastify
            // - SweetAlert2
            // - Notyf
        },
        
        // Start trading
        async startTrading() {
            try {
                const response = await fetch('/api/trading/start', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    this.tradingActive = true;
                    this.showNotification('Trading started', 'success');
                }
            } catch (error) {
                console.error('Failed to start trading:', error);
                this.showNotification('Failed to start trading', 'error');
            }
        },
        
        // Stop trading
        async stopTrading() {
            try {
                const response = await fetch('/api/trading/stop', {
                    method: 'POST'
                });
                
                if (response.ok) {
                    this.tradingActive = false;
                    this.showNotification('Trading stopped', 'success');
                }
            } catch (error) {
                console.error('Failed to stop trading:', error);
                this.showNotification('Failed to stop trading', 'error');
            }
        }
    };
}
