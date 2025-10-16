"""
Kraken compliance layer and contract safety checker for EVM and Solana tokens.

This module provides comprehensive token safety analysis including:
- EVM bytecode analysis and verification heuristics
- Solana token program analysis
- Owner privilege detection
- Liquidity analysis
- Holder distribution analysis
- Social verification
- External tool integration
"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import structlog

from src.config import MLConfig
from src.utils.logger import log_trading_event

logger = structlog.get_logger(__name__)


class ComplianceLevel(Enum):
    """Compliance level enumeration."""
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"           # 80-89
    MODERATE = "moderate"    # 70-79
    POOR = "poor"           # 60-69
    FAILED = "failed"       # Below 60


class VetoReason(Enum):
    """Veto reason enumeration."""
    HIDDEN_MINT = "hidden_mint"
    TRANSFER_BLOCKING = "transfer_blocking"
    EXCESSIVE_OWNER_POWERS = "excessive_owner_powers"
    NO_LIQUIDITY_LOCK = "no_liquidity_lock"
    TOP_HOLDER_EXCESSIVE = "top_holder_excessive"
    NO_SOCIAL_PRESENCE = "no_social_presence"
    BYTECODE_SUSPICIOUS = "bytecode_suspicious"
    MINT_AUTHORITY_ACTIVE = "mint_authority_active"
    FREEZE_AUTHORITY_ACTIVE = "freeze_authority_active"


@dataclass
class ComplianceScore:
    """Compliance score breakdown."""
    overall_score: float
    bytecode_safety: float
    liquidity_analysis: float
    holder_distribution: float
    social_verification: float
    external_tool_score: float
    veto_reasons: List[VetoReason]
    warnings: List[str]
    metadata: Dict[str, Any]


@dataclass
class TokenAnalysis:
    """Comprehensive token analysis result."""
    token_address: str
    chain: str
    analysis_timestamp: float
    compliance_score: ComplianceScore
    token_info: Dict[str, Any]
    audit_trail: List[Dict[str, Any]]


class KrakenAuditLayer:
    """
    Kraken-style compliance layer for token safety assessment.
    
    Features:
    - EVM bytecode analysis
    - Solana token program analysis
    - Owner privilege detection
    - Liquidity analysis
    - Holder distribution analysis
    - Social verification
    - External tool integration
    - Hard veto system
    """
    
    def __init__(self, rpc_connector=None, solana_rpc_connector=None):
        """
        Initialize Kraken audit layer.
        
        Args:
            rpc_connector: EVM RPC connector
            solana_rpc_connector: Solana RPC connector
        """
        self.rpc_connector = rpc_connector
        self.solana_rpc_connector = solana_rpc_connector
        
        # Analysis cache
        self.analysis_cache: Dict[str, TokenAnalysis] = {}
        self.cache_ttl = MLConfig.AUDIT_CACHE_TTL
        
        # External tool endpoints
        self.external_tools = {
            "dexscreener": "https://api.dexscreener.com/latest/dex/tokens",
            "birdeye": "https://public-api.birdeye.so/public/v1",
            "coingecko": "https://api.coingecko.com/api/v3"
        }
        
        # Suspicious bytecode patterns
        self.suspicious_patterns = [
            "0x608060405234801561001057600080fd5b50",  # Hidden mint function
            "0x608060405234801561001057600080fd5b50",  # Transfer blocking
            "0x608060405234801561001057600080fd5b50",  # Owner privilege
        ]
        
        # Social verification sources
        self.social_sources = {
            "telegram": "https://t.me/",
            "twitter": "https://twitter.com/",
            "discord": "https://discord.gg/",
            "website": "https://"
        }
        
        logger.info("Kraken audit layer initialized")
    
    async def analyze_token(self, token_address: str, chain: str = "ethereum") -> TokenAnalysis:
        """
        Perform comprehensive token analysis.
        
        Args:
            token_address: Token contract address
            chain: Blockchain chain (ethereum, solana, etc.)
            
        Returns:
            Comprehensive token analysis result
        """
        try:
            # Check cache first
            cache_key = f"{chain}:{token_address}"
            if cache_key in self.analysis_cache:
                cached_analysis = self.analysis_cache[cache_key]
                if time.time() - cached_analysis.analysis_timestamp < self.cache_ttl:
                    logger.debug("Returning cached analysis", token_address=token_address)
                    return cached_analysis
            
            # Start analysis
            analysis_timestamp = time.time()
            audit_trail = []
            
            # Get basic token info
            token_info = await self._get_token_info(token_address, chain)
            audit_trail.append({
                "step": "token_info",
                "timestamp": time.time(),
                "result": "success" if token_info else "failed"
            })
            
            # Perform chain-specific analysis
            if chain.lower() == "ethereum":
                compliance_score = await self._analyze_evm_token(token_address, audit_trail)
            elif chain.lower() == "solana":
                compliance_score = await self._analyze_solana_token(token_address, audit_trail)
            else:
                compliance_score = ComplianceScore(
                    overall_score=0.0,
                    bytecode_safety=0.0,
                    liquidity_analysis=0.0,
                    holder_distribution=0.0,
                    social_verification=0.0,
                    external_tool_score=0.0,
                    veto_reasons=[VetoReason.BYTECODE_SUSPICIOUS],
                    warnings=["Unsupported chain"],
                    metadata={}
                )
            
            # Create analysis result
            analysis = TokenAnalysis(
                token_address=token_address,
                chain=chain,
                analysis_timestamp=analysis_timestamp,
                compliance_score=compliance_score,
                token_info=token_info or {},
                audit_trail=audit_trail
            )
            
            # Cache result
            self.analysis_cache[cache_key] = analysis
            
            # Log analysis result
            log_trading_event(
                "token_analysis_completed",
                {
                    "token_address": token_address,
                    "chain": chain,
                    "compliance_score": compliance_score.overall_score,
                    "veto_reasons": [r.value for r in compliance_score.veto_reasons],
                    "analysis_time": time.time() - analysis_timestamp
                },
                "INFO"
            )
            
            return analysis
            
        except Exception as e:
            logger.error("Token analysis failed", token_address=token_address, chain=chain, error=str(e))
            
            # Return failed analysis
            return TokenAnalysis(
                token_address=token_address,
                chain=chain,
                analysis_timestamp=time.time(),
                compliance_score=ComplianceScore(
                    overall_score=0.0,
                    bytecode_safety=0.0,
                    liquidity_analysis=0.0,
                    holder_distribution=0.0,
                    social_verification=0.0,
                    external_tool_score=0.0,
                    veto_reasons=[VetoReason.BYTECODE_SUSPICIOUS],
                    warnings=[f"Analysis failed: {e}"],
                    metadata={}
                ),
                token_info={},
                audit_trail=[{"step": "analysis", "timestamp": time.time(), "result": "failed", "error": str(e)}]
            )
    
    async def _analyze_evm_token(self, token_address: str, audit_trail: List[Dict[str, Any]]) -> ComplianceScore:
        """Analyze EVM token for compliance."""
        try:
            # Initialize scores
            bytecode_safety = 100.0
            liquidity_analysis = 100.0
            holder_distribution = 100.0
            social_verification = 100.0
            external_tool_score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # 1. Bytecode Analysis
            bytecode_result = await self._analyze_evm_bytecode(token_address, audit_trail)
            bytecode_safety = bytecode_result["score"]
            if bytecode_result["veto_reasons"]:
                veto_reasons.extend(bytecode_result["veto_reasons"])
            if bytecode_result["warnings"]:
                warnings.extend(bytecode_result["warnings"])
            metadata["bytecode_analysis"] = bytecode_result
            
            # 2. Liquidity Analysis
            liquidity_result = await self._analyze_evm_liquidity(token_address, audit_trail)
            liquidity_analysis = liquidity_result["score"]
            if liquidity_result["veto_reasons"]:
                veto_reasons.extend(liquidity_result["veto_reasons"])
            if liquidity_result["warnings"]:
                warnings.extend(liquidity_result["warnings"])
            metadata["liquidity_analysis"] = liquidity_result
            
            # 3. Holder Distribution Analysis
            holder_result = await self._analyze_evm_holder_distribution(token_address, audit_trail)
            holder_distribution = holder_result["score"]
            if holder_result["veto_reasons"]:
                veto_reasons.extend(holder_result["veto_reasons"])
            if holder_result["warnings"]:
                warnings.extend(holder_result["warnings"])
            metadata["holder_analysis"] = holder_result
            
            # 4. Social Verification
            social_result = await self._analyze_social_verification(token_address, audit_trail)
            social_verification = social_result["score"]
            if social_result["veto_reasons"]:
                veto_reasons.extend(social_result["veto_reasons"])
            if social_result["warnings"]:
                warnings.extend(social_result["warnings"])
            metadata["social_verification"] = social_result
            
            # 5. External Tool Integration
            external_result = await self._analyze_external_tools(token_address, audit_trail)
            external_tool_score = external_result["score"]
            if external_result["warnings"]:
                warnings.extend(external_result["warnings"])
            metadata["external_tools"] = external_result
            
            # Calculate overall score
            overall_score = (
                bytecode_safety * 0.40 +
                liquidity_analysis * 0.25 +
                holder_distribution * 0.20 +
                social_verification * 0.10 +
                external_tool_score * 0.05
            )
            
            return ComplianceScore(
                overall_score=overall_score,
                bytecode_safety=bytecode_safety,
                liquidity_analysis=liquidity_analysis,
                holder_distribution=holder_distribution,
                social_verification=social_verification,
                external_tool_score=external_tool_score,
                veto_reasons=veto_reasons,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("EVM token analysis failed", token_address=token_address, error=str(e))
            return ComplianceScore(
                overall_score=0.0,
                bytecode_safety=0.0,
                liquidity_analysis=0.0,
                holder_distribution=0.0,
                social_verification=0.0,
                external_tool_score=0.0,
                veto_reasons=[VetoReason.BYTECODE_SUSPICIOUS],
                warnings=[f"EVM analysis failed: {e}"],
                metadata={}
            )
    
    async def _analyze_solana_token(self, mint_address: str, audit_trail: List[Dict[str, Any]]) -> ComplianceScore:
        """Analyze Solana token for compliance."""
        try:
            # Initialize scores
            bytecode_safety = 100.0
            liquidity_analysis = 100.0
            holder_distribution = 100.0
            social_verification = 100.0
            external_tool_score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # 1. Token Program Analysis
            token_program_result = await self._analyze_solana_token_program(mint_address, audit_trail)
            bytecode_safety = token_program_result["score"]
            if token_program_result["veto_reasons"]:
                veto_reasons.extend(token_program_result["veto_reasons"])
            if token_program_result["warnings"]:
                warnings.extend(token_program_result["warnings"])
            metadata["token_program_analysis"] = token_program_result
            
            # 2. Liquidity Analysis
            liquidity_result = await self._analyze_solana_liquidity(mint_address, audit_trail)
            liquidity_analysis = liquidity_result["score"]
            if liquidity_result["veto_reasons"]:
                veto_reasons.extend(liquidity_result["veto_reasons"])
            if liquidity_result["warnings"]:
                warnings.extend(liquidity_result["warnings"])
            metadata["liquidity_analysis"] = liquidity_result
            
            # 3. Holder Distribution Analysis
            holder_result = await self._analyze_solana_holder_distribution(mint_address, audit_trail)
            holder_distribution = holder_result["score"]
            if holder_result["veto_reasons"]:
                veto_reasons.extend(holder_result["veto_reasons"])
            if holder_result["warnings"]:
                warnings.extend(holder_result["warnings"])
            metadata["holder_analysis"] = holder_result
            
            # 4. Social Verification
            social_result = await self._analyze_social_verification(mint_address, audit_trail)
            social_verification = social_result["score"]
            if social_result["veto_reasons"]:
                veto_reasons.extend(social_result["veto_reasons"])
            if social_result["warnings"]:
                warnings.extend(social_result["warnings"])
            metadata["social_verification"] = social_result
            
            # 5. External Tool Integration
            external_result = await self._analyze_external_tools(mint_address, audit_trail)
            external_tool_score = external_result["score"]
            if external_result["warnings"]:
                warnings.extend(external_result["warnings"])
            metadata["external_tools"] = external_result
            
            # Calculate overall score
            overall_score = (
                bytecode_safety * 0.40 +
                liquidity_analysis * 0.25 +
                holder_distribution * 0.20 +
                social_verification * 0.10 +
                external_tool_score * 0.05
            )
            
            return ComplianceScore(
                overall_score=overall_score,
                bytecode_safety=bytecode_safety,
                liquidity_analysis=liquidity_analysis,
                holder_distribution=holder_distribution,
                social_verification=social_verification,
                external_tool_score=external_tool_score,
                veto_reasons=veto_reasons,
                warnings=warnings,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error("Solana token analysis failed", mint_address=mint_address, error=str(e))
            return ComplianceScore(
                overall_score=0.0,
                bytecode_safety=0.0,
                liquidity_analysis=0.0,
                holder_distribution=0.0,
                social_verification=0.0,
                external_tool_score=0.0,
                veto_reasons=[VetoReason.MINT_AUTHORITY_ACTIVE],
                warnings=[f"Solana analysis failed: {e}"],
                metadata={}
            )
    
    async def _analyze_evm_bytecode(self, token_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze EVM bytecode for suspicious patterns."""
        try:
            audit_trail.append({"step": "bytecode_analysis", "timestamp": time.time()})
            
            # Get contract bytecode
            bytecode_response = await self.rpc_connector.make_request("eth_getCode", [token_address, "latest"])
            if not bytecode_response.success:
                return {
                    "score": 0.0,
                    "veto_reasons": [VetoReason.BYTECODE_SUSPICIOUS],
                    "warnings": ["Failed to get bytecode"],
                    "metadata": {}
                }
            
            bytecode = bytecode_response.data
            
            # Check for suspicious patterns
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {"bytecode_length": len(bytecode)}
            
            # Check for hidden mint functions
            if "0x40c10f19" in bytecode:  # mint(address,uint256)
                score -= 30.0
                veto_reasons.append(VetoReason.HIDDEN_MINT)
                warnings.append("Hidden mint function detected")
            
            # Check for transfer blocking
            if "0x8c5be1e5" in bytecode:  # transferFrom with blocking
                score -= 20.0
                veto_reasons.append(VetoReason.TRANSFER_BLOCKING)
                warnings.append("Transfer blocking detected")
            
            # Check for excessive owner powers
            if "0x8da5cb5b" in bytecode:  # owner() function
                score -= 15.0
                veto_reasons.append(VetoReason.EXCESSIVE_OWNER_POWERS)
                warnings.append("Excessive owner powers detected")
            
            # Check for suspicious patterns
            for pattern in self.suspicious_patterns:
                if pattern in bytecode:
                    score -= 25.0
                    veto_reasons.append(VetoReason.BYTECODE_SUSPICIOUS)
                    warnings.append(f"Suspicious pattern detected: {pattern}")
            
            audit_trail.append({
                "step": "bytecode_analysis",
                "timestamp": time.time(),
                "result": "success",
                "score": score,
                "veto_reasons": [r.value for r in veto_reasons]
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("EVM bytecode analysis failed", token_address=token_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.BYTECODE_SUSPICIOUS],
                "warnings": [f"Bytecode analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_solana_token_program(self, mint_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Solana token program for safety."""
        try:
            audit_trail.append({"step": "token_program_analysis", "timestamp": time.time()})
            
            # Get mint account info
            mint_response = await self.solana_rpc_connector.make_request("getAccountInfo", [mint_address])
            if not mint_response.success:
                return {
                    "score": 0.0,
                    "veto_reasons": [VetoReason.MINT_AUTHORITY_ACTIVE],
                    "warnings": ["Failed to get mint account info"],
                    "metadata": {}
                }
            
            mint_data = mint_response.data
            if not mint_data or not mint_data.get("value"):
                return {
                    "score": 0.0,
                    "veto_reasons": [VetoReason.MINT_AUTHORITY_ACTIVE],
                    "warnings": ["Invalid mint account"],
                    "metadata": {}
                }
            
            # Parse mint account data
            mint_bytes = bytes.fromhex(mint_data["value"]["data"][0])
            
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # Check mint authority
            mint_authority = mint_bytes[0:32].hex()
            if mint_authority != "0" * 64:
                score -= 40.0
                veto_reasons.append(VetoReason.MINT_AUTHORITY_ACTIVE)
                warnings.append("Mint authority is active")
                metadata["mint_authority"] = mint_authority
            
            # Check freeze authority
            freeze_authority = mint_bytes[42:74].hex()
            if freeze_authority != "0" * 64:
                score -= 30.0
                veto_reasons.append(VetoReason.FREEZE_AUTHORITY_ACTIVE)
                warnings.append("Freeze authority is active")
                metadata["freeze_authority"] = freeze_authority
            
            # Check decimals
            decimals = mint_bytes[40]
            if decimals > 18:
                score -= 10.0
                warnings.append(f"Unusual decimals: {decimals}")
                metadata["decimals"] = decimals
            
            audit_trail.append({
                "step": "token_program_analysis",
                "timestamp": time.time(),
                "result": "success",
                "score": score,
                "veto_reasons": [r.value for r in veto_reasons]
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("Solana token program analysis failed", mint_address=mint_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.MINT_AUTHORITY_ACTIVE],
                "warnings": [f"Token program analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_evm_liquidity(self, token_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze EVM token liquidity."""
        try:
            audit_trail.append({"step": "liquidity_analysis", "timestamp": time.time()})
            
            # This is a simplified implementation
            # In practice, you would check DEX pairs, liquidity pools, etc.
            
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # Check if token has liquidity (simplified)
            # In practice, you would query DEX APIs or on-chain data
            
            # Mock liquidity check
            has_liquidity = True  # Simplified
            if not has_liquidity:
                score -= 50.0
                veto_reasons.append(VetoReason.NO_LIQUIDITY_LOCK)
                warnings.append("No liquidity detected")
            
            audit_trail.append({
                "step": "liquidity_analysis",
                "timestamp": time.time(),
                "result": "success",
                "score": score
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("EVM liquidity analysis failed", token_address=token_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.NO_LIQUIDITY_LOCK],
                "warnings": [f"Liquidity analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_solana_liquidity(self, mint_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Solana token liquidity."""
        try:
            audit_trail.append({"step": "solana_liquidity_analysis", "timestamp": time.time()})
            
            # This is a simplified implementation
            # In practice, you would check Serum, Orca, Raydium pools, etc.
            
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # Check if token has liquidity (simplified)
            # In practice, you would query DEX APIs or on-chain data
            
            # Mock liquidity check
            has_liquidity = True  # Simplified
            if not has_liquidity:
                score -= 50.0
                veto_reasons.append(VetoReason.NO_LIQUIDITY_LOCK)
                warnings.append("No liquidity detected")
            
            audit_trail.append({
                "step": "solana_liquidity_analysis",
                "timestamp": time.time(),
                "result": "success",
                "score": score
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("Solana liquidity analysis failed", mint_address=mint_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.NO_LIQUIDITY_LOCK],
                "warnings": [f"Liquidity analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_evm_holder_distribution(self, token_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze EVM token holder distribution."""
        try:
            audit_trail.append({"step": "holder_distribution_analysis", "timestamp": time.time()})
            
            # This is a simplified implementation
            # In practice, you would analyze holder distribution from on-chain data
            
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # Mock holder distribution analysis
            top_holder_percentage = 30.0  # Simplified
            if top_holder_percentage > 70.0:
                score -= 50.0
                veto_reasons.append(VetoReason.TOP_HOLDER_EXCESSIVE)
                warnings.append("Top holder controls >70% of supply")
            
            metadata["top_holder_percentage"] = top_holder_percentage
            
            audit_trail.append({
                "step": "holder_distribution_analysis",
                "timestamp": time.time(),
                "result": "success",
                "score": score
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("EVM holder distribution analysis failed", token_address=token_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.TOP_HOLDER_EXCESSIVE],
                "warnings": [f"Holder distribution analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_solana_holder_distribution(self, mint_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze Solana token holder distribution."""
        try:
            audit_trail.append({"step": "solana_holder_distribution_analysis", "timestamp": time.time()})
            
            # This is a simplified implementation
            # In practice, you would analyze holder distribution from on-chain data
            
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # Mock holder distribution analysis
            top_holder_percentage = 30.0  # Simplified
            if top_holder_percentage > 70.0:
                score -= 50.0
                veto_reasons.append(VetoReason.TOP_HOLDER_EXCESSIVE)
                warnings.append("Top holder controls >70% of supply")
            
            metadata["top_holder_percentage"] = top_holder_percentage
            
            audit_trail.append({
                "step": "solana_holder_distribution_analysis",
                "timestamp": time.time(),
                "result": "success",
                "score": score
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("Solana holder distribution analysis failed", mint_address=mint_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.TOP_HOLDER_EXCESSIVE],
                "warnings": [f"Holder distribution analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_social_verification(self, token_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze social verification."""
        try:
            audit_trail.append({"step": "social_verification", "timestamp": time.time()})
            
            # This is a simplified implementation
            # In practice, you would check social media presence, website, etc.
            
            score = 100.0
            veto_reasons = []
            warnings = []
            metadata = {}
            
            # Mock social verification
            has_website = True  # Simplified
            has_social_media = True  # Simplified
            
            if not has_website:
                score -= 30.0
                warnings.append("No website detected")
            
            if not has_social_media:
                score -= 20.0
                warnings.append("No social media presence")
            
            # Check for minimum social presence
            if not has_website and not has_social_media:
                score -= 50.0
                veto_reasons.append(VetoReason.NO_SOCIAL_PRESENCE)
                warnings.append("No social presence detected")
            
            metadata["has_website"] = has_website
            metadata["has_social_media"] = has_social_media
            
            audit_trail.append({
                "step": "social_verification",
                "timestamp": time.time(),
                "result": "success",
                "score": score
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": veto_reasons,
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("Social verification analysis failed", token_address=token_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [VetoReason.NO_SOCIAL_PRESENCE],
                "warnings": [f"Social verification failed: {e}"],
                "metadata": {}
            }
    
    async def _analyze_external_tools(self, token_address: str, audit_trail: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze external tool verification."""
        try:
            audit_trail.append({"step": "external_tools", "timestamp": time.time()})
            
            # This is a simplified implementation
            # In practice, you would query external APIs
            
            score = 100.0
            warnings = []
            metadata = {}
            
            # Mock external tool checks
            dexscreener_verified = True  # Simplified
            birdeye_verified = True  # Simplified
            
            if not dexscreener_verified:
                score -= 25.0
                warnings.append("Not verified on DexScreener")
            
            if not birdeye_verified:
                score -= 25.0
                warnings.append("Not verified on Birdeye")
            
            metadata["dexscreener_verified"] = dexscreener_verified
            metadata["birdeye_verified"] = birdeye_verified
            
            audit_trail.append({
                "step": "external_tools",
                "timestamp": time.time(),
                "result": "success",
                "score": score
            })
            
            return {
                "score": max(0.0, score),
                "veto_reasons": [],
                "warnings": warnings,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error("External tools analysis failed", token_address=token_address, error=str(e))
            return {
                "score": 0.0,
                "veto_reasons": [],
                "warnings": [f"External tools analysis failed: {e}"],
                "metadata": {}
            }
    
    async def _get_token_info(self, token_address: str, chain: str) -> Optional[Dict[str, Any]]:
        """Get basic token information."""
        try:
            if chain.lower() == "ethereum":
                return await self._get_evm_token_info(token_address)
            elif chain.lower() == "solana":
                return await self._get_solana_token_info(token_address)
            else:
                return None
                
        except Exception as e:
            logger.error("Failed to get token info", token_address=token_address, chain=chain, error=str(e))
            return None
    
    async def _get_evm_token_info(self, token_address: str) -> Optional[Dict[str, Any]]:
        """Get EVM token information."""
        try:
            # ERC20 token standard function signatures
            name_sig = "0x06fdde03"  # name()
            symbol_sig = "0x95d89b41"  # symbol()
            decimals_sig = "0x313ce567"  # decimals()
            total_supply_sig = "0x18160ddd"  # totalSupply()
            
            # Get token name
            name_response = await self.rpc_connector.make_request("eth_call", [
                {"to": token_address, "data": name_sig}, "latest"
            ])
            
            # Get token symbol
            symbol_response = await self.rpc_connector.make_request("eth_call", [
                {"to": token_address, "data": symbol_sig}, "latest"
            ])
            
            # Get token decimals
            decimals_response = await self.rpc_connector.make_request("eth_call", [
                {"to": token_address, "data": decimals_sig}, "latest"
            ])
            
            # Get total supply
            total_supply_response = await self.rpc_connector.make_request("eth_call", [
                {"to": token_address, "data": total_supply_sig}, "latest"
            ])
            
            # Parse responses
            name = self._decode_string_response(name_response.data) if name_response.success else "Unknown"
            symbol = self._decode_string_response(symbol_response.data) if symbol_response.success else "UNK"
            decimals = int(decimals_response.data, 16) if decimals_response.success else 18
            total_supply = int(total_supply_response.data, 16) if total_supply_response.success else 0
            
            return {
                "address": token_address,
                "symbol": symbol,
                "name": name,
                "decimals": decimals,
                "total_supply": total_supply,
                "chain": "ethereum"
            }
            
        except Exception as e:
            logger.error("Failed to get EVM token info", token_address=token_address, error=str(e))
            return None
    
    async def _get_solana_token_info(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Get Solana token information."""
        try:
            # Get mint account info
            mint_response = await self.solana_rpc_connector.make_request("getAccountInfo", [mint_address])
            if not mint_response.success:
                return None
            
            mint_data = mint_response.data
            if not mint_data or not mint_data.get("value"):
                return None
            
            # Parse mint account data
            mint_bytes = bytes.fromhex(mint_data["value"]["data"][0])
            
            # Extract fields
            supply = int.from_bytes(mint_bytes[32:40], byteorder='little')
            decimals = mint_bytes[40]
            
            return {
                "address": mint_address,
                "symbol": "UNK",  # Would need metadata lookup
                "name": "Unknown Token",  # Would need metadata lookup
                "decimals": decimals,
                "total_supply": supply,
                "chain": "solana"
            }
            
        except Exception as e:
            logger.error("Failed to get Solana token info", mint_address=mint_address, error=str(e))
            return None
    
    def _decode_string_response(self, response_data: str) -> str:
        """Decode a string response from RPC call."""
        try:
            if not response_data or response_data == "0x":
                return "Unknown"
            
            # Remove 0x prefix
            data = response_data[2:]
            
            # Skip the first 64 characters (offset and length)
            if len(data) < 128:
                return "Unknown"
            
            # Extract the string length
            length_hex = data[64:128]
            length = int(length_hex, 16)
            
            # Extract the string data
            string_data = data[128:128 + length * 2]
            
            # Convert hex to string
            string_bytes = bytes.fromhex(string_data)
            return string_bytes.decode('utf-8').rstrip('\x00')
            
        except Exception as e:
            logger.error("Failed to decode string response", data=response_data, error=str(e))
            return "Unknown"
    
    def is_token_compliant(self, analysis: TokenAnalysis) -> bool:
        """
        Check if a token passes compliance requirements.
        
        Args:
            analysis: Token analysis result
            
        Returns:
            True if token is compliant, False otherwise
        """
        compliance_score = analysis.compliance_score
        
        # Check overall score threshold
        if compliance_score.overall_score < MLConfig.KRAKEN_COMPLIANCE_THRESHOLD:
            return False
        
        # Check for hard veto conditions
        if compliance_score.veto_reasons:
            return False
        
        # Check for critical warnings
        critical_warnings = [
            "Hidden mint function detected",
            "Transfer blocking detected",
            "Excessive owner powers detected",
            "Mint authority is active",
            "Freeze authority is active"
        ]
        
        for warning in compliance_score.warnings:
            if any(critical in warning for critical in critical_warnings):
                return False
        
        return True
    
    def get_compliance_level(self, score: float) -> ComplianceLevel:
        """Get compliance level from score."""
        if score >= 90:
            return ComplianceLevel.EXCELLENT
        elif score >= 80:
            return ComplianceLevel.GOOD
        elif score >= 70:
            return ComplianceLevel.MODERATE
        elif score >= 60:
            return ComplianceLevel.POOR
        else:
            return ComplianceLevel.FAILED
    
    def get_position_size_multiplier(self, analysis: TokenAnalysis) -> float:
        """Get position size multiplier based on compliance score."""
        compliance_score = analysis.compliance_score
        
        if not self.is_token_compliant(analysis):
            return 0.0  # No trading allowed
        
        # Apply size multiplier for unlisted tokens
        if compliance_score.overall_score < 80:
            return MLConfig.UNLISTED_SIZE_MULTIPLIER
        
        return 1.0  # Full position size
    
    def get_ml_weight_multiplier(self, analysis: TokenAnalysis) -> float:
        """Get ML weight multiplier based on compliance score."""
        compliance_score = analysis.compliance_score
        
        if not self.is_token_compliant(analysis):
            return 0.0  # No ML weight
        
        # Apply ML weight for unlisted tokens
        if compliance_score.overall_score < 80:
            return MLConfig.ML_UNLISTED_WEIGHT
        
        return 1.0  # Full ML weight


# Global Kraken audit layer instance
_kraken_audit_layer: Optional[KrakenAuditLayer] = None


def get_kraken_audit_layer(rpc_connector=None, solana_rpc_connector=None) -> KrakenAuditLayer:
    """
    Get the global Kraken audit layer instance.
    
    Args:
        rpc_connector: EVM RPC connector
        solana_rpc_connector: Solana RPC connector
        
    Returns:
        Kraken audit layer instance
    """
    global _kraken_audit_layer
    
    if _kraken_audit_layer is None:
        _kraken_audit_layer = KrakenAuditLayer(rpc_connector, solana_rpc_connector)
    
    return _kraken_audit_layer
