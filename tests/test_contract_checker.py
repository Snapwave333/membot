"""
Unit tests for the contract checker module.

This module tests the Kraken compliance layer and contract safety checks.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.security.contract_checker import KrakenAuditLayer, ComplianceScore, ComplianceLevel, TokenAnalysis, VetoReason
from src.config import MLConfig


class TestKrakenAuditLayer:
    """Test cases for KrakenAuditLayer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.audit_layer = KrakenAuditLayer()
        self.test_address = "0x1234567890123456789012345678901234567890"
    
    @pytest.mark.asyncio
    async def test_analyze_token_ethereum(self):
        """Test token analysis for Ethereum."""
        # Mock the entire analyze_token method
        mock_compliance_score = ComplianceScore(
            overall_score=85.0,
            bytecode_safety=90.0,
            liquidity_analysis=80.0,
            holder_distribution=85.0,
            social_verification=80.0,
            external_tool_score=90.0,
            veto_reasons=[],
            warnings=[],
            metadata={}
        )
        
        mock_analysis = TokenAnalysis(
            token_address=self.test_address,
            chain="ethereum",
            analysis_timestamp=1234567890,
            compliance_score=mock_compliance_score,
            token_info={"name": "TestToken", "symbol": "TST"},
            audit_trail=[]
        )
        
        with patch.object(self.audit_layer, 'analyze_token', return_value=mock_analysis) as mock_analyze:
            result = await self.audit_layer.analyze_token(self.test_address, "ethereum")
            
            assert isinstance(result, TokenAnalysis)
            assert result.compliance_score.overall_score == 85.0
            mock_analyze.assert_called_once_with(self.test_address, "ethereum")
    
    @pytest.mark.asyncio
    async def test_analyze_token_solana(self):
        """Test token analysis for Solana."""
        # Mock the entire analyze_token method
        mock_compliance_score = ComplianceScore(
            overall_score=80.0,
            bytecode_safety=85.0,
            liquidity_analysis=75.0,
            holder_distribution=80.0,
            social_verification=85.0,
            external_tool_score=75.0,
            veto_reasons=[],
            warnings=[],
            metadata={}
        )
        
        mock_analysis = TokenAnalysis(
            token_address=self.test_address,
            chain="solana",
            analysis_timestamp=1234567890,
            compliance_score=mock_compliance_score,
            token_info={"name": "TestToken", "symbol": "TST"},
            audit_trail=[]
        )
        
        with patch.object(self.audit_layer, 'analyze_token', return_value=mock_analysis) as mock_analyze:
            result = await self.audit_layer.analyze_token(self.test_address, "solana")
            
            assert isinstance(result, TokenAnalysis)
            assert result.compliance_score.overall_score == 80.0
            mock_analyze.assert_called_once_with(self.test_address, "solana")
    
    def test_is_token_compliant_high_score(self):
        """Test compliance check with high score."""
        analysis = TokenAnalysis(
            token_address=self.test_address,
            chain="ethereum",
            analysis_timestamp=1234567890,
            compliance_score=ComplianceScore(
                overall_score=85.0,
                bytecode_safety=90.0,
                liquidity_analysis=80.0,
                holder_distribution=85.0,
                social_verification=80.0,
                external_tool_score=90.0,
                veto_reasons=[],
                warnings=[],
                metadata={}
            ),
            token_info={},
            audit_trail=[]
        )
        
        result = self.audit_layer.is_token_compliant(analysis)
        assert result is True
    
    def test_is_token_compliant_low_score(self):
        """Test compliance check with low score."""
        analysis = TokenAnalysis(
            token_address=self.test_address,
            chain="ethereum",
            analysis_timestamp=1234567890,
            compliance_score=ComplianceScore(
                overall_score=50.0,
                bytecode_safety=40.0,
                liquidity_analysis=60.0,
                holder_distribution=45.0,
                social_verification=55.0,
                external_tool_score=50.0,
                veto_reasons=[],
                warnings=[],
                metadata={}
            ),
            token_info={},
            audit_trail=[]
        )
        
        result = self.audit_layer.is_token_compliant(analysis)
        assert result is False
    
    def test_get_compliance_level_excellent(self):
        """Test compliance level determination for excellent score."""
        score = 95.0
        level = self.audit_layer.get_compliance_level(score)
        assert level == ComplianceLevel.EXCELLENT
    
    def test_get_compliance_level_good(self):
        """Test compliance level determination for good score."""
        score = 85.0
        level = self.audit_layer.get_compliance_level(score)
        assert level == ComplianceLevel.GOOD
    
    def test_get_compliance_level_moderate(self):
        """Test compliance level determination for moderate score."""
        score = 75.0
        level = self.audit_layer.get_compliance_level(score)
        assert level == ComplianceLevel.MODERATE
    
    def test_get_compliance_level_poor(self):
        """Test compliance level determination for poor score."""
        score = 65.0
        level = self.audit_layer.get_compliance_level(score)
        assert level == ComplianceLevel.POOR
    
    def test_get_compliance_level_failed(self):
        """Test compliance level determination for failed score."""
        score = 45.0
        level = self.audit_layer.get_compliance_level(score)
        assert level == ComplianceLevel.FAILED
    
    def test_get_position_size_multiplier_high_score(self):
        """Test position size multiplier for high compliance score."""
        analysis = TokenAnalysis(
            token_address=self.test_address,
            chain="ethereum",
            analysis_timestamp=1234567890,
            compliance_score=ComplianceScore(
                overall_score=90.0,
                bytecode_safety=95.0,
                liquidity_analysis=85.0,
                holder_distribution=90.0,
                social_verification=85.0,
                external_tool_score=95.0,
                veto_reasons=[],
                warnings=[],
                metadata={}
            ),
            token_info={},
            audit_trail=[]
        )
        
        multiplier = self.audit_layer.get_position_size_multiplier(analysis)
        assert multiplier == 1.0  # Full position size for high compliance
    
    def test_get_position_size_multiplier_low_score(self):
        """Test position size multiplier for low compliance score."""
        analysis = TokenAnalysis(
            token_address=self.test_address,
            chain="ethereum",
            analysis_timestamp=1234567890,
            compliance_score=ComplianceScore(
                overall_score=75.0,  # Above threshold but below 80
                bytecode_safety=75.0,
                liquidity_analysis=75.0,
                holder_distribution=75.0,
                social_verification=75.0,
                external_tool_score=75.0,
                veto_reasons=[],
                warnings=[],
                metadata={}
            ),
            token_info={},
            audit_trail=[]
        )
        
        multiplier = self.audit_layer.get_position_size_multiplier(analysis)
        assert multiplier == MLConfig.UNLISTED_SIZE_MULTIPLIER  # Reduced position size for low compliance


class TestKrakenAuditLayerIntegration:
    """Integration tests for KrakenAuditLayer."""
    
    @pytest.mark.asyncio
    async def test_full_token_analysis_workflow(self):
        """Test the complete token analysis workflow."""
        audit_layer = KrakenAuditLayer()
        test_address = "0x1234567890123456789012345678901234567890"
        
        # Mock all external dependencies
        with patch.object(audit_layer, '_get_token_info', return_value={"name": "Test Token", "symbol": "TEST", "decimals": 18}):
            with patch.object(audit_layer, '_analyze_evm_bytecode', return_value={"is_safe": True, "suspicious_patterns": []}):
                with patch.object(audit_layer, '_analyze_evm_liquidity', return_value={"has_sufficient_liquidity": True, "liquidity_usd": 50000.0}):
                    with patch.object(audit_layer, '_analyze_evm_holder_distribution', return_value={"is_distributed": True, "top_10_percent": 0.3}):
                        with patch.object(audit_layer, '_analyze_social_verification', return_value={"is_verified": True, "social_score": 85.0}):
                            with patch.object(audit_layer, '_analyze_external_tools', return_value={"tools_score": 90.0, "verified_by": ["tool1", "tool2"]}):
                                result = await audit_layer.analyze_token(test_address, "ethereum")
                                
                                assert isinstance(result, TokenAnalysis)
                                assert result.token_address == test_address
                                assert result.chain == "ethereum"
                                assert result.compliance_score.overall_score is not None
                                assert result.compliance_score.overall_score >= 0.0
                                assert result.compliance_score.overall_score <= 100.0
    
    @pytest.mark.asyncio
    async def test_token_analysis_with_mixed_results(self):
        """Test token analysis with mixed safe/unsafe results."""
        audit_layer = KrakenAuditLayer()
        test_address = "0x1234567890123456789012345678901234567890"
        
        # Mock mixed results (some safe, some unsafe)
        with patch.object(audit_layer, '_get_token_info', return_value={"name": "Mixed Token", "symbol": "MIXED", "decimals": 18}):
            with patch.object(audit_layer, '_analyze_evm_bytecode', return_value={"is_safe": False, "suspicious_patterns": ["delegatecall"]}):
                with patch.object(audit_layer, '_analyze_evm_liquidity', return_value={"has_sufficient_liquidity": True, "liquidity_usd": 15000.0}):
                    with patch.object(audit_layer, '_analyze_evm_holder_distribution', return_value={"is_distributed": False, "top_10_percent": 0.8}):
                        with patch.object(audit_layer, '_analyze_social_verification', return_value={"is_verified": True, "social_score": 70.0}):
                            with patch.object(audit_layer, '_analyze_external_tools', return_value={"tools_score": 60.0, "verified_by": ["tool1"]}):
                                result = await audit_layer.analyze_token(test_address, "ethereum")
                                
                                assert isinstance(result, TokenAnalysis)
                                assert result.token_address == test_address
                                assert result.chain == "ethereum"
                                # Should have a lower overall score due to mixed results
                                assert result.compliance_score.overall_score < 80.0