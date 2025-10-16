"""
Machine learning engine for the meme-coin trading bot.

This module provides ML-based predictions and decision support
using scikit-learn and other ML libraries.
"""

import time
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from src.utils.logger import log_performance_metric, log_trading_event

logger = structlog.get_logger(__name__)


class ModelType(Enum):
    """Model type enumeration."""
    PRICE_PREDICTION = "price_prediction"
    VOLUME_PREDICTION = "volume_prediction"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    TREND_ANALYSIS = "trend_analysis"


class PredictionConfidence(Enum):
    """Prediction confidence enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass
class MLPrediction:
    """ML prediction result."""
    model_type: ModelType
    prediction: float
    confidence: PredictionConfidence
    features_used: List[str]
    timestamp: float
    model_version: str
    metadata: Dict[str, Any]


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    last_trained: float
    training_samples: int
    validation_samples: int


class MLEngine:
    """
    Machine learning engine for trading predictions.
    
    Features:
    - Price and volume prediction
    - Sentiment analysis
    - Risk assessment
    - Trend analysis
    - Model training and evaluation
    """
    
    def __init__(self):
        """Initialize the ML engine."""
        self.models: Dict[str, Any] = {}
        self.feature_scalers: Dict[str, Any] = {}
        self.prediction_history: List[MLPrediction] = []
        self.model_performance: Dict[str, ModelPerformance] = {}
        self.last_training: float = 0.0
        
        # Initialize models
        self._initialize_models()
        
        logger.info("ML engine initialized", model_count=len(self.models))
    
    def _initialize_models(self):
        """Initialize ML models."""
        try:
            # Import ML libraries
            from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
            from sklearn.linear_model import LinearRegression, LogisticRegression
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            
            # Price prediction model
            self.models["price_prediction"] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Volume prediction model
            self.models["volume_prediction"] = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Sentiment analysis model
            self.models["sentiment_analysis"] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Risk assessment model
            self.models["risk_assessment"] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Trend analysis model
            self.models["trend_analysis"] = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
            
            # Feature scalers
            for model_name in self.models.keys():
                self.feature_scalers[model_name] = StandardScaler()
            
            logger.info("ML models initialized successfully")
            
        except ImportError as e:
            logger.warning("ML libraries not available", error=str(e))
            logger.info("ML engine running in stub mode")
        except Exception as e:
            logger.error("Failed to initialize ML models", error=str(e))
    
    def extract_features(self, market_data: Dict[str, Any]) -> Dict[str, np.ndarray]:
        """
        Extract features from market data.
        
        Args:
            market_data: Market data dictionary
            
        Returns:
            Dictionary of feature arrays for each model
        """
        try:
            features = {}
            
            # Price features
            price_features = []
            if "price_history" in market_data:
                prices = market_data["price_history"]
                if len(prices) >= 20:
                    # Technical indicators
                    price_features.extend([
                        np.mean(prices[-5:]),   # 5-period moving average
                        np.mean(prices[-10:]),  # 10-period moving average
                        np.mean(prices[-20:]),  # 20-period moving average
                        np.std(prices[-20:]),   # 20-period volatility
                        (prices[-1] - prices[-5]) / prices[-5],  # 5-period return
                        (prices[-1] - prices[-10]) / prices[-10], # 10-period return
                        (prices[-1] - prices[-20]) / prices[-20], # 20-period return
                    ])
            
            # Volume features
            volume_features = []
            if "volume_history" in market_data:
                volumes = market_data["volume_history"]
                if len(volumes) >= 20:
                    volume_features.extend([
                        np.mean(volumes[-5:]),   # 5-period average volume
                        np.mean(volumes[-10:]),  # 10-period average volume
                        np.mean(volumes[-20:]),  # 20-period average volume
                        np.std(volumes[-20:]),   # Volume volatility
                        volumes[-1] / np.mean(volumes[-20:]),  # Volume ratio
                    ])
            
            # Market features
            market_features = []
            if "market_cap" in market_data:
                market_features.append(market_data["market_cap"])
            if "liquidity" in market_data:
                market_features.append(market_data["liquidity"])
            if "holders" in market_data:
                market_features.append(market_data["holders"])
            
            # Combine features for different models
            features["price_prediction"] = np.array(price_features + volume_features + market_features)
            features["volume_prediction"] = np.array(price_features + volume_features + market_features)
            features["sentiment_analysis"] = np.array(price_features + volume_features + market_features)
            features["risk_assessment"] = np.array(price_features + volume_features + market_features)
            features["trend_analysis"] = np.array(price_features + volume_features + market_features)
            
            return features
            
        except Exception as e:
            logger.error("Failed to extract features", error=str(e))
            return {}
    
    def predict_price(self, market_data: Dict[str, Any]) -> MLPrediction:
        """
        Predict future price movement.
        
        Args:
            market_data: Market data for prediction
            
        Returns:
            Price prediction result
        """
        try:
            start_time = time.time()
            
            # Extract features
            features = self.extract_features(market_data)
            if "price_prediction" not in features:
                return MLPrediction(
                    model_type=ModelType.PRICE_PREDICTION,
                    prediction=0.0,
                    confidence=PredictionConfidence.LOW,
                    features_used=[],
                    timestamp=time.time(),
                    model_version="stub",
                    metadata={"error": "No features available"}
                )
            
            # Make prediction (stub implementation)
            prediction = 0.0
            confidence = PredictionConfidence.LOW
            
            # In a real implementation, this would use the trained model
            if len(features["price_prediction"]) > 0:
                # Simple heuristic prediction
                recent_prices = market_data.get("price_history", [])
                if len(recent_prices) >= 5:
                    recent_trend = (recent_prices[-1] - recent_prices[-5]) / recent_prices[-5]
                    prediction = recent_trend * 0.1  # Conservative prediction
                    confidence = PredictionConfidence.MEDIUM
            
            execution_time = time.time() - start_time
            log_performance_metric("ml_prediction_time", execution_time, "seconds")
            
            result = MLPrediction(
                model_type=ModelType.PRICE_PREDICTION,
                prediction=prediction,
                confidence=confidence,
                features_used=[f"feature_{i}" for i in range(len(features["price_prediction"]))],
                timestamp=time.time(),
                model_version="stub_v1.0",
                metadata={"execution_time": execution_time}
            )
            
            self.prediction_history.append(result)
            
            log_trading_event(
                "price_prediction_made",
                {
                    "prediction": prediction,
                    "confidence": confidence.value,
                    "features_count": len(features["price_prediction"]),
                    "execution_time": execution_time
                },
                "INFO"
            )
            
            return result
            
        except Exception as e:
            logger.error("Failed to predict price", error=str(e))
            return MLPrediction(
                model_type=ModelType.PRICE_PREDICTION,
                prediction=0.0,
                confidence=PredictionConfidence.LOW,
                features_used=[],
                timestamp=time.time(),
                model_version="error",
                metadata={"error": str(e)}
            )
    
    def predict_volume(self, market_data: Dict[str, Any]) -> MLPrediction:
        """
        Predict future volume movement.
        
        Args:
            market_data: Market data for prediction
            
        Returns:
            Volume prediction result
        """
        try:
            start_time = time.time()
            
            # Extract features
            features = self.extract_features(market_data)
            if "volume_prediction" not in features:
                return MLPrediction(
                    model_type=ModelType.VOLUME_PREDICTION,
                    prediction=0.0,
                    confidence=PredictionConfidence.LOW,
                    features_used=[],
                    timestamp=time.time(),
                    model_version="stub",
                    metadata={"error": "No features available"}
                )
            
            # Make prediction (stub implementation)
            prediction = 0.0
            confidence = PredictionConfidence.LOW
            
            # Simple heuristic prediction
            recent_volumes = market_data.get("volume_history", [])
            if len(recent_volumes) >= 5:
                avg_volume = np.mean(recent_volumes[-5:])
                prediction = avg_volume * 1.1  # Slight increase
                confidence = PredictionConfidence.MEDIUM
            
            execution_time = time.time() - start_time
            log_performance_metric("ml_prediction_time", execution_time, "seconds")
            
            result = MLPrediction(
                model_type=ModelType.VOLUME_PREDICTION,
                prediction=prediction,
                confidence=confidence,
                features_used=[f"feature_{i}" for i in range(len(features["volume_prediction"]))],
                timestamp=time.time(),
                model_version="stub_v1.0",
                metadata={"execution_time": execution_time}
            )
            
            self.prediction_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error("Failed to predict volume", error=str(e))
            return MLPrediction(
                model_type=ModelType.VOLUME_PREDICTION,
                prediction=0.0,
                confidence=PredictionConfidence.LOW,
                features_used=[],
                timestamp=time.time(),
                model_version="error",
                metadata={"error": str(e)}
            )
    
    def analyze_sentiment(self, market_data: Dict[str, Any]) -> MLPrediction:
        """
        Analyze market sentiment.
        
        Args:
            market_data: Market data for sentiment analysis
            
        Returns:
            Sentiment analysis result
        """
        try:
            start_time = time.time()
            
            # Extract features
            features = self.extract_features(market_data)
            if "sentiment_analysis" not in features:
                return MLPrediction(
                    model_type=ModelType.SENTIMENT_ANALYSIS,
                    prediction=0.0,
                    confidence=PredictionConfidence.LOW,
                    features_used=[],
                    timestamp=time.time(),
                    model_version="stub",
                    metadata={"error": "No features available"}
                )
            
            # Simple sentiment analysis (stub implementation)
            prediction = 0.0  # Neutral sentiment
            confidence = PredictionConfidence.LOW
            
            # Analyze price momentum
            recent_prices = market_data.get("price_history", [])
            if len(recent_prices) >= 5:
                recent_trend = (recent_prices[-1] - recent_prices[-5]) / recent_prices[-5]
                if recent_trend > 0.05:
                    prediction = 0.7  # Positive sentiment
                    confidence = PredictionConfidence.MEDIUM
                elif recent_trend < -0.05:
                    prediction = -0.7  # Negative sentiment
                    confidence = PredictionConfidence.MEDIUM
            
            execution_time = time.time() - start_time
            
            result = MLPrediction(
                model_type=ModelType.SENTIMENT_ANALYSIS,
                prediction=prediction,
                confidence=confidence,
                features_used=[f"feature_{i}" for i in range(len(features["sentiment_analysis"]))],
                timestamp=time.time(),
                model_version="stub_v1.0",
                metadata={"execution_time": execution_time}
            )
            
            self.prediction_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error("Failed to analyze sentiment", error=str(e))
            return MLPrediction(
                model_type=ModelType.SENTIMENT_ANALYSIS,
                prediction=0.0,
                confidence=PredictionConfidence.LOW,
                features_used=[],
                timestamp=time.time(),
                model_version="error",
                metadata={"error": str(e)}
            )
    
    def assess_risk(self, market_data: Dict[str, Any]) -> MLPrediction:
        """
        Assess market risk.
        
        Args:
            market_data: Market data for risk assessment
            
        Returns:
            Risk assessment result
        """
        try:
            start_time = time.time()
            
            # Extract features
            features = self.extract_features(market_data)
            if "risk_assessment" not in features:
                return MLPrediction(
                    model_type=ModelType.RISK_ASSESSMENT,
                    prediction=0.5,
                    confidence=PredictionConfidence.LOW,
                    features_used=[],
                    timestamp=time.time(),
                    model_version="stub",
                    metadata={"error": "No features available"}
                )
            
            # Simple risk assessment (stub implementation)
            risk_score = 0.5  # Medium risk
            confidence = PredictionConfidence.LOW
            
            # Analyze volatility
            recent_prices = market_data.get("price_history", [])
            if len(recent_prices) >= 20:
                volatility = np.std(recent_prices[-20:]) / np.mean(recent_prices[-20:])
                if volatility > 0.1:
                    risk_score = 0.8  # High risk
                    confidence = PredictionConfidence.MEDIUM
                elif volatility < 0.05:
                    risk_score = 0.2  # Low risk
                    confidence = PredictionConfidence.MEDIUM
            
            execution_time = time.time() - start_time
            
            result = MLPrediction(
                model_type=ModelType.RISK_ASSESSMENT,
                prediction=risk_score,
                confidence=confidence,
                features_used=[f"feature_{i}" for i in range(len(features["risk_assessment"]))],
                timestamp=time.time(),
                model_version="stub_v1.0",
                metadata={"execution_time": execution_time}
            )
            
            self.prediction_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error("Failed to assess risk", error=str(e))
            return MLPrediction(
                model_type=ModelType.RISK_ASSESSMENT,
                prediction=0.5,
                confidence=PredictionConfidence.LOW,
                features_used=[],
                timestamp=time.time(),
                model_version="error",
                metadata={"error": str(e)}
            )
    
    def analyze_trend(self, market_data: Dict[str, Any]) -> MLPrediction:
        """
        Analyze market trend.
        
        Args:
            market_data: Market data for trend analysis
            
        Returns:
            Trend analysis result
        """
        try:
            start_time = time.time()
            
            # Extract features
            features = self.extract_features(market_data)
            if "trend_analysis" not in features:
                return MLPrediction(
                    model_type=ModelType.TREND_ANALYSIS,
                    prediction=0.0,
                    confidence=PredictionConfidence.LOW,
                    features_used=[],
                    timestamp=time.time(),
                    model_version="stub",
                    metadata={"error": "No features available"}
                )
            
            # Simple trend analysis (stub implementation)
            trend_score = 0.0  # No trend
            confidence = PredictionConfidence.LOW
            
            # Analyze price trend
            recent_prices = market_data.get("price_history", [])
            if len(recent_prices) >= 10:
                short_ma = np.mean(recent_prices[-5:])
                long_ma = np.mean(recent_prices[-10:])
                
                if short_ma > long_ma * 1.02:
                    trend_score = 0.7  # Uptrend
                    confidence = PredictionConfidence.MEDIUM
                elif short_ma < long_ma * 0.98:
                    trend_score = -0.7  # Downtrend
                    confidence = PredictionConfidence.MEDIUM
            
            execution_time = time.time() - start_time
            
            result = MLPrediction(
                model_type=ModelType.TREND_ANALYSIS,
                prediction=trend_score,
                confidence=confidence,
                features_used=[f"feature_{i}" for i in range(len(features["trend_analysis"]))],
                timestamp=time.time(),
                model_version="stub_v1.0",
                metadata={"execution_time": execution_time}
            )
            
            self.prediction_history.append(result)
            
            return result
            
        except Exception as e:
            logger.error("Failed to analyze trend", error=str(e))
            return MLPrediction(
                model_type=ModelType.TREND_ANALYSIS,
                prediction=0.0,
                confidence=PredictionConfidence.LOW,
                features_used=[],
                timestamp=time.time(),
                model_version="error",
                metadata={"error": str(e)}
            )
    
    def get_ml_decision(self, market_data: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Get ML-based trading decision.
        
        Args:
            market_data: Market data for decision making
            
        Returns:
            Tuple of (decision, reason, confidence)
        """
        try:
            # Get predictions from all models
            price_pred = self.predict_price(market_data)
            volume_pred = self.predict_volume(market_data)
            sentiment_pred = self.analyze_sentiment(market_data)
            risk_pred = self.assess_risk(market_data)
            trend_pred = self.analyze_trend(market_data)
            
            # Combine predictions for decision
            decision_score = 0.0
            confidence_scores = []
            reasons = []
            
            # Price prediction weight: 30%
            if price_pred.confidence != PredictionConfidence.LOW:
                decision_score += price_pred.prediction * 0.3
                confidence_scores.append(0.3)
                reasons.append(f"Price prediction: {price_pred.prediction:.3f}")
            
            # Volume prediction weight: 20%
            if volume_pred.confidence != PredictionConfidence.LOW:
                decision_score += volume_pred.prediction * 0.2
                confidence_scores.append(0.2)
                reasons.append(f"Volume prediction: {volume_pred.prediction:.3f}")
            
            # Sentiment analysis weight: 25%
            if sentiment_pred.confidence != PredictionConfidence.LOW:
                decision_score += sentiment_pred.prediction * 0.25
                confidence_scores.append(0.25)
                reasons.append(f"Sentiment: {sentiment_pred.prediction:.3f}")
            
            # Risk assessment weight: 15%
            if risk_pred.confidence != PredictionConfidence.LOW:
                decision_score += (1.0 - risk_pred.prediction) * 0.15
                confidence_scores.append(0.15)
                reasons.append(f"Risk assessment: {risk_pred.prediction:.3f}")
            
            # Trend analysis weight: 10%
            if trend_pred.confidence != PredictionConfidence.LOW:
                decision_score += trend_pred.prediction * 0.1
                confidence_scores.append(0.1)
                reasons.append(f"Trend analysis: {trend_pred.prediction:.3f}")
            
            # Calculate overall confidence
            overall_confidence = sum(confidence_scores) if confidence_scores else 0.0
            
            # Make decision based on score and confidence
            if overall_confidence < 0.3:
                return False, "Insufficient confidence for ML decision", 0.0
            
            decision = decision_score > 0.1  # Threshold for positive decision
            reason = f"ML decision score: {decision_score:.3f} ({', '.join(reasons)})"
            
            log_trading_event(
                "ml_decision_made",
                {
                    "decision": decision,
                    "score": decision_score,
                    "confidence": overall_confidence,
                    "reason": reason
                },
                "INFO"
            )
            
            return decision, reason, overall_confidence
            
        except Exception as e:
            logger.error("Failed to get ML decision", error=str(e))
            return False, f"ML decision error: {e}", 0.0
    
    def get_prediction_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about ML predictions.
        
        Returns:
            Dictionary with prediction statistics
        """
        try:
            if not self.prediction_history:
                return {"total_predictions": 0}
            
            # Calculate statistics by model type
            stats = {}
            for model_type in ModelType:
                model_predictions = [p for p in self.prediction_history if p.model_type == model_type]
                if model_predictions:
                    predictions = [p.prediction for p in model_predictions]
                    confidences = [p.confidence.value for p in model_predictions]
                    
                    stats[model_type.value] = {
                        "total_predictions": len(model_predictions),
                        "avg_prediction": np.mean(predictions),
                        "std_prediction": np.std(predictions),
                        "min_prediction": np.min(predictions),
                        "max_prediction": np.max(predictions),
                        "confidence_distribution": {
                            "low": confidences.count("low"),
                            "medium": confidences.count("medium"),
                            "high": confidences.count("high"),
                            "very_high": confidences.count("very_high")
                        }
                    }
            
            return {
                "total_predictions": len(self.prediction_history),
                "model_statistics": stats,
                "last_training": self.last_training
            }
            
        except Exception as e:
            logger.error("Failed to get prediction statistics", error=str(e))
            return {"error": str(e)}


# Global ML engine instance
_ml_engine: Optional[MLEngine] = None


def get_ml_engine() -> MLEngine:
    """
    Get the global ML engine instance.
    
    Returns:
        ML engine instance
    """
    global _ml_engine
    
    if _ml_engine is None:
        _ml_engine = MLEngine()
    
    return _ml_engine
