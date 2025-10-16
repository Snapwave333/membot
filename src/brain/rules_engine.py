"""
Rules engine for the meme-coin trading bot.

This module provides a rules-based decision engine that evaluates
trading conditions and makes decisions based on predefined rules.
"""

import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import structlog

from src.config import TRADING_CONFIG, SAFETY_CONFIG
from src.utils.logger import log_trading_event, log_performance_metric

logger = structlog.get_logger(__name__)


class RuleType(Enum):
    """Rule type enumeration."""
    ENTRY = "entry"
    EXIT = "exit"
    RISK = "risk"
    POSITION_SIZE = "position_size"
    TIMING = "timing"


class RuleResult(Enum):
    """Rule result enumeration."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    ERROR = "error"


@dataclass
class Rule:
    """Rule data structure."""
    name: str
    rule_type: RuleType
    condition: str
    action: str
    priority: int
    enabled: bool = True
    created_at: float = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


@dataclass
class RuleEvaluation:
    """Rule evaluation result."""
    rule: Rule
    result: RuleResult
    score: float
    message: str
    timestamp: float
    execution_time: float


class RulesEngine:
    """
    Rules-based decision engine for trading decisions.
    
    Features:
    - Rule evaluation and scoring
    - Decision aggregation
    - Performance monitoring
    - Rule management
    """
    
    def __init__(self):
        """Initialize the rules engine."""
        self.rules: Dict[str, Rule] = {}
        self.evaluation_history: List[RuleEvaluation] = []
        self.last_evaluation: float = 0.0
        
        # Initialize default rules
        self._initialize_default_rules()
        
        logger.info("Rules engine initialized", rule_count=len(self.rules))
    
    def _initialize_default_rules(self):
        """Initialize default trading rules."""
        default_rules = [
            # Entry rules
            Rule(
                name="volume_threshold",
                rule_type=RuleType.ENTRY,
                condition="volume_24h > min_volume_threshold",
                action="allow_entry",
                priority=1
            ),
            Rule(
                name="liquidity_check",
                rule_type=RuleType.ENTRY,
                condition="liquidity > min_liquidity_threshold",
                action="allow_entry",
                priority=2
            ),
            Rule(
                name="price_momentum",
                rule_type=RuleType.ENTRY,
                condition="price_change_1h > 0.05",
                action="allow_entry",
                priority=3
            ),
            
            # Exit rules
            Rule(
                name="profit_target",
                rule_type=RuleType.EXIT,
                condition="unrealized_pnl_pct >= profit_target_pct",
                action="close_position",
                priority=1
            ),
            Rule(
                name="stop_loss",
                rule_type=RuleType.EXIT,
                condition="unrealized_pnl_pct <= -hard_stop_pct",
                action="close_position",
                priority=1
            ),
            Rule(
                name="time_based_exit",
                rule_type=RuleType.EXIT,
                condition="position_age_hours > max_hold_time",
                action="close_position",
                priority=2
            ),
            
            # Risk rules
            Rule(
                name="daily_loss_limit",
                rule_type=RuleType.RISK,
                condition="daily_pnl < -daily_max_loss_pct",
                action="stop_trading",
                priority=1
            ),
            Rule(
                name="max_positions",
                rule_type=RuleType.RISK,
                condition="position_count >= max_concurrent_positions",
                action="prevent_new_positions",
                priority=1
            ),
            Rule(
                name="drawdown_limit",
                rule_type=RuleType.RISK,
                condition="max_drawdown > max_drawdown_pct",
                action="stop_trading",
                priority=1
            ),
            
            # Position sizing rules
            Rule(
                name="min_position_size",
                rule_type=RuleType.POSITION_SIZE,
                condition="position_value >= min_position_size_usd",
                action="allow_position",
                priority=1
            ),
            Rule(
                name="max_position_size",
                rule_type=RuleType.POSITION_SIZE,
                condition="position_value <= max_position_size_usd",
                action="allow_position",
                priority=1
            ),
            Rule(
                name="portfolio_percentage",
                rule_type=RuleType.POSITION_SIZE,
                condition="position_pct <= per_trade_pct",
                action="allow_position",
                priority=2
            ),
            
            # Timing rules
            Rule(
                name="min_trade_interval",
                rule_type=RuleType.TIMING,
                condition="time_since_last_trade >= min_trade_interval",
                action="allow_trade",
                priority=1
            ),
            Rule(
                name="market_hours",
                rule_type=RuleType.TIMING,
                condition="market_open == true",
                action="allow_trade",
                priority=2
            ),
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: Rule) -> bool:
        """
        Add a new rule to the engine.
        
        Args:
            rule: Rule to add
            
        Returns:
            True if rule added successfully, False otherwise
        """
        try:
            self.rules[rule.name] = rule
            logger.info("Rule added", rule_name=rule.name, rule_type=rule.rule_type.value)
            return True
            
        except Exception as e:
            logger.error("Failed to add rule", rule_name=rule.name, error=str(e))
            return False
    
    def remove_rule(self, rule_name: str) -> bool:
        """
        Remove a rule from the engine.
        
        Args:
            rule_name: Name of rule to remove
            
        Returns:
            True if rule removed successfully, False otherwise
        """
        try:
            if rule_name in self.rules:
                del self.rules[rule_name]
                logger.info("Rule removed", rule_name=rule_name)
                return True
            else:
                logger.warning("Rule not found", rule_name=rule_name)
                return False
                
        except Exception as e:
            logger.error("Failed to remove rule", rule_name=rule_name, error=str(e))
            return False
    
    def enable_rule(self, rule_name: str) -> bool:
        """
        Enable a rule.
        
        Args:
            rule_name: Name of rule to enable
            
        Returns:
            True if rule enabled successfully, False otherwise
        """
        try:
            if rule_name in self.rules:
                self.rules[rule_name].enabled = True
                logger.info("Rule enabled", rule_name=rule_name)
                return True
            else:
                logger.warning("Rule not found", rule_name=rule_name)
                return False
                
        except Exception as e:
            logger.error("Failed to enable rule", rule_name=rule_name, error=str(e))
            return False
    
    def disable_rule(self, rule_name: str) -> bool:
        """
        Disable a rule.
        
        Args:
            rule_name: Name of rule to disable
            
        Returns:
            True if rule disabled successfully, False otherwise
        """
        try:
            if rule_name in self.rules:
                self.rules[rule_name].enabled = False
                logger.info("Rule disabled", rule_name=rule_name)
                return True
            else:
                logger.warning("Rule not found", rule_name=rule_name)
                return False
                
        except Exception as e:
            logger.error("Failed to disable rule", rule_name=rule_name, error=str(e))
            return False
    
    def evaluate_rule(self, rule: Rule, context: Dict[str, Any]) -> RuleEvaluation:
        """
        Evaluate a single rule against the given context.
        
        Args:
            rule: Rule to evaluate
            context: Context data for evaluation
            
        Returns:
            Rule evaluation result
        """
        start_time = time.time()
        
        try:
            # Skip disabled rules
            if not rule.enabled:
                return RuleEvaluation(
                    rule=rule,
                    result=RuleResult.PASS,
                    score=0.0,
                    message="Rule disabled",
                    timestamp=time.time(),
                    execution_time=time.time() - start_time
                )
            
            # Evaluate rule condition
            result, score, message = self._evaluate_condition(rule.condition, context)
            
            execution_time = time.time() - start_time
            
            evaluation = RuleEvaluation(
                rule=rule,
                result=result,
                score=score,
                message=message,
                timestamp=time.time(),
                execution_time=execution_time
            )
            
            # Log performance metric
            log_performance_metric("rule_evaluation_time", execution_time, "seconds")
            
            return evaluation
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error("Failed to evaluate rule", rule_name=rule.name, error=str(e))
            
            return RuleEvaluation(
                rule=rule,
                result=RuleResult.ERROR,
                score=0.0,
                message=f"Evaluation error: {e}",
                timestamp=time.time(),
                execution_time=execution_time
            )
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> Tuple[RuleResult, float, str]:
        """
        Evaluate a rule condition.
        
        Args:
            condition: Condition string to evaluate
            context: Context data
            
        Returns:
            Tuple of (result, score, message)
        """
        try:
            # Simple condition evaluation (in production, use a proper expression evaluator)
            if "volume_24h > min_volume_threshold" in condition:
                volume_24h = context.get("volume_24h", 0)
                min_volume_threshold = context.get("min_volume_threshold", TRADING_CONFIG.MIN_VOLUME_24H_USD)
                
                if volume_24h > min_volume_threshold:
                    return RuleResult.PASS, 1.0, f"Volume sufficient: {volume_24h} > {min_volume_threshold}"
                else:
                    return RuleResult.FAIL, 0.0, f"Volume insufficient: {volume_24h} <= {min_volume_threshold}"
            
            elif "liquidity > min_liquidity_threshold" in condition:
                liquidity = context.get("liquidity", 0)
                min_liquidity_threshold = context.get("min_liquidity_threshold", TRADING_CONFIG.MIN_LIQUIDITY_USD)
                
                if liquidity > min_liquidity_threshold:
                    return RuleResult.PASS, 1.0, f"Liquidity sufficient: {liquidity} > {min_liquidity_threshold}"
                else:
                    return RuleResult.FAIL, 0.0, f"Liquidity insufficient: {liquidity} <= {min_liquidity_threshold}"
            
            elif "price_change_1h > 0.05" in condition:
                price_change_1h = context.get("price_change_1h", 0)
                
                if price_change_1h > 0.05:
                    return RuleResult.PASS, 1.0, f"Positive momentum: {price_change_1h:.2%}"
                else:
                    return RuleResult.FAIL, 0.0, f"No momentum: {price_change_1h:.2%}"
            
            elif "unrealized_pnl_pct >= profit_target_pct" in condition:
                unrealized_pnl_pct = context.get("unrealized_pnl_pct", 0)
                profit_target_pct = context.get("profit_target_pct", TRADING_CONFIG.PROFIT_TARGET_PCT)
                
                if unrealized_pnl_pct >= profit_target_pct:
                    return RuleResult.PASS, 1.0, f"Profit target reached: {unrealized_pnl_pct:.2f}% >= {profit_target_pct}%"
                else:
                    return RuleResult.FAIL, 0.0, f"Profit target not reached: {unrealized_pnl_pct:.2f}% < {profit_target_pct}%"
            
            elif "unrealized_pnl_pct <= -hard_stop_pct" in condition:
                unrealized_pnl_pct = context.get("unrealized_pnl_pct", 0)
                hard_stop_pct = context.get("hard_stop_pct", TRADING_CONFIG.HARD_STOP_PCT)
                
                if unrealized_pnl_pct <= -hard_stop_pct:
                    return RuleResult.PASS, 1.0, f"Stop loss triggered: {unrealized_pnl_pct:.2f}% <= -{hard_stop_pct}%"
                else:
                    return RuleResult.FAIL, 0.0, f"Stop loss not triggered: {unrealized_pnl_pct:.2f}% > -{hard_stop_pct}%"
            
            elif "position_age_hours > max_hold_time" in condition:
                position_age_hours = context.get("position_age_hours", 0)
                max_hold_time = context.get("max_hold_time", TRADING_CONFIG.MAX_TRADE_DURATION_HOURS)
                
                if position_age_hours > max_hold_time:
                    return RuleResult.PASS, 1.0, f"Position too old: {position_age_hours}h > {max_hold_time}h"
                else:
                    return RuleResult.FAIL, 0.0, f"Position age OK: {position_age_hours}h <= {max_hold_time}h"
            
            elif "daily_pnl < -daily_max_loss_pct" in condition:
                daily_pnl = context.get("daily_pnl", 0)
                daily_max_loss_pct = context.get("daily_max_loss_pct", TRADING_CONFIG.DAILY_MAX_LOSS_PERCENT)
                portfolio_value = context.get("portfolio_value", 10000)
                daily_max_loss = portfolio_value * (daily_max_loss_pct / 100.0)
                
                if daily_pnl < -daily_max_loss:
                    return RuleResult.PASS, 1.0, f"Daily loss limit exceeded: ${daily_pnl:.2f} < -${daily_max_loss:.2f}"
                else:
                    return RuleResult.FAIL, 0.0, f"Daily loss limit OK: ${daily_pnl:.2f} >= -${daily_max_loss:.2f}"
            
            elif "position_count >= max_concurrent_positions" in condition:
                position_count = context.get("position_count", 0)
                max_concurrent_positions = context.get("max_concurrent_positions", TRADING_CONFIG.MAX_CONCURRENT_POSITIONS)
                
                if position_count >= max_concurrent_positions:
                    return RuleResult.PASS, 1.0, f"Max positions reached: {position_count} >= {max_concurrent_positions}"
                else:
                    return RuleResult.FAIL, 0.0, f"Position count OK: {position_count} < {max_concurrent_positions}"
            
            elif "max_drawdown > max_drawdown_pct" in condition:
                max_drawdown = context.get("max_drawdown", 0)
                max_drawdown_pct = context.get("max_drawdown_pct", SAFETY_CONFIG.MAX_DRAWDOWN_PCT)
                
                if max_drawdown > max_drawdown_pct:
                    return RuleResult.PASS, 1.0, f"Max drawdown exceeded: {max_drawdown:.2f}% > {max_drawdown_pct}%"
                else:
                    return RuleResult.FAIL, 0.0, f"Drawdown OK: {max_drawdown:.2f}% <= {max_drawdown_pct}%"
            
            elif "position_value >= min_position_size_usd" in condition:
                position_value = context.get("position_value", 0)
                min_position_size_usd = context.get("min_position_size_usd", TRADING_CONFIG.MIN_POSITION_SIZE_USD)
                
                if position_value >= min_position_size_usd:
                    return RuleResult.PASS, 1.0, f"Position size sufficient: ${position_value:.2f} >= ${min_position_size_usd}"
                else:
                    return RuleResult.FAIL, 0.0, f"Position size too small: ${position_value:.2f} < ${min_position_size_usd}"
            
            elif "position_value <= max_position_size_usd" in condition:
                position_value = context.get("position_value", 0)
                max_position_size_usd = context.get("max_position_size_usd", TRADING_CONFIG.MAX_POSITION_SIZE_USD)
                
                if position_value <= max_position_size_usd:
                    return RuleResult.PASS, 1.0, f"Position size OK: ${position_value:.2f} <= ${max_position_size_usd}"
                else:
                    return RuleResult.FAIL, 0.0, f"Position size too large: ${position_value:.2f} > ${max_position_size_usd}"
            
            elif "position_pct <= per_trade_pct" in condition:
                position_pct = context.get("position_pct", 0)
                per_trade_pct = context.get("per_trade_pct", TRADING_CONFIG.PER_TRADE_PCT)
                
                if position_pct <= per_trade_pct:
                    return RuleResult.PASS, 1.0, f"Position percentage OK: {position_pct:.2f}% <= {per_trade_pct}%"
                else:
                    return RuleResult.FAIL, 0.0, f"Position percentage too high: {position_pct:.2f}% > {per_trade_pct}%"
            
            elif "time_since_last_trade >= min_trade_interval" in condition:
                time_since_last_trade = context.get("time_since_last_trade", 0)
                min_trade_interval = context.get("min_trade_interval", TRADING_CONFIG.MIN_TRADE_INTERVAL_SECONDS)
                
                if time_since_last_trade >= min_trade_interval:
                    return RuleResult.PASS, 1.0, f"Trade interval OK: {time_since_last_trade}s >= {min_trade_interval}s"
                else:
                    return RuleResult.FAIL, 0.0, f"Trade interval too short: {time_since_last_trade}s < {min_trade_interval}s"
            
            elif "market_open == true" in condition:
                market_open = context.get("market_open", True)
                
                if market_open:
                    return RuleResult.PASS, 1.0, "Market is open"
                else:
                    return RuleResult.FAIL, 0.0, "Market is closed"
            
            else:
                # Unknown condition
                return RuleResult.ERROR, 0.0, f"Unknown condition: {condition}"
                
        except Exception as e:
            return RuleResult.ERROR, 0.0, f"Condition evaluation error: {e}"
    
    def evaluate_rules(self, rule_type: RuleType, context: Dict[str, Any]) -> List[RuleEvaluation]:
        """
        Evaluate all rules of a specific type.
        
        Args:
            rule_type: Type of rules to evaluate
            context: Context data for evaluation
            
        Returns:
            List of rule evaluation results
        """
        try:
            evaluations = []
            
            # Get rules of the specified type
            relevant_rules = [rule for rule in self.rules.values() if rule.rule_type == rule_type]
            
            # Sort by priority
            relevant_rules.sort(key=lambda x: x.priority)
            
            # Evaluate each rule
            for rule in relevant_rules:
                evaluation = self.evaluate_rule(rule, context)
                evaluations.append(evaluation)
                
                # Store in history
                self.evaluation_history.append(evaluation)
            
            # Keep only recent history
            if len(self.evaluation_history) > 1000:
                self.evaluation_history = self.evaluation_history[-1000:]
            
            self.last_evaluation = time.time()
            
            log_trading_event(
                "rules_evaluated",
                {
                    "rule_type": rule_type.value,
                    "rule_count": len(relevant_rules),
                    "passed_count": sum(1 for e in evaluations if e.result == RuleResult.PASS),
                    "failed_count": sum(1 for e in evaluations if e.result == RuleResult.FAIL),
                    "error_count": sum(1 for e in evaluations if e.result == RuleResult.ERROR)
                },
                "INFO"
            )
            
            return evaluations
            
        except Exception as e:
            logger.error("Failed to evaluate rules", rule_type=rule_type.value, error=str(e))
            return []
    
    def get_decision(self, rule_type: RuleType, context: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Get a decision based on rule evaluations.
        
        Args:
            rule_type: Type of rules to evaluate
            context: Context data for evaluation
            
        Returns:
            Tuple of (decision, reason, confidence)
        """
        try:
            evaluations = self.evaluate_rules(rule_type, context)
            
            if not evaluations:
                return False, "No rules to evaluate", 0.0
            
            # Calculate decision based on rule results
            passed_rules = [e for e in evaluations if e.result == RuleResult.PASS]
            failed_rules = [e for e in evaluations if e.result == RuleResult.FAIL]
            error_rules = [e for e in evaluations if e.result == RuleResult.ERROR]
            
            # If any rule fails, decision is negative
            if failed_rules:
                reason = f"Failed rules: {', '.join([r.rule.name for r in failed_rules])}"
                confidence = 0.0
                return False, reason, confidence
            
            # If any rule has an error, decision is negative
            if error_rules:
                reason = f"Error in rules: {', '.join([r.rule.name for r in error_rules])}"
                confidence = 0.0
                return False, reason, confidence
            
            # All rules passed
            reason = f"All rules passed: {', '.join([r.rule.name for r in passed_rules])}"
            confidence = sum(e.score for e in passed_rules) / len(passed_rules)
            
            return True, reason, confidence
            
        except Exception as e:
            logger.error("Failed to get decision", rule_type=rule_type.value, error=str(e))
            return False, f"Decision error: {e}", 0.0
    
    def get_rule_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about rule evaluations.
        
        Returns:
            Dictionary with rule statistics
        """
        try:
            if not self.evaluation_history:
                return {"total_evaluations": 0}
            
            # Calculate statistics
            total_evaluations = len(self.evaluation_history)
            passed_evaluations = sum(1 for e in self.evaluation_history if e.result == RuleResult.PASS)
            failed_evaluations = sum(1 for e in self.evaluation_history if e.result == RuleResult.FAIL)
            error_evaluations = sum(1 for e in self.evaluation_history if e.result == RuleResult.ERROR)
            
            avg_execution_time = sum(e.execution_time for e in self.evaluation_history) / total_evaluations
            
            # Rule-specific statistics
            rule_stats = {}
            for rule_name in self.rules.keys():
                rule_evaluations = [e for e in self.evaluation_history if e.rule.name == rule_name]
                if rule_evaluations:
                    rule_stats[rule_name] = {
                        "total_evaluations": len(rule_evaluations),
                        "passed": sum(1 for e in rule_evaluations if e.result == RuleResult.PASS),
                        "failed": sum(1 for e in rule_evaluations if e.result == RuleResult.FAIL),
                        "errors": sum(1 for e in rule_evaluations if e.result == RuleResult.ERROR),
                        "avg_score": sum(e.score for e in rule_evaluations) / len(rule_evaluations),
                        "avg_execution_time": sum(e.execution_time for e in rule_evaluations) / len(rule_evaluations)
                    }
            
            return {
                "total_evaluations": total_evaluations,
                "passed_evaluations": passed_evaluations,
                "failed_evaluations": failed_evaluations,
                "error_evaluations": error_evaluations,
                "pass_rate": passed_evaluations / total_evaluations if total_evaluations > 0 else 0.0,
                "avg_execution_time": avg_execution_time,
                "rule_statistics": rule_stats,
                "last_evaluation": self.last_evaluation
            }
            
        except Exception as e:
            logger.error("Failed to get rule statistics", error=str(e))
            return {"error": str(e)}


# Global rules engine instance
_rules_engine: Optional[RulesEngine] = None


def get_rules_engine() -> RulesEngine:
    """
    Get the global rules engine instance.
    
    Returns:
        Rules engine instance
    """
    global _rules_engine
    
    if _rules_engine is None:
        _rules_engine = RulesEngine()
    
    return _rules_engine
