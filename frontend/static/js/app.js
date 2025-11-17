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
        
        // Settings - API Keys
        apiKeys: {
            ANTHROPIC_API_KEY: { masked_value: null, is_set: false, status: 'not_set' },
            LUNARCRUSH_API_KEY: { masked_value: null, is_set: false, status: 'not_set' },
            MEXC_API_KEY: { masked_value: null, is_set: false, status: 'not_set' },
            MEXC_SECRET_KEY: { masked_value: null, is_set: false, status: 'not_set' },
            OPENROUTER_API_KEY: { masked_value: null, is_set: false, status: 'not_set' }
        },
        
        // Settings - Edit state
        editingKey: null,
        editingValue: '',
        
        // Settings - Trading settings
        tradingSettings: {
            trading_mode: 'testing',
            auto_trading_enabled: false,
            max_position_size: 500,
            max_leverage: 5,
            max_concurrent_positions: 3,
            stop_loss_default: 2.0,
            min_confidence: 7.5,
            enable_spot_trading: true,
            enable_futures_trading: true,
            auto_compound_profits: false
        },
        
        // Settings - UI state
        saving: false,
        testing: false,
        message: null,
        messageType: 'info',
        
        // ML Patterns
        mlPatterns: [],
        mlPatternStats: {
            total_patterns: 0,
            active_patterns: 0,
            avg_success_rate: 0,
            avg_return: 0
        },
        
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
            
            // Load ML Patterns
            this.loadMLPatterns();
            
            // Fetch initial data
            this.fetchData();
            
            // Load settings
            this.loadAPIKeys();
            this.loadTradingSettings();
            
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
        },
        
        // ========================================
        // Settings Methods
        // ========================================
        
        /**
         * Load API keys from backend
         */
        async loadAPIKeys() {
            try {
                const response = await fetch('/api/settings/api-keys');
                if (response.ok) {
                    const data = await response.json();
                    this.apiKeys = data;
                }
            } catch (error) {
                console.error('Failed to load API keys:', error);
            }
        },
        
        /**
         * Load trading settings from backend
         */
        async loadTradingSettings() {
            try {
                const response = await fetch('/api/settings/trading');
                if (response.ok) {
                    const data = await response.json();
                    this.tradingSettings = data;
                }
            } catch (error) {
                console.error('Failed to load trading settings:', error);
            }
        },
        
        /**
         * Start editing API key
         */
        startEditKey(keyName) {
            this.editingKey = keyName;
            this.editingValue = '';
        },
        
        /**
         * Cancel editing
         */
        cancelEdit() {
            this.editingKey = null;
            this.editingValue = '';
        },
        
        /**
         * Save API key
         */
        async saveAPIKey(keyName) {
            if (!this.editingValue.trim()) {
                this.showMessage('Please enter a valid API key', 'error');
                return;
            }
            
            this.saving = true;
            
            try {
                const response = await fetch('/api/settings/api-keys', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        key_name: keyName,
                        key_value: this.editingValue
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage('API key saved successfully', 'success');
                    this.apiKeys[keyName] = data.key_data;
                    this.cancelEdit();
                } else {
                    this.showMessage(data.message || 'Failed to save API key', 'error');
                }
            } catch (error) {
                console.error('Failed to save API key:', error);
                this.showMessage('Failed to save API key', 'error');
            } finally {
                this.saving = false;
            }
        },
        
        /**
         * Delete API key
         */
        async deleteAPIKey(keyName) {
            if (!confirm(`Are you sure you want to delete ${this.getKeyLabel(keyName)}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/settings/api-keys/${keyName}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage('API key deleted successfully', 'success');
                    this.apiKeys[keyName] = { masked_value: null, is_set: false, status: 'not_set' };
                } else {
                    this.showMessage('Failed to delete API key', 'error');
                }
            } catch (error) {
                console.error('Failed to delete API key:', error);
                this.showMessage('Failed to delete API key', 'error');
            }
        },
        
        /**
         * Test connection
         */
        async testConnection(keyName) {
            this.testing = true;
            
            try {
                const response = await fetch(`/api/settings/api-keys/${keyName}/test`);
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage(`${this.getKeyLabel(keyName)} connection successful!`, 'success');
                    this.apiKeys[keyName].status = 'valid';
                } else {
                    this.showMessage(`${this.getKeyLabel(keyName)} connection failed: ${data.message}`, 'error');
                    this.apiKeys[keyName].status = 'invalid';
                }
            } catch (error) {
                console.error('Failed to test connection:', error);
                this.showMessage('Failed to test connection', 'error');
            } finally {
                this.testing = false;
            }
        },
        
        /**
         * Save trading settings
         */
        async saveTradingSettings() {
            this.saving = true;
            
            try {
                const response = await fetch('/api/settings/trading', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(this.tradingSettings)
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage('Trading settings saved successfully', 'success');
                    this.tradingSettings = data.settings;
                } else {
                    this.showMessage('Failed to save trading settings', 'error');
                }
            } catch (error) {
                console.error('Failed to save trading settings:', error);
                this.showMessage('Failed to save trading settings', 'error');
            } finally {
                this.saving = false;
            }
        },
        
        /**
         * Show message
         */
        showMessage(text, type = 'info') {
            this.message = text;
            this.messageType = type;
            
            setTimeout(() => {
                this.message = null;
            }, 5000);
        },
        
        /**
         * Get API key label
         */
        getKeyLabel(keyName) {
            const labels = {
                'ANTHROPIC_API_KEY': 'Claude API Key',
                'LUNARCRUSH_API_KEY': 'LunarCrush API Key',
                'MEXC_API_KEY': 'MEXC API Key',
                'MEXC_SECRET_KEY': 'MEXC Secret Key',
                'OPENROUTER_API_KEY': 'OpenRouter API Key'
            };
            return labels[keyName] || keyName;
        },
        
        /**
         * Get API key description
         */
        getKeyDescription(keyName) {
            const descriptions = {
                'ANTHROPIC_API_KEY': 'Your Claude Max subscription API key (main AI brain)',
                'LUNARCRUSH_API_KEY': 'LunarCrush Individual plan API key for social data',
                'MEXC_API_KEY': 'MEXC exchange API key for trading',
                'MEXC_SECRET_KEY': 'MEXC exchange secret key (keep secure!)',
                'OPENROUTER_API_KEY': 'OpenRouter API key for multi-AI consensus (optional)'
            };
            return descriptions[keyName] || '';
        },
        
        /**
         * Get status badge color
         */
        getStatusColor(status) {
            const colors = {
                'valid': 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
                'invalid': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
                'not_set': 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-400'
            };
            return colors[status] || colors['not_set'];
        },
        
        // ========================================
        // ML Patterns Methods
        // ========================================
        
        /**
         * Load ML patterns from API
         */
        async loadMLPatterns() {
            try {
                const response = await fetch('/api/ml-patterns/patterns?active_only=false');
                const data = await response.json();
                
                if (data.success) {
                    this.mlPatterns = data.patterns || [];
                    console.log(`✅ Loaded ${this.mlPatterns.length} ML patterns`);
                }
                
                // Load statistics
                await this.loadMLPatternStats();
                
            } catch (error) {
                console.error('❌ Failed to load ML patterns:', error);
            }
        },
        
        /**
         * Load ML pattern statistics
         */
        async loadMLPatternStats() {
            try {
                const response = await fetch('/api/ml-patterns/statistics');
                const data = await response.json();
                
                if (data.success) {
                    this.mlPatternStats = data.statistics || {};
                    console.log('✅ Loaded ML pattern statistics');
                }
                
            } catch (error) {
                console.error('❌ Failed to load ML pattern statistics:', error);
            }
        },
        
        /**
         * Refresh ML patterns
         */
        async refreshMLPatterns() {
            console.log('🔄 Refreshing ML patterns...');
            await this.loadMLPatterns();
        },
        
        /**
         * Trigger pattern discovery
         */
        async discoverPatterns() {
            try {
                console.log('🔍 Triggering pattern discovery...');
                
                const response = await fetch('/api/ml-patterns/discover', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    console.log('✅ Pattern discovery triggered');
                    alert('Pattern discovery started! This may take a few minutes.');
                    
                    // Refresh after delay
                    setTimeout(() => this.loadMLPatterns(), 5000);
                } else {
                    alert('Failed to trigger pattern discovery');
                }
                
            } catch (error) {
                console.error('❌ Failed to trigger pattern discovery:', error);
                alert('Error triggering pattern discovery');
            }
        },
        
        /**
         * Prune underperforming patterns
         */
        async prunePatterns() {
            try {
                if (!confirm('Are you sure you want to prune underperforming patterns?')) {
                    return;
                }
                
                console.log('🗑️ Pruning patterns...');
                
                const response = await fetch('/api/ml-patterns/prune', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    console.log(`✅ Pruned ${data.pruned_count} patterns`);
                    alert(`Pruned ${data.pruned_count} underperforming patterns`);
                    
                    // Refresh
                    await this.loadMLPatterns();
                } else {
                    alert('Failed to prune patterns');
                }
                
            } catch (error) {
                console.error('❌ Failed to prune patterns:', error);
                alert('Error pruning patterns');
            }
        },
        
        /**
         * Export patterns
         */
        async exportPatterns() {
            try {
                console.log('💾 Exporting patterns...');
                
                const response = await fetch('/api/ml-patterns/export', {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    console.log('✅ Patterns exported:', data.filepath);
                    alert(`Patterns exported to: ${data.filepath}`);
                } else {
                    alert('Failed to export patterns');
                }
                
            } catch (error) {
                console.error('❌ Failed to export patterns:', error);
                alert('Error exporting patterns');
            }
        }
    };
}
