"""
ETA Cache Service

Implements Redis-based ETA caching with appropriate TTL, background tasks for
ETA recalculation and cache updates, and ETA confidence scoring.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
import redis.asyncio as redis
from sqlalchemy.orm import Session

from ..models.vehicle import Vehicle, VehicleStatus
from ..models.stop import Stop
from ..models.subscription import Subscription
from ..core.database import get_db
from .eta_calculation_service import ETAResult, eta_service
from .location_tracking_service import location_service

logger = logging.getLogger(__name__)

@dataclass
class ETACacheEntry:
    """ETA cache entry with metadata"""
    eta_result: ETAResult
    cache_timestamp: datetime
    access_count: int
    last_accessed: datetime
    priority_score: float

@dataclass
class ETAUpdateTask:
    """Background ETA update task"""
    vehicle_id: int
    stop_id: int
    priority: int
    scheduled_at: datetime
    retry_count: int = 0

class ETACacheService:
    """Service for managing ETA caching and background updates"""
    
    def __init__(self, redis_client: redis.Redis = None):
        self.redis_client = redis_client
        self.cache_entries: Dict[str, ETACacheEntry] = {}
        self.update_queue: List[ETAUpdateTask] = []
        self.active_subscriptions: Dict[int, Set[int]] = {}  # stop_id -> set of vehicle_ids
        self.confidence_thresholds = {
            "high": 0.8,
            "medium": 0.6,
            "low": 0.4
        }
        
        # Configuration
        self.default_ttl = 120  # 2 minutes default TTL
        self.high_confidence_ttl = 180  # 3 minutes for high confidence
        self.low_confidence_ttl = 60   # 1 minute for low confidence
        self.max_cache_size = 10000    # Maximum cache entries
        self.update_interval = 30      # Background update interval (seconds)
        self.batch_size = 50          # Batch size for updates
        
    async def initialize(self):
        """Initialize the ETA cache service"""
        if not self.redis_client:
            self.redis_client = redis.from_url("redis://localhost:6379")
        
        # Load active subscriptions
        await self._load_active_subscriptions()
        
        # Start background tasks
        asyncio.create_task(self._background_eta_updater())
        asyncio.create_task(self._cache_cleanup_task())
        asyncio.create_task(self._subscription_monitor())
        
        logger.info("ETA cache service initialized")
    
    async def get_eta(self, vehicle_id: int, stop_id: int, 
                     force_recalculate: bool = False) -> Optional[ETAResult]:
        """
        Get ETA with intelligent caching
        
        Args:
            vehicle_id: ID of the vehicle
            stop_id: ID of the destination stop
            force_recalculate: Force recalculation even if cached
            
        Returns:
            ETAResult or None if calculation fails
        """
        cache_key = self._get_cache_key(vehicle_id, stop_id)
        
        # Check cache first (unless forced recalculation)
        if not force_recalculate:
            cached_eta = await self._get_cached_eta(cache_key)
            if cached_eta and self._is_cache_valid(cached_eta):
                # Update access statistics
                await self._update_access_stats(cache_key)
                return cached_eta.eta_result
        
        # Calculate new ETA
        eta_result = await eta_service.calculate_eta(vehicle_id, stop_id)
        if not eta_result:
            return None
        
        # Cache the result with appropriate TTL
        await self._cache_eta_result(cache_key, eta_result)
        
        # Schedule background updates if this is a high-priority ETA
        await self._schedule_background_update(vehicle_id, stop_id, eta_result)
        
        return eta_result
    
    async def get_multiple_etas(self, vehicle_stop_pairs: List[Tuple[int, int]]) -> Dict[Tuple[int, int], Optional[ETAResult]]:
        """Get multiple ETAs efficiently"""
        results = {}
        
        # Check cache for all pairs first
        cache_hits = {}
        cache_misses = []
        
        for vehicle_id, stop_id in vehicle_stop_pairs:
            cache_key = self._get_cache_key(vehicle_id, stop_id)
            cached_eta = await self._get_cached_eta(cache_key)
            
            if cached_eta and self._is_cache_valid(cached_eta):
                cache_hits[(vehicle_id, stop_id)] = cached_eta.eta_result
                await self._update_access_stats(cache_key)
            else:
                cache_misses.append((vehicle_id, stop_id))
        
        # Calculate missing ETAs in parallel
        if cache_misses:
            tasks = []
            for vehicle_id, stop_id in cache_misses:
                task = asyncio.create_task(
                    eta_service.calculate_eta(vehicle_id, stop_id)
                )
                tasks.append((vehicle_id, stop_id, task))
            
            # Wait for all calculations
            for vehicle_id, stop_id, task in tasks:
                try:
                    eta_result = await task
                    if eta_result:
                        cache_key = self._get_cache_key(vehicle_id, stop_id)
                        await self._cache_eta_result(cache_key, eta_result)
                        results[(vehicle_id, stop_id)] = eta_result
                        
                        # Schedule background updates
                        await self._schedule_background_update(vehicle_id, stop_id, eta_result)
                    else:
                        results[(vehicle_id, stop_id)] = None
                        
                except Exception as e:
                    logger.error(f"Error calculating ETA for vehicle {vehicle_id}, stop {stop_id}: {e}")
                    results[(vehicle_id, stop_id)] = None
        
        # Combine cache hits and new calculations
        results.update(cache_hits)
        return results
    
    async def invalidate_vehicle_etas(self, vehicle_id: int):
        """Invalidate all cached ETAs for a vehicle"""
        try:
            pattern = f"eta:{vehicle_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} ETA cache entries for vehicle {vehicle_id}")
            
            # Remove from local cache
            keys_to_remove = [key for key in self.cache_entries.keys() 
                            if key.startswith(f"eta:{vehicle_id}:")]
            for key in keys_to_remove:
                del self.cache_entries[key]
                
        except Exception as e:
            logger.error(f"Error invalidating ETAs for vehicle {vehicle_id}: {e}")
    
    async def invalidate_stop_etas(self, stop_id: int):
        """Invalidate all cached ETAs for a stop"""
        try:
            pattern = f"eta:*:{stop_id}"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                await self.redis_client.delete(*keys)
                logger.debug(f"Invalidated {len(keys)} ETA cache entries for stop {stop_id}")
            
            # Remove from local cache
            keys_to_remove = [key for key in self.cache_entries.keys() 
                            if key.endswith(f":{stop_id}")]
            for key in keys_to_remove:
                del self.cache_entries[key]
                
        except Exception as e:
            logger.error(f"Error invalidating ETAs for stop {stop_id}: {e}")
    
    async def get_eta_confidence_score(self, eta_result: ETAResult) -> Dict[str, any]:
        """Calculate comprehensive confidence score for ETA"""
        try:
            # Base confidence from calculation
            base_confidence = eta_result.confidence
            
            # Age factor (newer is better)
            age_seconds = (datetime.now() - eta_result.calculated_at).total_seconds()
            age_factor = max(0.1, 1.0 - (age_seconds / 300))  # Decay over 5 minutes
            
            # Method factor (some methods are more reliable)
            method_factors = {
                "route_aware": 1.0,
                "historical": 0.9,
                "haversine": 0.7
            }
            method_factor = method_factors.get(eta_result.calculation_method, 0.5)
            
            # Speed consistency factor
            speed_factor = 1.0
            if eta_result.average_speed_kmh < 5 or eta_result.average_speed_kmh > 60:
                speed_factor = 0.8
            
            # Traffic factor impact
            traffic_impact = abs(eta_result.traffic_factor - 1.0)
            traffic_factor = max(0.7, 1.0 - traffic_impact)
            
            # Delay factor impact
            delay_impact = abs(eta_result.delay_factor - 1.0)
            delay_factor = max(0.7, 1.0 - delay_impact)
            
            # Calculate composite confidence
            composite_confidence = (
                base_confidence * 0.4 +
                age_factor * 0.2 +
                method_factor * 0.2 +
                speed_factor * 0.1 +
                traffic_factor * 0.05 +
                delay_factor * 0.05
            )
            
            # Determine confidence level
            if composite_confidence >= self.confidence_thresholds["high"]:
                confidence_level = "high"
            elif composite_confidence >= self.confidence_thresholds["medium"]:
                confidence_level = "medium"
            else:
                confidence_level = "low"
            
            return {
                "composite_confidence": composite_confidence,
                "confidence_level": confidence_level,
                "factors": {
                    "base_confidence": base_confidence,
                    "age_factor": age_factor,
                    "method_factor": method_factor,
                    "speed_factor": speed_factor,
                    "traffic_factor": traffic_factor,
                    "delay_factor": delay_factor
                },
                "age_seconds": age_seconds,
                "recommended_ttl": self._get_ttl_for_confidence(composite_confidence)
            }
            
        except Exception as e:
            logger.error(f"Error calculating confidence score: {e}")
            return {
                "composite_confidence": 0.5,
                "confidence_level": "medium",
                "factors": {},
                "age_seconds": 0,
                "recommended_ttl": self.default_ttl
            }
    
    def _get_cache_key(self, vehicle_id: int, stop_id: int) -> str:
        """Generate cache key for vehicle-stop pair"""
        return f"eta:{vehicle_id}:{stop_id}"
    
    async def _get_cached_eta(self, cache_key: str) -> Optional[ETACacheEntry]:
        """Get ETA from cache"""
        # Check local cache first
        if cache_key in self.cache_entries:
            return self.cache_entries[cache_key]
        
        # Check Redis cache
        if self.redis_client:
            try:
                cached_data = await self.redis_client.get(cache_key)
                if cached_data:
                    data = json.loads(cached_data)
                    eta_data = data["eta_result"]
                    eta_data["calculated_at"] = datetime.fromisoformat(eta_data["calculated_at"])
                    
                    eta_result = ETAResult(**eta_data)
                    cache_entry = ETACacheEntry(
                        eta_result=eta_result,
                        cache_timestamp=datetime.fromisoformat(data["cache_timestamp"]),
                        access_count=data.get("access_count", 0),
                        last_accessed=datetime.fromisoformat(data.get("last_accessed", datetime.now().isoformat())),
                        priority_score=data.get("priority_score", 0.0)
                    )
                    
                    # Update local cache
                    self.cache_entries[cache_key] = cache_entry
                    return cache_entry
                    
            except Exception as e:
                logger.error(f"Error reading from cache: {e}")
        
        return None
    
    def _is_cache_valid(self, cache_entry: ETACacheEntry) -> bool:
        """Check if cache entry is still valid"""
        age = (datetime.now() - cache_entry.cache_timestamp).total_seconds()
        
        # Get TTL based on confidence
        confidence_score = cache_entry.eta_result.confidence
        ttl = self._get_ttl_for_confidence(confidence_score)
        
        return age < ttl
    
    def _get_ttl_for_confidence(self, confidence: float) -> int:
        """Get TTL based on confidence score"""
        if confidence >= self.confidence_thresholds["high"]:
            return self.high_confidence_ttl
        elif confidence >= self.confidence_thresholds["low"]:
            return self.default_ttl
        else:
            return self.low_confidence_ttl
    
    async def _cache_eta_result(self, cache_key: str, eta_result: ETAResult):
        """Cache ETA result with appropriate TTL"""
        try:
            cache_entry = ETACacheEntry(
                eta_result=eta_result,
                cache_timestamp=datetime.now(),
                access_count=1,
                last_accessed=datetime.now(),
                priority_score=self._calculate_priority_score(eta_result)
            )
            
            # Update local cache
            self.cache_entries[cache_key] = cache_entry
            
            # Update Redis cache
            if self.redis_client:
                cache_data = {
                    "eta_result": asdict(eta_result),
                    "cache_timestamp": cache_entry.cache_timestamp.isoformat(),
                    "access_count": cache_entry.access_count,
                    "last_accessed": cache_entry.last_accessed.isoformat(),
                    "priority_score": cache_entry.priority_score
                }
                
                # Convert datetime to string for JSON serialization
                cache_data["eta_result"]["calculated_at"] = eta_result.calculated_at.isoformat()
                
                ttl = self._get_ttl_for_confidence(eta_result.confidence)
                await self.redis_client.setex(cache_key, ttl, json.dumps(cache_data))
            
            # Manage cache size
            await self._manage_cache_size()
            
        except Exception as e:
            logger.error(f"Error caching ETA result: {e}")
    
    async def _update_access_stats(self, cache_key: str):
        """Update access statistics for cache entry"""
        if cache_key in self.cache_entries:
            entry = self.cache_entries[cache_key]
            entry.access_count += 1
            entry.last_accessed = datetime.now()
            entry.priority_score = self._calculate_priority_score(entry.eta_result)
    
    def _calculate_priority_score(self, eta_result: ETAResult) -> float:
        """Calculate priority score for cache entry"""
        # Higher priority for:
        # - Higher confidence
        # - Shorter ETA (more urgent)
        # - Recent calculations
        
        confidence_score = eta_result.confidence * 0.4
        
        # Urgency score (shorter ETA = higher priority)
        urgency_score = max(0, (1800 - eta_result.eta_seconds) / 1800) * 0.3  # 30 min max
        
        # Recency score
        age_seconds = (datetime.now() - eta_result.calculated_at).total_seconds()
        recency_score = max(0, (300 - age_seconds) / 300) * 0.3  # 5 min max
        
        return confidence_score + urgency_score + recency_score
    
    async def _schedule_background_update(self, vehicle_id: int, stop_id: int, eta_result: ETAResult):
        """Schedule background ETA update"""
        # Only schedule updates for high-priority ETAs
        priority_score = self._calculate_priority_score(eta_result)
        
        if priority_score > 0.6:  # High priority threshold
            # Schedule update before cache expires
            ttl = self._get_ttl_for_confidence(eta_result.confidence)
            update_delay = max(30, ttl - 30)  # Update 30 seconds before expiry
            
            update_task = ETAUpdateTask(
                vehicle_id=vehicle_id,
                stop_id=stop_id,
                priority=int(priority_score * 100),
                scheduled_at=datetime.now() + timedelta(seconds=update_delay)
            )
            
            self.update_queue.append(update_task)
            self.update_queue.sort(key=lambda x: (x.scheduled_at, -x.priority))
    
    async def _background_eta_updater(self):
        """Background task to update high-priority ETAs"""
        try:
            while True:
                current_time = datetime.now()
                
                # Process due updates
                due_updates = []
                remaining_updates = []
                
                for task in self.update_queue:
                    if task.scheduled_at <= current_time:
                        due_updates.append(task)
                    else:
                        remaining_updates.append(task)
                
                self.update_queue = remaining_updates
                
                # Process updates in batches
                for i in range(0, len(due_updates), self.batch_size):
                    batch = due_updates[i:i + self.batch_size]
                    await self._process_update_batch(batch)
                
                await asyncio.sleep(self.update_interval)
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in background ETA updater: {e}")
    
    async def _process_update_batch(self, batch: List[ETAUpdateTask]):
        """Process a batch of ETA updates"""
        tasks = []
        
        for update_task in batch:
            task = asyncio.create_task(
                self._update_single_eta(update_task)
            )
            tasks.append(task)
        
        # Wait for all updates to complete
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _update_single_eta(self, update_task: ETAUpdateTask):
        """Update a single ETA"""
        try:
            # Force recalculation
            eta_result = await self.get_eta(
                update_task.vehicle_id, 
                update_task.stop_id, 
                force_recalculate=True
            )
            
            if eta_result:
                logger.debug(f"Updated ETA for vehicle {update_task.vehicle_id}, stop {update_task.stop_id}")
            else:
                # Retry with exponential backoff
                if update_task.retry_count < 3:
                    update_task.retry_count += 1
                    update_task.scheduled_at = datetime.now() + timedelta(
                        seconds=30 * (2 ** update_task.retry_count)
                    )
                    self.update_queue.append(update_task)
                    
        except Exception as e:
            logger.error(f"Error updating ETA for vehicle {update_task.vehicle_id}, stop {update_task.stop_id}: {e}")
    
    async def _manage_cache_size(self):
        """Manage cache size by removing low-priority entries"""
        if len(self.cache_entries) > self.max_cache_size:
            # Sort by priority score (ascending) and remove lowest priority entries
            sorted_entries = sorted(
                self.cache_entries.items(),
                key=lambda x: x[1].priority_score
            )
            
            # Remove 10% of entries
            remove_count = len(self.cache_entries) // 10
            for i in range(remove_count):
                cache_key = sorted_entries[i][0]
                del self.cache_entries[cache_key]
                
                # Also remove from Redis
                if self.redis_client:
                    try:
                        await self.redis_client.delete(cache_key)
                    except Exception as e:
                        logger.error(f"Error removing cache entry from Redis: {e}")
    
    async def _cache_cleanup_task(self):
        """Background task to clean up expired cache entries"""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = datetime.now()
                expired_keys = []
                
                for cache_key, cache_entry in self.cache_entries.items():
                    if not self._is_cache_valid(cache_entry):
                        expired_keys.append(cache_key)
                
                # Remove expired entries
                for cache_key in expired_keys:
                    del self.cache_entries[cache_key]
                
                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")
    
    async def _load_active_subscriptions(self):
        """Load active subscriptions to prioritize ETA calculations"""
        try:
            db = next(get_db())
            try:
                subscriptions = db.query(Subscription).filter(
                    Subscription.is_active == True
                ).all()
                
                for subscription in subscriptions:
                    stop_id = subscription.stop_id
                    if stop_id not in self.active_subscriptions:
                        self.active_subscriptions[stop_id] = set()
                    
                    # We don't have direct vehicle subscription, so we'll monitor all vehicles for subscribed stops
                    # This would be optimized in a real implementation
                
                logger.info(f"Loaded {len(subscriptions)} active subscriptions for {len(self.active_subscriptions)} stops")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading active subscriptions: {e}")
    
    async def _subscription_monitor(self):
        """Monitor subscription changes and update priorities"""
        try:
            while True:
                await asyncio.sleep(600)  # Check every 10 minutes
                await self._load_active_subscriptions()
                
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error in subscription monitor: {e}")
    
    async def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics"""
        try:
            total_entries = len(self.cache_entries)
            
            # Calculate confidence distribution
            confidence_distribution = {"high": 0, "medium": 0, "low": 0}
            total_access_count = 0
            
            for entry in self.cache_entries.values():
                confidence = entry.eta_result.confidence
                if confidence >= self.confidence_thresholds["high"]:
                    confidence_distribution["high"] += 1
                elif confidence >= self.confidence_thresholds["medium"]:
                    confidence_distribution["medium"] += 1
                else:
                    confidence_distribution["low"] += 1
                
                total_access_count += entry.access_count
            
            # Redis stats
            redis_info = {}
            if self.redis_client:
                try:
                    redis_info = await self.redis_client.info("memory")
                except Exception as e:
                    logger.error(f"Error getting Redis info: {e}")
            
            return {
                "total_entries": total_entries,
                "confidence_distribution": confidence_distribution,
                "total_access_count": total_access_count,
                "pending_updates": len(self.update_queue),
                "active_subscriptions": len(self.active_subscriptions),
                "redis_info": redis_info,
                "cache_hit_ratio": getattr(self, '_cache_hit_ratio', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Global instance
eta_cache_service = ETACacheService()