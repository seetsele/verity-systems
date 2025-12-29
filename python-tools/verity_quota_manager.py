"""
Verity Usage Quota System
Tracks API usage per user and enforces tier-based limits.
"""

import os
import json
import time
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger("VerityQuota")

class PlanTier(Enum):
    """Subscription tiers"""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


@dataclass
class PlanLimits:
    """Limits for each plan tier"""
    verifications_per_month: int
    verifications_per_day: int
    data_sources: int
    api_access: bool
    nlp_analysis: bool
    source_credibility: bool
    monte_carlo: bool
    temporal_geo: bool
    similar_claims: bool
    deep_research: bool  # Deep Research Mode with 4-8 LLMs, 20+ sources
    llm_models: int  # Number of LLM models for consensus
    team_members: int
    priority_support: bool
    
    @classmethod
    def get_limits(cls, tier: PlanTier) -> 'PlanLimits':
        """Get limits for a specific tier"""
        limits = {
            PlanTier.FREE: cls(
                verifications_per_month=300,
                verifications_per_day=10,
                data_sources=5,
                api_access=False,
                nlp_analysis=False,
                source_credibility=False,
                monte_carlo=False,
                temporal_geo=False,
                similar_claims=False,
                deep_research=False,  # Limited to 2 LLMs, 5 sources
                llm_models=2,
                team_members=1,
                priority_support=False
            ),
            PlanTier.PRO: cls(
                verifications_per_month=500,
                verifications_per_day=50,
                data_sources=27,
                api_access=True,
                nlp_analysis=True,
                source_credibility=True,
                monte_carlo=False,
                temporal_geo=False,
                similar_claims=True,
                deep_research=True,  # Full Deep Research: 4-8 LLMs, 20+ sources
                llm_models=8,
                team_members=1,
                priority_support=False
            ),
            PlanTier.TEAM: cls(
                verifications_per_month=2500,
                verifications_per_day=200,
                data_sources=27,
                api_access=True,
                nlp_analysis=True,
                source_credibility=True,
                monte_carlo=True,
                temporal_geo=True,
                similar_claims=True,
                deep_research=True,  # Full Deep Research: 4-8 LLMs, 20+ sources
                llm_models=8,
                team_members=5,
                priority_support=True
            ),
            PlanTier.ENTERPRISE: cls(
                verifications_per_month=999999,  # Unlimited
                verifications_per_day=999999,
                data_sources=27,
                api_access=True,
                nlp_analysis=True,
                source_credibility=True,
                monte_carlo=True,
                temporal_geo=True,
                similar_claims=True,
                deep_research=True,  # Full Deep Research: 4-8 LLMs, 20+ sources
                llm_models=15,  # Access to ALL LLM models
                team_members=999999,
                priority_support=True
            )
        }
        return limits.get(tier, limits[PlanTier.FREE])


@dataclass
class UserUsage:
    """Track user usage"""
    user_id: str
    tier: str
    verifications_today: int = 0
    verifications_this_month: int = 0
    last_verification: Optional[str] = None
    day_reset: Optional[str] = None
    month_reset: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserUsage':
        return cls(**data)


class QuotaManager:
    """
    Manages user quotas and usage tracking.
    Uses file-based storage for simplicity, can be swapped for Redis/DB.
    """
    
    def __init__(self, storage_path: str = ".verity_quotas"):
        self.storage_path = storage_path
        self._ensure_storage()
        
    def _ensure_storage(self):
        """Ensure storage directory exists"""
        os.makedirs(self.storage_path, exist_ok=True)
        
    def _get_user_file(self, user_id: str) -> str:
        """Get path to user's quota file"""
        safe_id = hashlib.md5(user_id.encode()).hexdigest()
        return os.path.join(self.storage_path, f"{safe_id}.json")
    
    def _load_user(self, user_id: str, tier: str = "free") -> UserUsage:
        """Load or create user usage record"""
        filepath = self._get_user_file(user_id)
        
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data = json.load(f)
                usage = UserUsage.from_dict(data)
                # Update tier if changed
                usage.tier = tier
                return usage
        
        # Create new user
        now = datetime.utcnow()
        return UserUsage(
            user_id=user_id,
            tier=tier,
            verifications_today=0,
            verifications_this_month=0,
            day_reset=(now + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat(),
            month_reset=(now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0).isoformat(),
            created_at=now.isoformat()
        )
    
    def _save_user(self, usage: UserUsage):
        """Save user usage record"""
        filepath = self._get_user_file(usage.user_id)
        with open(filepath, 'w') as f:
            json.dump(usage.to_dict(), f, indent=2)
    
    def _check_resets(self, usage: UserUsage) -> UserUsage:
        """Check and apply quota resets"""
        now = datetime.utcnow()
        
        # Daily reset
        if usage.day_reset:
            day_reset = datetime.fromisoformat(usage.day_reset)
            if now >= day_reset:
                usage.verifications_today = 0
                usage.day_reset = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()
                logger.info(f"Daily quota reset for user {usage.user_id[:8]}...")
        
        # Monthly reset
        if usage.month_reset:
            month_reset = datetime.fromisoformat(usage.month_reset)
            if now >= month_reset:
                usage.verifications_this_month = 0
                usage.month_reset = (now.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0).isoformat()
                logger.info(f"Monthly quota reset for user {usage.user_id[:8]}...")
        
        return usage
    
    def check_quota(self, user_id: str, tier: str = "free") -> Tuple[bool, Dict[str, Any]]:
        """
        Check if user has remaining quota.
        
        Returns:
            Tuple of (allowed: bool, details: dict)
        """
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        usage = self._load_user(user_id, tier)
        usage = self._check_resets(usage)
        
        # Check daily limit
        daily_remaining = limits.verifications_per_day - usage.verifications_today
        if daily_remaining <= 0:
            return False, {
                "allowed": False,
                "reason": "daily_limit_exceeded",
                "message": f"Daily limit of {limits.verifications_per_day} verifications reached. Resets at midnight UTC.",
                "daily_used": usage.verifications_today,
                "daily_limit": limits.verifications_per_day,
                "monthly_used": usage.verifications_this_month,
                "monthly_limit": limits.verifications_per_month,
                "reset_at": usage.day_reset,
                "tier": tier
            }
        
        # Check monthly limit
        monthly_remaining = limits.verifications_per_month - usage.verifications_this_month
        if monthly_remaining <= 0:
            return False, {
                "allowed": False,
                "reason": "monthly_limit_exceeded",
                "message": f"Monthly limit of {limits.verifications_per_month} verifications reached. Resets on the 1st.",
                "daily_used": usage.verifications_today,
                "daily_limit": limits.verifications_per_day,
                "monthly_used": usage.verifications_this_month,
                "monthly_limit": limits.verifications_per_month,
                "reset_at": usage.month_reset,
                "tier": tier,
                "upgrade_url": "/pricing.html"
            }
        
        return True, {
            "allowed": True,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining,
            "daily_used": usage.verifications_today,
            "daily_limit": limits.verifications_per_day,
            "monthly_used": usage.verifications_this_month,
            "monthly_limit": limits.verifications_per_month,
            "tier": tier
        }
    
    def record_usage(self, user_id: str, tier: str = "free") -> Dict[str, Any]:
        """
        Record a verification and return updated usage.
        Should be called after successful verification.
        """
        usage = self._load_user(user_id, tier)
        usage = self._check_resets(usage)
        
        usage.verifications_today += 1
        usage.verifications_this_month += 1
        usage.last_verification = datetime.utcnow().isoformat()
        
        self._save_user(usage)
        
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        
        return {
            "recorded": True,
            "daily_used": usage.verifications_today,
            "daily_limit": limits.verifications_per_day,
            "daily_remaining": limits.verifications_per_day - usage.verifications_today,
            "monthly_used": usage.verifications_this_month,
            "monthly_limit": limits.verifications_per_month,
            "monthly_remaining": limits.verifications_per_month - usage.verifications_this_month
        }
    
    def get_usage(self, user_id: str, tier: str = "free") -> Dict[str, Any]:
        """Get current usage stats for a user"""
        usage = self._load_user(user_id, tier)
        usage = self._check_resets(usage)
        
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        
        return {
            "user_id": user_id[:8] + "...",
            "tier": tier,
            "usage": {
                "today": {
                    "used": usage.verifications_today,
                    "limit": limits.verifications_per_day,
                    "remaining": max(0, limits.verifications_per_day - usage.verifications_today),
                    "reset_at": usage.day_reset
                },
                "month": {
                    "used": usage.verifications_this_month,
                    "limit": limits.verifications_per_month,
                    "remaining": max(0, limits.verifications_per_month - usage.verifications_this_month),
                    "reset_at": usage.month_reset
                }
            },
            "features": {
                "api_access": limits.api_access,
                "data_sources": limits.data_sources,
                "nlp_analysis": limits.nlp_analysis,
                "source_credibility": limits.source_credibility,
                "monte_carlo": limits.monte_carlo,
                "temporal_geo": limits.temporal_geo,
                "similar_claims": limits.similar_claims,
                "team_members": limits.team_members
            },
            "last_verification": usage.last_verification,
            "member_since": usage.created_at
        }
    
    def check_feature_access(self, user_id: str, tier: str, feature: str) -> Tuple[bool, str]:
        """
        Check if user has access to a specific feature.
        
        Features:
        - api_access
        - nlp_analysis
        - source_credibility
        - monte_carlo
        - temporal_geo
        - similar_claims
        """
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        
        feature_map = {
            "api_access": limits.api_access,
            "nlp_analysis": limits.nlp_analysis,
            "source_credibility": limits.source_credibility,
            "monte_carlo": limits.monte_carlo,
            "temporal_geo": limits.temporal_geo,
            "similar_claims": limits.similar_claims,
        }
        
        has_access = feature_map.get(feature, False)
        
        if not has_access:
            # Find minimum tier that has this feature
            upgrade_to = None
            for check_tier in [PlanTier.PRO, PlanTier.TEAM, PlanTier.ENTERPRISE]:
                check_limits = PlanLimits.get_limits(check_tier)
                if getattr(check_limits, feature, False):
                    upgrade_to = check_tier.value
                    break
            
            return False, f"Feature '{feature}' requires {upgrade_to or 'higher'} plan. Upgrade at /pricing.html"
        
        return True, "Access granted"


# Global instance
_quota_manager: Optional[QuotaManager] = None

def get_quota_manager() -> QuotaManager:
    """Get or create the global quota manager"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager


# FastAPI dependency for quota checking
async def check_user_quota(user_id: str, tier: str = "free"):
    """
    FastAPI dependency to check quota before processing request.
    Raises HTTPException if quota exceeded.
    """
    from fastapi import HTTPException
    
    manager = get_quota_manager()
    allowed, details = manager.check_quota(user_id, tier)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=details
        )
    
    return details


# Test
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    manager = QuotaManager()
    
    # Test free user
    print("\n=== Testing Free User ===")
    user_id = "test_user_free_123"
    
    for i in range(12):
        allowed, details = manager.check_quota(user_id, "free")
        if allowed:
            result = manager.record_usage(user_id, "free")
            print(f"Verification {i+1}: ✓ ({result['daily_remaining']} remaining today)")
        else:
            print(f"Verification {i+1}: ✗ {details['message']}")
            break
    
    # Test pro user
    print("\n=== Testing Pro User ===")
    user_id = "test_user_pro_456"
    
    usage = manager.get_usage(user_id, "pro")
    print(f"Pro user features: {json.dumps(usage['features'], indent=2)}")
    
    # Test feature access
    print("\n=== Testing Feature Access ===")
    for feature in ["nlp_analysis", "monte_carlo", "api_access"]:
        has_access, msg = manager.check_feature_access("user", "free", feature)
        print(f"Free - {feature}: {'✓' if has_access else '✗'} {msg if not has_access else ''}")
        
        has_access, msg = manager.check_feature_access("user", "pro", feature)
        print(f"Pro  - {feature}: {'✓' if has_access else '✗'} {msg if not has_access else ''}")
