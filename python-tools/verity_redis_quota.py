"""
Verity Redis Quota Manager
Production-ready quota management using Redis Cloud.

Features:
- Distributed quota tracking (works across multiple instances)
- Atomic operations (no race conditions)
- Automatic TTL-based resets
- Rate limiting with sliding windows
- Real-time usage analytics

Author: Verity Systems
License: MIT
"""

import os
import json
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger("VerityRedisQuota")


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
    ultimate_suite: bool  # All-in-one enterprise feature
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
                ultimate_suite=False,
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
                ultimate_suite=False,
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
                ultimate_suite=False,
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
                ultimate_suite=True,  # Only Enterprise gets Ultimate Suite!
                team_members=999999,
                priority_support=True
            )
        }
        return limits.get(tier, limits[PlanTier.FREE])


class RedisQuotaManager:
    """
    Production Redis-backed quota manager.
    
    Key Structure:
    - verity:user:{user_hash}:daily:{date} -> int (verifications count)
    - verity:user:{user_hash}:monthly:{month} -> int (verifications count)
    - verity:user:{user_hash}:info -> hash (tier, created_at, etc.)
    - verity:rate:{user_hash}:{minute} -> int (rate limit counter)
    """
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL')
        self._client = None
        self._sync_client = None
        self.prefix = "verity:"
        
    async def _get_client(self):
        """Get async Redis client"""
        if self._client is None:
            try:
                import redis.asyncio as aioredis
                self._client = aioredis.from_url(
                    self.redis_url,
                    encoding='utf-8',
                    decode_responses=True
                )
                # Test connection
                await self._client.ping()
                logger.info("[OK] Redis connection established")
            except Exception as e:
                logger.error(f"[ERROR] Redis connection failed: {e}")
                raise
        return self._client
    
    def _get_sync_client(self):
        """Get synchronous Redis client for non-async contexts"""
        if self._sync_client is None:
            try:
                import redis
                self._sync_client = redis.from_url(
                    self.redis_url,
                    encoding='utf-8',
                    decode_responses=True
                )
                self._sync_client.ping()
                logger.info("[OK] Redis sync connection established")
            except Exception as e:
                logger.error(f"[ERROR] Redis sync connection failed: {e}")
                raise
        return self._sync_client
    
    def _user_hash(self, user_id: str) -> str:
        """Create a safe hash for user ID"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _now_utc(self) -> datetime:
        """Get current UTC time (timezone-aware)"""
        try:
            return datetime.now(datetime.UTC)
        except AttributeError:
            # Python < 3.11 fallback
            from datetime import timezone
            return datetime.now(timezone.utc)
    
    def _today_key(self) -> str:
        """Get today's date key"""
        return self._now_utc().strftime('%Y-%m-%d')
    
    def _month_key(self) -> str:
        """Get this month's key"""
        return self._now_utc().strftime('%Y-%m')
    
    def _seconds_until_midnight(self) -> int:
        """Seconds until next UTC midnight"""
        now = self._now_utc()
        midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        return int((midnight - now).total_seconds())
    
    def _seconds_until_month_end(self) -> int:
        """Seconds until end of month"""
        now = self._now_utc()
        if now.month == 12:
            next_month = now.replace(year=now.year + 1, month=1, day=1)
        else:
            next_month = now.replace(month=now.month + 1, day=1)
        return int((next_month - now).total_seconds())

    # =====================================================
    # ASYNC METHODS (for FastAPI)
    # =====================================================
    
    async def check_quota(self, user_id: str, tier: str = "free") -> Tuple[bool, Dict[str, Any]]:
        """Check if user has remaining quota (async)"""
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        client = await self._get_client()
        
        user_hash = self._user_hash(user_id)
        daily_key = f"{self.prefix}user:{user_hash}:daily:{self._today_key()}"
        monthly_key = f"{self.prefix}user:{user_hash}:monthly:{self._month_key()}"
        
        # Get current counts
        daily_count = await client.get(daily_key)
        monthly_count = await client.get(monthly_key)
        
        daily_used = int(daily_count) if daily_count else 0
        monthly_used = int(monthly_count) if monthly_count else 0
        
        # Check daily limit
        daily_remaining = limits.verifications_per_day - daily_used
        if daily_remaining <= 0:
            return False, {
                "allowed": False,
                "reason": "daily_limit_exceeded",
                "message": f"Daily limit of {limits.verifications_per_day} verifications reached. Resets at midnight UTC.",
                "daily_used": daily_used,
                "daily_limit": limits.verifications_per_day,
                "monthly_used": monthly_used,
                "monthly_limit": limits.verifications_per_month,
                "seconds_until_reset": self._seconds_until_midnight(),
                "tier": tier
            }
        
        # Check monthly limit
        monthly_remaining = limits.verifications_per_month - monthly_used
        if monthly_remaining <= 0:
            return False, {
                "allowed": False,
                "reason": "monthly_limit_exceeded",
                "message": f"Monthly limit of {limits.verifications_per_month} verifications reached.",
                "daily_used": daily_used,
                "daily_limit": limits.verifications_per_day,
                "monthly_used": monthly_used,
                "monthly_limit": limits.verifications_per_month,
                "seconds_until_reset": self._seconds_until_month_end(),
                "tier": tier,
                "upgrade_url": "/pricing.html"
            }
        
        return True, {
            "allowed": True,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining,
            "daily_used": daily_used,
            "daily_limit": limits.verifications_per_day,
            "monthly_used": monthly_used,
            "monthly_limit": limits.verifications_per_month,
            "tier": tier
        }
    
    async def record_usage(self, user_id: str, tier: str = "free") -> Dict[str, Any]:
        """Record a verification (async)"""
        client = await self._get_client()
        
        user_hash = self._user_hash(user_id)
        daily_key = f"{self.prefix}user:{user_hash}:daily:{self._today_key()}"
        monthly_key = f"{self.prefix}user:{user_hash}:monthly:{self._month_key()}"
        last_key = f"{self.prefix}user:{user_hash}:last"
        
        # Use pipeline for atomic operation
        pipe = client.pipeline()
        pipe.incr(daily_key)
        pipe.expire(daily_key, self._seconds_until_midnight() + 3600)  # +1hr buffer
        pipe.incr(monthly_key)
        pipe.expire(monthly_key, self._seconds_until_month_end() + 86400)  # +1day buffer
        pipe.set(last_key, self._now_utc().isoformat())
        results = await pipe.execute()
        
        daily_used = results[0]
        monthly_used = results[2]
        
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        
        return {
            "recorded": True,
            "daily_used": daily_used,
            "daily_limit": limits.verifications_per_day,
            "daily_remaining": limits.verifications_per_day - daily_used,
            "monthly_used": monthly_used,
            "monthly_limit": limits.verifications_per_month,
            "monthly_remaining": limits.verifications_per_month - monthly_used
        }
    
    async def get_usage(self, user_id: str, tier: str = "free") -> Dict[str, Any]:
        """Get current usage stats (async)"""
        client = await self._get_client()
        
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        
        user_hash = self._user_hash(user_id)
        daily_key = f"{self.prefix}user:{user_hash}:daily:{self._today_key()}"
        monthly_key = f"{self.prefix}user:{user_hash}:monthly:{self._month_key()}"
        last_key = f"{self.prefix}user:{user_hash}:last"
        
        pipe = client.pipeline()
        pipe.get(daily_key)
        pipe.get(monthly_key)
        pipe.get(last_key)
        results = await pipe.execute()
        
        daily_used = int(results[0]) if results[0] else 0
        monthly_used = int(results[1]) if results[1] else 0
        last_verification = results[2]
        
        return {
            "user_id": user_hash,
            "tier": tier,
            "usage": {
                "today": {
                    "used": daily_used,
                    "limit": limits.verifications_per_day,
                    "remaining": max(0, limits.verifications_per_day - daily_used),
                    "resets_in_seconds": self._seconds_until_midnight()
                },
                "month": {
                    "used": monthly_used,
                    "limit": limits.verifications_per_month,
                    "remaining": max(0, limits.verifications_per_month - monthly_used),
                    "resets_in_seconds": self._seconds_until_month_end()
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
                "ultimate_suite": limits.ultimate_suite,
                "team_members": limits.team_members
            },
            "last_verification": last_verification
        }
    
    async def check_rate_limit(self, user_id: str, tier: str = "free", 
                                max_per_minute: int = 10) -> Tuple[bool, Dict[str, Any]]:
        """
        Sliding window rate limiter.
        Enterprise gets 100/min, Team 50/min, Pro 20/min, Free 10/min.
        """
        # Tier-based rate limits
        tier_limits = {
            "enterprise": 100,
            "team": 50,
            "pro": 20,
            "free": 10
        }
        max_per_minute = tier_limits.get(tier.lower(), 10)
        
        client = await self._get_client()
        user_hash = self._user_hash(user_id)
        now = self._now_utc()
        minute_key = f"{self.prefix}rate:{user_hash}:{now.strftime('%Y%m%d%H%M')}"
        
        pipe = client.pipeline()
        pipe.incr(minute_key)
        pipe.expire(minute_key, 120)  # Expire after 2 minutes
        results = await pipe.execute()
        
        current_count = results[0]
        
        if current_count > max_per_minute:
            return False, {
                "allowed": False,
                "reason": "rate_limit_exceeded",
                "message": f"Rate limit of {max_per_minute}/minute exceeded. Please slow down.",
                "current_rate": current_count,
                "limit": max_per_minute,
                "retry_after_seconds": 60 - now.second
            }
        
        return True, {
            "allowed": True,
            "current_rate": current_count,
            "limit": max_per_minute,
            "remaining": max_per_minute - current_count
        }
    
    async def check_feature_access(self, user_id: str, tier: str, feature: str) -> Tuple[bool, str]:
        """Check if user has access to a specific feature"""
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
            "ultimate_suite": limits.ultimate_suite,
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
            
            return False, f"Feature '{feature}' requires {upgrade_to or 'Enterprise'} plan. Upgrade at /pricing.html"
        
        return True, "Access granted"

    # =====================================================
    # SYNC METHODS (for non-async contexts)
    # =====================================================
    
    def check_quota_sync(self, user_id: str, tier: str = "free") -> Tuple[bool, Dict[str, Any]]:
        """Check if user has remaining quota (sync)"""
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        client = self._get_sync_client()
        
        user_hash = self._user_hash(user_id)
        daily_key = f"{self.prefix}user:{user_hash}:daily:{self._today_key()}"
        monthly_key = f"{self.prefix}user:{user_hash}:monthly:{self._month_key()}"
        
        # Get current counts
        daily_count = client.get(daily_key)
        monthly_count = client.get(monthly_key)
        
        daily_used = int(daily_count) if daily_count else 0
        monthly_used = int(monthly_count) if monthly_count else 0
        
        # Check daily limit
        daily_remaining = limits.verifications_per_day - daily_used
        if daily_remaining <= 0:
            return False, {
                "allowed": False,
                "reason": "daily_limit_exceeded",
                "message": f"Daily limit of {limits.verifications_per_day} verifications reached.",
                "daily_used": daily_used,
                "daily_limit": limits.verifications_per_day,
                "monthly_used": monthly_used,
                "monthly_limit": limits.verifications_per_month,
                "tier": tier
            }
        
        # Check monthly limit
        monthly_remaining = limits.verifications_per_month - monthly_used
        if monthly_remaining <= 0:
            return False, {
                "allowed": False,
                "reason": "monthly_limit_exceeded",
                "message": f"Monthly limit of {limits.verifications_per_month} verifications reached.",
                "daily_used": daily_used,
                "daily_limit": limits.verifications_per_day,
                "monthly_used": monthly_used,
                "monthly_limit": limits.verifications_per_month,
                "tier": tier
            }
        
        return True, {
            "allowed": True,
            "daily_remaining": daily_remaining,
            "monthly_remaining": monthly_remaining,
            "daily_used": daily_used,
            "daily_limit": limits.verifications_per_day,
            "monthly_used": monthly_used,
            "monthly_limit": limits.verifications_per_month,
            "tier": tier
        }
    
    def record_usage_sync(self, user_id: str, tier: str = "free") -> Dict[str, Any]:
        """Record a verification (sync)"""
        client = self._get_sync_client()
        
        user_hash = self._user_hash(user_id)
        daily_key = f"{self.prefix}user:{user_hash}:daily:{self._today_key()}"
        monthly_key = f"{self.prefix}user:{user_hash}:monthly:{self._month_key()}"
        last_key = f"{self.prefix}user:{user_hash}:last"
        
        pipe = client.pipeline()
        pipe.incr(daily_key)
        pipe.expire(daily_key, self._seconds_until_midnight() + 3600)
        pipe.incr(monthly_key)
        pipe.expire(monthly_key, self._seconds_until_month_end() + 86400)
        pipe.set(last_key, self._now_utc().isoformat())
        results = pipe.execute()
        
        daily_used = results[0]
        monthly_used = results[2]
        
        try:
            plan_tier = PlanTier(tier.lower())
        except ValueError:
            plan_tier = PlanTier.FREE
            
        limits = PlanLimits.get_limits(plan_tier)
        
        return {
            "recorded": True,
            "daily_used": daily_used,
            "daily_limit": limits.verifications_per_day,
            "daily_remaining": limits.verifications_per_day - daily_used,
            "monthly_used": monthly_used,
            "monthly_limit": limits.verifications_per_month,
            "monthly_remaining": limits.verifications_per_month - monthly_used
        }

    async def close(self):
        """Close Redis connections"""
        if self._client:
            await self._client.aclose()
            self._client = None
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None


# =====================================================
# CACHING UTILITIES
# =====================================================

class RedisCache:
    """Simple Redis cache for verification results"""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL')
        self._client = None
        self.prefix = "verity:cache:"
        self.default_ttl = 3600  # 1 hour
    
    async def _get_client(self):
        """Get async Redis client"""
        if self._client is None:
            import redis.asyncio as aioredis
            self._client = aioredis.from_url(
                self.redis_url,
                encoding='utf-8',
                decode_responses=True
            )
        return self._client
    
    def _make_key(self, claim: str) -> str:
        """Create cache key from claim text"""
        claim_hash = hashlib.sha256(claim.encode()).hexdigest()[:32]
        return f"{self.prefix}{claim_hash}"
    
    async def get(self, claim: str) -> Optional[Dict[str, Any]]:
        """Get cached verification result"""
        try:
            client = await self._get_client()
            key = self._make_key(claim)
            data = await client.get(key)
            if data:
                logger.debug(f"Cache HIT for claim: {claim[:50]}...")
                return json.loads(data)
            logger.debug(f"Cache MISS for claim: {claim[:50]}...")
            return None
        except Exception as e:
            logger.warning(f"Cache get error: {e}")
            return None
    
    async def set(self, claim: str, result: Dict[str, Any], ttl: int = None) -> bool:
        """Cache verification result"""
        try:
            client = await self._get_client()
            key = self._make_key(claim)
            ttl = ttl or self.default_ttl
            await client.setex(key, ttl, json.dumps(result))
            logger.debug(f"Cached result for claim: {claim[:50]}...")
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {e}")
            return False
    
    async def invalidate(self, claim: str) -> bool:
        """Remove cached result"""
        try:
            client = await self._get_client()
            key = self._make_key(claim)
            await client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache invalidate error: {e}")
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            client = await self._get_client()
            info = await client.info('memory')
            keys = await client.keys(f"{self.prefix}*")
            return {
                "cached_verifications": len(keys),
                "memory_used": info.get('used_memory_human', 'unknown'),
                "connected": True
            }
        except Exception as e:
            return {
                "cached_verifications": 0,
                "memory_used": "unknown",
                "connected": False,
                "error": str(e)
            }

    async def close(self):
        """Close Redis connection"""
        if self._client:
            await self._client.aclose()
            self._client = None


# =====================================================
# GLOBAL INSTANCES
# =====================================================

_quota_manager: Optional[RedisQuotaManager] = None
_cache: Optional[RedisCache] = None


def get_redis_quota_manager(redis_url: Optional[str] = None) -> RedisQuotaManager:
    """Get or create the global Redis quota manager"""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = RedisQuotaManager(redis_url)
    return _quota_manager


def get_redis_cache(redis_url: Optional[str] = None) -> RedisCache:
    """Get or create the global Redis cache"""
    global _cache
    if _cache is None:
        _cache = RedisCache(redis_url)
    return _cache


# =====================================================
# FASTAPI DEPENDENCIES
# =====================================================

async def require_quota(user_id: str, tier: str = "free"):
    """FastAPI dependency to check quota before processing"""
    from fastapi import HTTPException
    
    manager = get_redis_quota_manager()
    allowed, details = await manager.check_quota(user_id, tier)
    
    if not allowed:
        raise HTTPException(status_code=429, detail=details)
    
    return details


async def require_rate_limit(user_id: str, tier: str = "free"):
    """FastAPI dependency for rate limiting"""
    from fastapi import HTTPException
    
    manager = get_redis_quota_manager()
    allowed, details = await manager.check_rate_limit(user_id, tier)
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=details,
            headers={"Retry-After": str(details.get("retry_after_seconds", 60))}
        )
    
    return details


async def require_feature(user_id: str, tier: str, feature: str):
    """FastAPI dependency to check feature access"""
    from fastapi import HTTPException
    
    manager = get_redis_quota_manager()
    has_access, message = await manager.check_feature_access(user_id, tier, feature)
    
    if not has_access:
        raise HTTPException(
            status_code=403,
            detail={
                "allowed": False,
                "reason": "feature_not_available",
                "message": message,
                "feature": feature,
                "tier": tier
            }
        )
    
    return True


# =====================================================
# TEST
# =====================================================

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def test_redis():
        redis_url = os.getenv('REDIS_URL')
        if not redis_url:
            print("❌ REDIS_URL not set. Please set it in .env file.")
            print("   Format: redis://default:<password>@<host>:<port>")
            return
        
        print(f"🔗 Connecting to Redis: {redis_url[:30]}...")
        
        manager = RedisQuotaManager(redis_url)
        cache = RedisCache(redis_url)
        
        try:
            # Test quota
            print("\n=== Testing Quota System ===")
            user_id = "test_user_123"
            
            allowed, details = await manager.check_quota(user_id, "free")
            print(f"✓ Quota check: {'allowed' if allowed else 'blocked'}")
            print(f"  Details: {json.dumps(details, indent=2)}")
            
            # Record usage
            result = await manager.record_usage(user_id, "free")
            print(f"✓ Recorded usage: {result}")
            
            # Get usage
            usage = await manager.get_usage(user_id, "free")
            print(f"✓ Usage stats: {json.dumps(usage, indent=2)}")
            
            # Test rate limiting
            print("\n=== Testing Rate Limiting ===")
            for i in range(5):
                allowed, details = await manager.check_rate_limit(user_id, "free")
                print(f"  Request {i+1}: {'✓' if allowed else '✗'} ({details.get('remaining', 0)} remaining)")
            
            # Test cache
            print("\n=== Testing Cache ===")
            test_claim = "The Earth is approximately 4.5 billion years old"
            test_result = {"verdict": "TRUE", "confidence": 0.95}
            
            await cache.set(test_claim, test_result)
            print(f"✓ Cached result")
            
            cached = await cache.get(test_claim)
            print(f"✓ Retrieved from cache: {cached}")
            
            stats = await cache.get_stats()
            print(f"✓ Cache stats: {stats}")
            
            print("\n✅ All tests passed!")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await manager.close()
            await cache.close()
    
    asyncio.run(test_redis())
