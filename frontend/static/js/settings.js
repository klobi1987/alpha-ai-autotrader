/**
 * Settings Management
 * Handles API key management and trading configuration
 */

function settingsModule() {
    return {
        // API Keys
        apiKeys: {
            ANTHROPIC_API_KEY: { masked: null, is_set: false, status: 'not_set' },
            LUNARCRUSH_API_KEY: { masked: null, is_set: false, status: 'not_set' },
            MEXC_API_KEY: { masked: null, is_set: false, status: 'not_set' },
            MEXC_SECRET_KEY: { masked: null, is_set: false, status: 'not_set' },
            OPENROUTER_API_KEY: { masked: null, is_set: false, status: 'not_set' }
        },
        
        // Edit state
        editingKey: null,
        editingValue: '',
        
        // Trading settings
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
        
        // UI state
        saving: false,
        testing: false,
        message: null,
        messageType: 'info',
        
        /**
         * Initialize settings
         */
        async initSettings() {
            await this.loadAPIKeys();
            await this.loadTradingSettings();
        },
        
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
                this.showMessage('Failed to load API keys', 'error');
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
                this.showMessage('Failed to load trading settings', 'error');
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
                    this.showMessage(data.message, 'success');
                    await this.loadAPIKeys();
                    this.cancelEdit();
                } else {
                    this.showMessage(data.message, 'error');
                }
            } catch (error) {
                console.error('Failed to save API key:', error);
                this.showMessage('Failed to save API key', 'error');
            } finally {
                this.saving = false;
            }
        },
        
        /**
         * Test API key connection
         */
        async testConnection(keyName) {
            this.testing = true;
            
            try {
                const response = await fetch(`/api/settings/test-connection/${keyName}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage(data.message, 'success');
                } else {
                    this.showMessage(data.message, 'error');
                }
            } catch (error) {
                console.error('Failed to test connection:', error);
                this.showMessage('Failed to test connection', 'error');
            } finally {
                this.testing = false;
            }
        },
        
        /**
         * Delete API key
         */
        async deleteAPIKey(keyName) {
            if (!confirm(`Are you sure you want to delete ${keyName}?`)) {
                return;
            }
            
            try {
                const response = await fetch(`/api/settings/api-keys/${keyName}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showMessage(data.message, 'success');
                    await this.loadAPIKeys();
                } else {
                    this.showMessage(data.message, 'error');
                }
            } catch (error) {
                console.error('Failed to delete API key:', error);
                this.showMessage('Failed to delete API key', 'error');
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
        }
    };
}
