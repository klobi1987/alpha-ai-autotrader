"""
Alpha AI Autotrader - Machine Learning Engine
Pattern discovery and strategy optimization through ML
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from loguru import logger
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os


class MLEngine:
    """
    Machine Learning Engine - Pattern Discovery & Strategy Optimization
    
    Capabilities:
    - Discover new profitable patterns
    - Predict trade outcomes
    - Optimize entry/exit points
    - Adapt strategies based on market conditions
    - Learn from successful and failed trades
    """
    
    def __init__(self, model_dir: str = "./models"):
        """
        Args:
            model_dir: Directory to save/load models
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)
        
        # Models
        self.outcome_classifier = None  # Predict LONG/SHORT/WAIT
        self.pnl_regressor = None  # Predict expected P&L
        self.scaler = StandardScaler()
        
        # Load existing models if available
        self._load_models()
        
        logger.info("✅ ML Engine initialized")
    
    def _load_models(self):
        """Load pre-trained models if they exist"""
        try:
            classifier_path = os.path.join(self.model_dir, "outcome_classifier.joblib")
            regressor_path = os.path.join(self.model_dir, "pnl_regressor.joblib")
            scaler_path = os.path.join(self.model_dir, "scaler.joblib")
            
            if os.path.exists(classifier_path):
                self.outcome_classifier = joblib.load(classifier_path)
                logger.info("✅ Loaded outcome classifier")
            
            if os.path.exists(regressor_path):
                self.pnl_regressor = joblib.load(regressor_path)
                logger.info("✅ Loaded P&L regressor")
            
            if os.path.exists(scaler_path):
                self.scaler = joblib.load(scaler_path)
                logger.info("✅ Loaded scaler")
        
        except Exception as e:
            logger.warning(f"Could not load models: {e}")
    
    def _save_models(self):
        """Save trained models"""
        try:
            if self.outcome_classifier:
                joblib.dump(
                    self.outcome_classifier,
                    os.path.join(self.model_dir, "outcome_classifier.joblib")
                )
            
            if self.pnl_regressor:
                joblib.dump(
                    self.pnl_regressor,
                    os.path.join(self.model_dir, "pnl_regressor.joblib")
                )
            
            joblib.dump(
                self.scaler,
                os.path.join(self.model_dir, "scaler.joblib")
            )
            
            logger.info("✅ Models saved")
        
        except Exception as e:
            logger.error(f"Failed to save models: {e}")
    
    def extract_features(self, coin_data: Dict, market_data: Optional[Dict] = None) -> np.ndarray:
        """
        Extract features from coin and market data
        
        Args:
            coin_data: LunarCrush coin data
            market_data: MEXC market data
        
        Returns:
            Feature vector
        """
        features = []
        
        # LunarCrush features
        features.append(coin_data.get("alt_rank", 5000) / 10000)  # Normalize
        features.append(coin_data.get("galaxy_score", 50) / 100)
        features.append(coin_data.get("sentiment", 50) / 100)
        features.append(coin_data.get("social_volume_24h", 0) / 10000)
        features.append(coin_data.get("social_dominance", 0) * 100)
        features.append(coin_data.get("interactions_24h", 0) / 10000)
        features.append(coin_data.get("volatility", 0))
        features.append(coin_data.get("percent_change_24h", 0) / 100)
        features.append(coin_data.get("volume_24h", 0) / 1e9)  # Normalize to billions
        features.append(coin_data.get("market_cap", 0) / 1e9)
        
        # Market data features (if available)
        if market_data:
            features.append(market_data.get("price", 0) / 100000)  # Normalize
            features.append(market_data.get("volume", 0) / 1e9)
            features.append(market_data.get("bid_ask_spread", 0) * 1000)
            features.append(market_data.get("order_book_depth", 0) / 1e6)
        else:
            features.extend([0, 0, 0, 0])  # Placeholder
        
        # Time features
        import datetime
        now = datetime.datetime.utcnow()
        features.append(now.hour / 24)  # Hour of day
        features.append(now.weekday() / 7)  # Day of week
        
        return np.array(features).reshape(1, -1)
    
    def train(self, historical_trades: List[Dict]) -> Dict:
        """
        Train ML models on historical trades
        
        Args:
            historical_trades: List of past trades with outcomes
        
        Returns:
            Training statistics
        """
        if len(historical_trades) < 50:
            logger.warning(f"Not enough data to train ({len(historical_trades)} trades). Need at least 50.")
            return {"status": "insufficient_data", "trades": len(historical_trades)}
        
        logger.info(f"🎓 Training ML models on {len(historical_trades)} trades...")
        
        try:
            # Prepare training data
            X = []
            y_outcome = []
            y_pnl = []
            
            for trade in historical_trades:
                # Extract features
                coin_data = trade.get("metadata", {}).get("market_conditions", {})
                market_data = trade.get("metadata", {}).get("mexc_data", {})
                
                features = self.extract_features(coin_data, market_data)
                X.append(features[0])
                
                # Labels
                side = trade.get("side", "WAIT")
                pnl = trade.get("pnl", 0)
                
                y_outcome.append(side)
                y_pnl.append(pnl)
            
            X = np.array(X)
            y_outcome = np.array(y_outcome)
            y_pnl = np.array(y_pnl)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train outcome classifier
            X_train, X_test, y_train, y_test = train_test_split(
                X_scaled, y_outcome, test_size=0.2, random_state=42
            )
            
            self.outcome_classifier = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            self.outcome_classifier.fit(X_train, y_train)
            
            classifier_score = self.outcome_classifier.score(X_test, y_test)
            
            # Train P&L regressor (only on executed trades)
            executed_mask = y_outcome != "WAIT"
            X_executed = X_scaled[executed_mask]
            y_pnl_executed = y_pnl[executed_mask]
            
            if len(X_executed) > 20:
                X_train_pnl, X_test_pnl, y_train_pnl, y_test_pnl = train_test_split(
                    X_executed, y_pnl_executed, test_size=0.2, random_state=42
                )
                
                self.pnl_regressor = GradientBoostingRegressor(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42
                )
                self.pnl_regressor.fit(X_train_pnl, y_train_pnl)
                
                regressor_score = self.pnl_regressor.score(X_test_pnl, y_test_pnl)
            else:
                regressor_score = 0.0
            
            # Save models
            self._save_models()
            
            logger.info(
                f"✅ Training complete: "
                f"Classifier accuracy={classifier_score:.2%}, "
                f"Regressor R²={regressor_score:.2f}"
            )
            
            return {
                "status": "success",
                "trades_used": len(historical_trades),
                "classifier_accuracy": classifier_score,
                "regressor_r2": regressor_score
            }
        
        except Exception as e:
            logger.error(f"Training failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def predict_outcome(
        self,
        coin_data: Dict,
        market_data: Optional[Dict] = None
    ) -> Dict:
        """
        Predict trade outcome using ML
        
        Args:
            coin_data: LunarCrush coin data
            market_data: MEXC market data
        
        Returns:
            {
                "predicted_decision": "LONG" | "SHORT" | "WAIT",
                "confidence": 0.85,
                "expected_pnl": 125.50,
                "ml_score": 8.2
            }
        """
        if not self.outcome_classifier:
            return {
                "predicted_decision": "WAIT",
                "confidence": 0.5,
                "expected_pnl": 0,
                "ml_score": 5.0,
                "note": "Model not trained yet"
            }
        
        try:
            # Extract features
            features = self.extract_features(coin_data, market_data)
            features_scaled = self.scaler.transform(features)
            
            # Predict outcome
            predicted_decision = self.outcome_classifier.predict(features_scaled)[0]
            
            # Get prediction probability (confidence)
            probabilities = self.outcome_classifier.predict_proba(features_scaled)[0]
            confidence = max(probabilities)
            
            # Predict expected P&L
            expected_pnl = 0
            if self.pnl_regressor and predicted_decision != "WAIT":
                expected_pnl = self.pnl_regressor.predict(features_scaled)[0]
            
            # Calculate ML score (0-10)
            ml_score = confidence * 10
            
            return {
                "predicted_decision": predicted_decision,
                "confidence": confidence,
                "expected_pnl": expected_pnl,
                "ml_score": ml_score
            }
        
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return {
                "predicted_decision": "WAIT",
                "confidence": 0.5,
                "expected_pnl": 0,
                "ml_score": 5.0,
                "error": str(e)
            }
    
    def discover_patterns(self, historical_trades: List[Dict]) -> List[Dict]:
        """
        Discover new profitable patterns using ML
        
        Args:
            historical_trades: Historical trade data
        
        Returns:
            List of discovered patterns
        """
        if len(historical_trades) < 100:
            logger.warning("Not enough data for pattern discovery")
            return []
        
        logger.info("🔍 Discovering new patterns...")
        
        try:
            # Convert to DataFrame
            df = pd.DataFrame(historical_trades)
            
            # Filter profitable trades
            profitable = df[df["pnl"] > 0]
            
            if len(profitable) < 20:
                return []
            
            patterns = []
            
            # Pattern 1: AltRank + Galaxy Score combination
            for trade in profitable.to_dict("records"):
                metadata = trade.get("metadata", {})
                market_cond = metadata.get("market_conditions", {})
                
                altrank = market_cond.get("alt_rank", 0)
                galaxy = market_cond.get("galaxy_score", 0)
                sentiment = market_cond.get("sentiment", 0)
                
                if altrank < 500 and galaxy > 70 and sentiment > 70:
                    patterns.append({
                        "name": "High Quality Momentum",
                        "conditions": {
                            "alt_rank": "<500",
                            "galaxy_score": ">70",
                            "sentiment": ">70"
                        },
                        "avg_pnl": trade["pnl"],
                        "confidence": 8.0
                    })
            
            # Pattern 2: Social surge
            for trade in profitable.to_dict("records"):
                metadata = trade.get("metadata", {})
                market_cond = metadata.get("market_conditions", {})
                
                social_vol = market_cond.get("social_volume_24h", 0)
                interactions = market_cond.get("interactions_24h", 0)
                
                if social_vol > 5000 and interactions > 10000:
                    patterns.append({
                        "name": "Viral Social Surge",
                        "conditions": {
                            "social_volume_24h": ">5000",
                            "interactions_24h": ">10000"
                        },
                        "avg_pnl": trade["pnl"],
                        "confidence": 7.5
                    })
            
            # Deduplicate and aggregate
            unique_patterns = {}
            for pattern in patterns:
                name = pattern["name"]
                if name not in unique_patterns:
                    unique_patterns[name] = pattern
                else:
                    # Average P&L
                    existing = unique_patterns[name]
                    count = existing.get("count", 1)
                    existing["avg_pnl"] = (existing["avg_pnl"] * count + pattern["avg_pnl"]) / (count + 1)
                    existing["count"] = count + 1
            
            discovered = list(unique_patterns.values())
            
            logger.info(f"✅ Discovered {len(discovered)} new patterns")
            
            return discovered
        
        except Exception as e:
            logger.error(f"Pattern discovery failed: {e}")
            return []
    
    def optimize_parameters(self, historical_trades: List[Dict]) -> Dict:
        """
        Optimize trading parameters based on historical performance
        
        Args:
            historical_trades: Historical trade data
        
        Returns:
            Optimized parameters
        """
        if len(historical_trades) < 50:
            return {}
        
        logger.info("⚙️ Optimizing parameters...")
        
        try:
            df = pd.DataFrame(historical_trades)
            
            # Find optimal confidence threshold
            profitable = df[df["pnl"] > 0]
            
            if len(profitable) > 0:
                # Get confidence values from profitable trades
                confidences = []
                for trade in profitable.to_dict("records"):
                    metadata = trade.get("metadata", {})
                    decision_ctx = metadata.get("decision_context", {})
                    conf = decision_ctx.get("confidence", 7.5)
                    confidences.append(conf)
                
                optimal_confidence = np.percentile(confidences, 25) if confidences else 7.5
            else:
                optimal_confidence = 7.5
            
            # Find optimal leverage
            leverages = df["leverage"].values
            pnls = df["pnl"].values
            
            # Calculate average P&L per leverage level
            leverage_performance = {}
            for lev, pnl in zip(leverages, pnls):
                if lev not in leverage_performance:
                    leverage_performance[lev] = []
                leverage_performance[lev].append(pnl)
            
            optimal_leverage = 1
            best_avg_pnl = -float("inf")
            
            for lev, pnls_list in leverage_performance.items():
                avg_pnl = np.mean(pnls_list)
                if avg_pnl > best_avg_pnl:
                    best_avg_pnl = avg_pnl
                    optimal_leverage = lev
            
            optimized = {
                "min_confidence": float(optimal_confidence),
                "recommended_leverage": int(optimal_leverage),
                "based_on_trades": len(historical_trades)
            }
            
            logger.info(f"✅ Optimized parameters: {optimized}")
            
            return optimized
        
        except Exception as e:
            logger.error(f"Parameter optimization failed: {e}")
            return {}
