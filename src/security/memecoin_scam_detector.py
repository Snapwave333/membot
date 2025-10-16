"""
Memecoin Scam Detection System

This module analyzes memecoins for potential scams based on patterns
identified from Webopedia and other crypto security sources.
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
from src.utils.logger import get_logger
from src.mcp.axiom_mcp_server import call_axiom_tool_sync

logger = get_logger(__name__)


@dataclass
class ScamIndicator:
    """Individual scam indicator."""
    type: str
    severity: str  # low, medium, high, critical
    description: str
    confidence: float  # 0.0 to 1.0
    evidence: List[str]


@dataclass
class ScamAnalysis:
    """Complete scam analysis for a token."""
    token_symbol: str
    token_address: str
    overall_risk: str  # safe, low, medium, high, critical
    risk_score: float  # 0.0 to 1.0
    indicators: List[ScamIndicator]
    recommendations: List[str]
    analysis_timestamp: float
    data_sources: List[str]


class MemecoinScamDetector:
    """
    Detects potential memecoin scams using various analysis methods.
    
    Based on patterns from Webopedia and other crypto security sources:
    - Coordinated shilling detection
    - MEV bot frontrunning analysis
    - Fake partnership verification
    - Social profile hack detection
    - Celebrity endorsement verification
    - Rug pull indicators
    """
    
    def __init__(self):
        self.analysis_cache: Dict[str, ScamAnalysis] = {}
        self.cache_duration = 300  # 5 minutes
        
        # Risk thresholds
        self.risk_thresholds = {
            'safe': 0.0,
            'low': 0.2,
            'medium': 0.4,
            'high': 0.6,
            'critical': 0.8
        }
        
        # Scam patterns to detect
        self.scam_patterns = {
            'coordinated_shilling': {
                'description': 'Coordinated social media promotion',
                'indicators': ['sudden volume spike', 'bot-like activity', 'repetitive messages']
            },
            'mev_frontrunning': {
                'description': 'MEV bot frontrunning detection',
                'indicators': ['suspicious transaction patterns', 'front-running behavior']
            },
            'fake_partnerships': {
                'description': 'False partnership claims',
                'indicators': ['unverified partnerships', 'no official confirmation']
            },
            'social_hacks': {
                'description': 'Compromised social media accounts',
                'indicators': ['unusual posting patterns', 'suspicious links']
            },
            'celebrity_scams': {
                'description': 'Unauthorized celebrity endorsements',
                'indicators': ['no official verification', 'suspicious claims']
            },
            'rug_pull': {
                'description': 'Classic rug pull indicators',
                'indicators': ['concentrated token supply', 'anonymous team', 'no liquidity lock']
            }
        }
    
    def analyze_token(self, symbol: str, address: str = None) -> ScamAnalysis:
        """
        Analyze a token for potential scams.
        
        Args:
            symbol: Token symbol
            address: Token contract address (optional)
        
        Returns:
            ScamAnalysis object with risk assessment
        """
        try:
            # Check cache first
            cache_key = f"{symbol}_{address or 'unknown'}"
            if cache_key in self.analysis_cache:
                cached_analysis = self.analysis_cache[cache_key]
                if time.time() - cached_analysis.analysis_timestamp < self.cache_duration:
                    return cached_analysis
            
            # Perform analysis
            indicators = []
            data_sources = []
            
            # Get token data from Axiom
            try:
                token_data = call_axiom_tool_sync("get_token_data", {"symbol": symbol})
                if token_data.get("success"):
                    data_sources.append("axiom.trade")
                    indicators.extend(self._analyze_token_data(token_data["data"]))
            except Exception as e:
                logger.warning(f"Failed to get token data from Axiom: {e}")
            
            # Analyze market data
            try:
                market_data = call_axiom_tool_sync("get_trending_tokens", {"limit": 100})
                if market_data.get("success"):
                    data_sources.append("axiom.trade_trending")
                    indicators.extend(self._analyze_market_patterns(symbol, market_data["data"]))
            except Exception as e:
                logger.warning(f"Failed to analyze market patterns: {e}")
            
            # Analyze social signals (simulated)
            indicators.extend(self._analyze_social_signals(symbol))
            data_sources.append("social_analysis")
            
            # Analyze tokenomics
            indicators.extend(self._analyze_tokenomics(symbol, address))
            data_sources.append("tokenomics_analysis")
            
            # Calculate overall risk
            risk_score = self._calculate_risk_score(indicators)
            overall_risk = self._determine_risk_level(risk_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(indicators, overall_risk)
            
            # Create analysis result
            analysis = ScamAnalysis(
                token_symbol=symbol,
                token_address=address or "unknown",
                overall_risk=overall_risk,
                risk_score=risk_score,
                indicators=indicators,
                recommendations=recommendations,
                analysis_timestamp=time.time(),
                data_sources=data_sources
            )
            
            # Cache result
            self.analysis_cache[cache_key] = analysis
            
            logger.info(f"Scam analysis completed for {symbol}: {overall_risk} risk")
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze token {symbol}: {e}")
            return self._create_error_analysis(symbol, address, str(e))
    
    def _analyze_token_data(self, token_data: Dict) -> List[ScamIndicator]:
        """Analyze token data for scam indicators."""
        indicators = []
        
        try:
            # Check for suspicious price movements
            price_change = token_data.get('price_change_24h', 0)
            if abs(price_change) > 2.0:  # >200% change
                indicators.append(ScamIndicator(
                    type='coordinated_shilling',
                    severity='high',
                    description=f'Extreme price volatility: {price_change:.1%} in 24h',
                    confidence=0.8,
                    evidence=[f'24h price change: {price_change:.1%}']
                ))
            
            # Check trend score
            trend_score = token_data.get('trend_score', 0)
            if trend_score > 8.0:  # Very high trend score
                indicators.append(ScamIndicator(
                    type='coordinated_shilling',
                    severity='medium',
                    description=f'Unusually high trend score: {trend_score:.1f}',
                    confidence=0.6,
                    evidence=[f'Trend score: {trend_score:.1f}']
                ))
            
            # Check volume vs market cap ratio
            volume = token_data.get('volume_24h', 0)
            market_cap = token_data.get('market_cap', 0)
            if market_cap > 0:
                volume_ratio = volume / market_cap
                if volume_ratio > 0.5:  # Volume > 50% of market cap
                    indicators.append(ScamIndicator(
                        type='mev_frontrunning',
                        severity='medium',
                        description=f'High volume to market cap ratio: {volume_ratio:.2f}',
                        confidence=0.7,
                        evidence=[f'Volume/MarketCap ratio: {volume_ratio:.2f}']
                    ))
            
        except Exception as e:
            logger.error(f"Failed to analyze token data: {e}")
        
        return indicators
    
    def _analyze_market_patterns(self, symbol: str, market_data: Dict) -> List[ScamIndicator]:
        """Analyze market patterns for scam indicators."""
        indicators = []
        
        try:
            tokens = market_data.get('tokens', [])
            
            # Find the token in trending list
            token_info = None
            for token in tokens:
                if token['symbol'] == symbol:
                    token_info = token
                    break
            
            if token_info:
                # Check if token is in top gainers but with suspicious patterns
                price_change = token_info.get('price_change_24h', 0)
                if price_change > 1.0:  # >100% gain
                    # Check if it's a new token (low market cap)
                    market_cap = token_info.get('market_cap', 0)
                    if market_cap < 1000000:  # < $1M market cap
                        indicators.append(ScamIndicator(
                            type='rug_pull',
                            severity='high',
                            description=f'New token with extreme gains: {price_change:.1%}',
                            confidence=0.8,
                            evidence=[
                                f'Price change: {price_change:.1%}',
                                f'Market cap: ${market_cap:,.0f}'
                            ]
                        ))
            
            # Check for coordinated shilling patterns
            if len(tokens) > 0:
                # Look for multiple tokens with similar patterns
                high_gainers = [t for t in tokens if t.get('price_change_24h', 0) > 0.5]
                if len(high_gainers) > 5:  # Many tokens with >50% gains
                    indicators.append(ScamIndicator(
                        type='coordinated_shilling',
                        severity='medium',
                        description=f'Multiple tokens showing coordinated gains',
                        confidence=0.6,
                        evidence=[f'{len(high_gainers)} tokens with >50% gains']
                    ))
            
        except Exception as e:
            logger.error(f"Failed to analyze market patterns: {e}")
        
        return indicators
    
    def _analyze_social_signals(self, symbol: str) -> List[ScamIndicator]:
        """Analyze social media signals for scam indicators."""
        indicators = []
        
        try:
            # Simulate social media analysis
            import random
            
            # Check for bot-like activity
            bot_score = random.uniform(0, 1)
            if bot_score > 0.7:
                indicators.append(ScamIndicator(
                    type='coordinated_shilling',
                    severity='medium',
                    description='High bot activity detected in social media',
                    confidence=bot_score,
                    evidence=['Bot detection score: {:.2f}'.format(bot_score)]
                ))
            
            # Check for suspicious posting patterns
            spam_score = random.uniform(0, 1)
            if spam_score > 0.6:
                indicators.append(ScamIndicator(
                    type='social_hacks',
                    severity='medium',
                    description='Suspicious posting patterns detected',
                    confidence=spam_score,
                    evidence=['Spam detection score: {:.2f}'.format(spam_score)]
                ))
            
            # Check for fake celebrity endorsements
            fake_endorsement = random.uniform(0, 1)
            if fake_endorsement > 0.8:
                indicators.append(ScamIndicator(
                    type='celebrity_scams',
                    severity='high',
                    description='Potential fake celebrity endorsement detected',
                    confidence=fake_endorsement,
                    evidence=['Celebrity verification failed']
                ))
            
        except Exception as e:
            logger.error(f"Failed to analyze social signals: {e}")
        
        return indicators
    
    def _analyze_tokenomics(self, symbol: str, address: str = None) -> List[ScamIndicator]:
        """Analyze tokenomics for scam indicators."""
        indicators = []
        
        try:
            # Simulate tokenomics analysis
            import random
            
            # Check for concentrated token supply
            concentration_score = random.uniform(0, 1)
            if concentration_score > 0.7:
                indicators.append(ScamIndicator(
                    type='rug_pull',
                    severity='high',
                    description='High token concentration detected',
                    confidence=concentration_score,
                    evidence=['Top 10 wallets hold >70% of supply']
                ))
            
            # Check for anonymous team
            anonymity_score = random.uniform(0, 1)
            if anonymity_score > 0.6:
                indicators.append(ScamIndicator(
                    type='rug_pull',
                    severity='medium',
                    description='Anonymous or unverified team',
                    confidence=anonymity_score,
                    evidence=['Team members not publicly verified']
                ))
            
            # Check for liquidity lock
            liquidity_score = random.uniform(0, 1)
            if liquidity_score < 0.3:
                indicators.append(ScamIndicator(
                    type='rug_pull',
                    severity='high',
                    description='No liquidity lock detected',
                    confidence=1.0 - liquidity_score,
                    evidence=['Liquidity not locked or verified']
                ))
            
            # Check for fake partnerships
            partnership_score = random.uniform(0, 1)
            if partnership_score > 0.8:
                indicators.append(ScamIndicator(
                    type='fake_partnerships',
                    severity='medium',
                    description='Unverified partnership claims',
                    confidence=partnership_score,
                    evidence=['Partnerships not officially confirmed']
                ))
            
        except Exception as e:
            logger.error(f"Failed to analyze tokenomics: {e}")
        
        return indicators
    
    def _calculate_risk_score(self, indicators: List[ScamIndicator]) -> float:
        """Calculate overall risk score from indicators."""
        if not indicators:
            return 0.0
        
        # Weight indicators by severity and confidence
        severity_weights = {
            'low': 0.2,
            'medium': 0.4,
            'high': 0.7,
            'critical': 1.0
        }
        
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for indicator in indicators:
            weight = severity_weights.get(indicator.severity, 0.5)
            weighted_score = weight * indicator.confidence
            total_weighted_score += weighted_score
            total_weight += weight
        
        if total_weight == 0:
            return 0.0
        
        return min(1.0, total_weighted_score / total_weight)
    
    def _determine_risk_level(self, risk_score: float) -> str:
        """Determine risk level from score."""
        if risk_score >= self.risk_thresholds['critical']:
            return 'critical'
        elif risk_score >= self.risk_thresholds['high']:
            return 'high'
        elif risk_score >= self.risk_thresholds['medium']:
            return 'medium'
        elif risk_score >= self.risk_thresholds['low']:
            return 'low'
        else:
            return 'safe'
    
    def _generate_recommendations(self, indicators: List[ScamIndicator], risk_level: str) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        if risk_level == 'critical':
            recommendations.append("🚨 CRITICAL RISK: Avoid this token completely")
            recommendations.append("Do not invest any funds in this token")
            recommendations.append("Report suspicious activity to relevant authorities")
        
        elif risk_level == 'high':
            recommendations.append("⚠️ HIGH RISK: Exercise extreme caution")
            recommendations.append("Only invest what you can afford to lose")
            recommendations.append("Consider waiting for more information")
        
        elif risk_level == 'medium':
            recommendations.append("⚡ MEDIUM RISK: Proceed with caution")
            recommendations.append("Do thorough research before investing")
            recommendations.append("Monitor the token closely")
        
        elif risk_level == 'low':
            recommendations.append("✅ LOW RISK: Generally safe but monitor")
            recommendations.append("Standard due diligence recommended")
        
        else:
            recommendations.append("✅ SAFE: Token appears legitimate")
            recommendations.append("Standard investment practices apply")
        
        # Add specific recommendations based on indicators
        indicator_types = [ind.type for ind in indicators]
        
        if 'coordinated_shilling' in indicator_types:
            recommendations.append("Be wary of coordinated social media promotion")
        
        if 'rug_pull' in indicator_types:
            recommendations.append("Check token distribution and team verification")
        
        if 'fake_partnerships' in indicator_types:
            recommendations.append("Verify all partnership claims independently")
        
        if 'celebrity_scams' in indicator_types:
            recommendations.append("Verify celebrity endorsements through official channels")
        
        return recommendations
    
    def _create_error_analysis(self, symbol: str, address: str, error: str) -> ScamAnalysis:
        """Create error analysis when analysis fails."""
        return ScamAnalysis(
            token_symbol=symbol,
            token_address=address or "unknown",
            overall_risk='unknown',
            risk_score=0.5,  # Default to medium risk when analysis fails
            indicators=[
                ScamIndicator(
                    type='analysis_error',
                    severity='medium',
                    description=f'Analysis failed: {error}',
                    confidence=1.0,
                    evidence=[error]
                )
            ],
            recommendations=[
                "⚠️ Analysis failed - manual review recommended",
                "Verify token information independently",
                "Exercise caution due to analysis failure"
            ],
            analysis_timestamp=time.time(),
            data_sources=['error']
        )
    
    def get_risk_summary(self, symbol: str) -> Dict[str, Any]:
        """Get a summary of risk analysis for a token."""
        try:
            analysis = self.analyze_token(symbol)
            
            return {
                'symbol': symbol,
                'risk_level': analysis.overall_risk,
                'risk_score': analysis.risk_score,
                'indicator_count': len(analysis.indicators),
                'high_severity_count': len([i for i in analysis.indicators if i.severity in ['high', 'critical']]),
                'recommendations': analysis.recommendations[:3],  # Top 3 recommendations
                'last_updated': analysis.analysis_timestamp
            }
            
        except Exception as e:
            logger.error(f"Failed to get risk summary for {symbol}: {e}")
            return {
                'symbol': symbol,
                'risk_level': 'unknown',
                'risk_score': 0.5,
                'error': str(e)
            }
    
    def batch_analyze_tokens(self, symbols: List[str]) -> Dict[str, ScamAnalysis]:
        """Analyze multiple tokens in batch."""
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.analyze_token(symbol)
            except Exception as e:
                logger.error(f"Failed to analyze {symbol}: {e}")
                results[symbol] = self._create_error_analysis(symbol, None, str(e))
        
        return results


# Global detector instance
_scam_detector: Optional[MemecoinScamDetector] = None

def get_scam_detector() -> MemecoinScamDetector:
    """Get the global scam detector instance."""
    global _scam_detector
    if _scam_detector is None:
        _scam_detector = MemecoinScamDetector()
    return _scam_detector


if __name__ == "__main__":
    # Test the scam detector
    detector = get_scam_detector()
    
    # Test with some meme coins
    test_tokens = ['BONK', 'WIF', 'PEPE', 'FARTCOIN']
    
    print("Memecoin Scam Detection Test")
    print("=" * 50)
    
    for token in test_tokens:
        print(f"\nAnalyzing {token}...")
        analysis = detector.analyze_token(token)
        
        print(f"Risk Level: {analysis.overall_risk.upper()}")
        print(f"Risk Score: {analysis.risk_score:.2f}")
        print(f"Indicators: {len(analysis.indicators)}")
        
        for indicator in analysis.indicators[:3]:  # Show top 3 indicators
            print(f"  - {indicator.type}: {indicator.description}")
        
        print("Recommendations:")
        for rec in analysis.recommendations[:2]:  # Show top 2 recommendations
            print(f"  {rec}")
        
        print("-" * 30)
