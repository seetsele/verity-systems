"""
Verity Systems - Carto Integration
Geographic mapping and visualization of misinformation spread

GitHub Education: Carto credits available
Use for: Tracking where misinformation originates and spreads
"""

import os
import json
import logging
import aiohttp
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
import hashlib

logger = logging.getLogger('VerityCarto')

# Configuration
CARTO_API_KEY = os.getenv('CARTO_API_KEY')
CARTO_USERNAME = os.getenv('CARTO_USERNAME', 'verity')
CARTO_API_URL = f'https://{CARTO_USERNAME}.carto.com/api/v2'

# For IP geolocation (fallback)
IPINFO_TOKEN = os.getenv('IPINFO_TOKEN')


@dataclass
class GeoLocation:
    """Geographic location data"""
    latitude: float
    longitude: float
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None


class MisinformationMapper:
    """
    Track and visualize geographic spread of misinformation
    
    Use cases for Verity Systems:
    1. Map where false claims are being checked from
    2. Identify regional misinformation hotspots
    3. Track how misinformation spreads geographically
    4. Correlate topics with geographic regions
    5. Generate geographic reports for researchers
    """
    
    def __init__(self, api_key: str = None, username: str = None):
        self.api_key = api_key or CARTO_API_KEY
        self.username = username or CARTO_USERNAME
        self.api_url = f'https://{self.username}.carto.com/api/v2'
        
        if not self.api_key:
            logger.warning("Carto API key not configured - geographic tracking disabled")
    
    # ============================================================
    # DATA LOGGING
    # ============================================================
    
    async def log_verification(
        self,
        claim_id: str,
        claim_text: str,
        verdict: str,
        confidence: float,
        location: GeoLocation,
        topic: str = 'general',
        sources_count: int = 0
    ) -> bool:
        """
        Log a verification event with geographic data
        
        This creates a record of where fact-checks are happening,
        enabling analysis of misinformation patterns by region.
        """
        if not self.api_key:
            logger.debug("Carto not configured, skipping geo logging")
            return False
        
        # Hash claim for privacy
        claim_hash = hashlib.sha256(claim_text.encode()).hexdigest()[:16]
        
        sql = f"""
        INSERT INTO verity_verifications (
            claim_id, claim_hash, verdict, confidence, topic,
            sources_count, the_geom, city, region, country, 
            country_code, verified_at
        ) VALUES (
            '{claim_id}',
            '{claim_hash}',
            '{verdict}',
            {confidence},
            '{self._sanitize(topic)}',
            {sources_count},
            ST_SetSRID(ST_Point({location.longitude}, {location.latitude}), 4326),
            '{self._sanitize(location.city or "")}',
            '{self._sanitize(location.region or "")}',
            '{self._sanitize(location.country or "")}',
            '{location.country_code or ""}',
            '{datetime.utcnow().isoformat()}'
        )
        """
        
        return await self._execute_sql(sql)
    
    async def log_claim_origin(
        self,
        claim_text: str,
        origin_url: str,
        location: GeoLocation,
        topic: str = 'general'
    ) -> bool:
        """
        Log where a claim originated (if source URL provides location data)
        """
        if not self.api_key:
            return False
        
        claim_hash = hashlib.sha256(claim_text.encode()).hexdigest()[:16]
        
        sql = f"""
        INSERT INTO claim_origins (
            claim_hash, origin_url, topic, the_geom,
            country, logged_at
        ) VALUES (
            '{claim_hash}',
            '{self._sanitize(origin_url)}',
            '{self._sanitize(topic)}',
            ST_SetSRID(ST_Point({location.longitude}, {location.latitude}), 4326),
            '{self._sanitize(location.country or "")}',
            '{datetime.utcnow().isoformat()}'
        )
        """
        
        return await self._execute_sql(sql)
    
    # ============================================================
    # ANALYTICS QUERIES
    # ============================================================
    
    async def get_misinformation_hotspots(
        self,
        days: int = 7,
        min_claims: int = 5,
        verdict_filter: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get clusters of fact-check activity (potential misinformation hotspots)
        
        Returns areas with high concentrations of FALSE or MISLEADING verdicts
        """
        if not self.api_key:
            return []
        
        verdict_clause = f"AND verdict IN ('{verdict_filter}')" if verdict_filter else ""
        
        sql = f"""
        WITH clusters AS (
            SELECT 
                ST_ClusterKMeans(the_geom, 20) OVER() as cluster_id,
                *
            FROM verity_verifications
            WHERE verified_at > NOW() - INTERVAL '{days} days'
            {verdict_clause}
        )
        SELECT 
            cluster_id,
            COUNT(*) as total_claims,
            SUM(CASE WHEN verdict = 'FALSE' THEN 1 ELSE 0 END) as false_claims,
            SUM(CASE WHEN verdict = 'MISLEADING' THEN 1 ELSE 0 END) as misleading_claims,
            AVG(confidence) as avg_confidence,
            ST_Centroid(ST_Collect(the_geom)) as center,
            ST_AsGeoJSON(ST_Centroid(ST_Collect(the_geom))) as center_geojson,
            array_agg(DISTINCT topic) as topics,
            array_agg(DISTINCT country) as countries,
            (SUM(CASE WHEN verdict IN ('FALSE', 'MISLEADING') THEN 1 ELSE 0 END)::float / COUNT(*)::float) as misinfo_rate
        FROM clusters
        GROUP BY cluster_id
        HAVING COUNT(*) >= {min_claims}
        ORDER BY misinfo_rate DESC, total_claims DESC
        LIMIT 50
        """
        
        result = await self._query_sql(sql)
        
        if result:
            return [
                {
                    'cluster_id': row['cluster_id'],
                    'total_claims': row['total_claims'],
                    'false_claims': row['false_claims'],
                    'misleading_claims': row['misleading_claims'],
                    'misinfo_rate': round(row['misinfo_rate'] * 100, 1),
                    'avg_confidence': round(row['avg_confidence'], 1),
                    'center': json.loads(row['center_geojson']),
                    'topics': row['topics'],
                    'countries': row['countries']
                }
                for row in result
            ]
        return []
    
    async def get_regional_statistics(
        self,
        country: str = None,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get fact-check statistics aggregated by region
        """
        if not self.api_key:
            return []
        
        where_clause = f"AND country = '{country}'" if country else ""
        
        sql = f"""
        SELECT 
            country,
            region,
            COUNT(*) as total_verifications,
            SUM(CASE WHEN verdict = 'TRUE' THEN 1 ELSE 0 END) as true_count,
            SUM(CASE WHEN verdict = 'FALSE' THEN 1 ELSE 0 END) as false_count,
            SUM(CASE WHEN verdict = 'PARTIALLY_TRUE' THEN 1 ELSE 0 END) as partial_count,
            SUM(CASE WHEN verdict = 'MISLEADING' THEN 1 ELSE 0 END) as misleading_count,
            AVG(confidence) as avg_confidence,
            array_agg(DISTINCT topic ORDER BY topic) as topics
        FROM verity_verifications
        WHERE verified_at > NOW() - INTERVAL '{days} days'
        {where_clause}
        GROUP BY country, region
        ORDER BY total_verifications DESC
        """
        
        result = await self._query_sql(sql)
        
        if result:
            return [
                {
                    'country': row['country'],
                    'region': row['region'],
                    'total': row['total_verifications'],
                    'verdicts': {
                        'true': row['true_count'],
                        'false': row['false_count'],
                        'partial': row['partial_count'],
                        'misleading': row['misleading_count']
                    },
                    'avg_confidence': round(row['avg_confidence'], 1),
                    'topics': row['topics']
                }
                for row in result
            ]
        return []
    
    async def get_topic_geography(
        self,
        topic: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get geographic distribution of a specific topic
        """
        if not self.api_key:
            return {}
        
        sql = f"""
        SELECT 
            country,
            COUNT(*) as claim_count,
            AVG(confidence) as avg_confidence,
            SUM(CASE WHEN verdict = 'FALSE' THEN 1 ELSE 0 END)::float / COUNT(*)::float as false_rate,
            ST_AsGeoJSON(ST_Centroid(ST_Collect(the_geom))) as center
        FROM verity_verifications
        WHERE topic = '{self._sanitize(topic)}'
        AND verified_at > NOW() - INTERVAL '{days} days'
        GROUP BY country
        ORDER BY claim_count DESC
        """
        
        result = await self._query_sql(sql)
        
        if result:
            return {
                'topic': topic,
                'countries': [
                    {
                        'country': row['country'],
                        'claim_count': row['claim_count'],
                        'false_rate': round(row['false_rate'] * 100, 1),
                        'center': json.loads(row['center']) if row['center'] else None
                    }
                    for row in result
                ]
            }
        return {'topic': topic, 'countries': []}
    
    async def get_spread_timeline(
        self,
        claim_hash: str,
        hours: int = 72
    ) -> List[Dict[str, Any]]:
        """
        Track how a specific claim spreads geographically over time
        """
        if not self.api_key:
            return []
        
        sql = f"""
        SELECT 
            date_trunc('hour', verified_at) as hour,
            COUNT(*) as check_count,
            array_agg(DISTINCT country) as countries,
            ST_AsGeoJSON(ST_Collect(the_geom)) as points
        FROM verity_verifications
        WHERE claim_hash = '{claim_hash}'
        AND verified_at > NOW() - INTERVAL '{hours} hours'
        GROUP BY date_trunc('hour', verified_at)
        ORDER BY hour
        """
        
        result = await self._query_sql(sql)
        
        if result:
            return [
                {
                    'timestamp': row['hour'].isoformat() if row['hour'] else None,
                    'check_count': row['check_count'],
                    'countries': row['countries'],
                    'points': json.loads(row['points']) if row['points'] else None
                }
                for row in result
            ]
        return []
    
    # ============================================================
    # MAP GENERATION
    # ============================================================
    
    def get_embed_map_url(self, map_type: str = 'verifications') -> str:
        """
        Get URL for embeddable Carto map
        
        Map types:
        - verifications: All verification activity
        - hotspots: Misinformation hotspots
        - topics: Topic distribution
        """
        map_ids = {
            'verifications': 'verity-verification-map',
            'hotspots': 'verity-hotspot-map',
            'topics': 'verity-topic-map'
        }
        
        map_id = map_ids.get(map_type, map_ids['verifications'])
        return f'https://{self.username}.carto.com/builder/{map_id}/embed'
    
    def get_iframe_embed(self, map_type: str = 'verifications', width: int = 800, height: int = 600) -> str:
        """Generate iframe embed code"""
        url = self.get_embed_map_url(map_type)
        return f'<iframe src="{url}" width="{width}" height="{height}" frameborder="0" allowfullscreen></iframe>'
    
    # ============================================================
    # HELPER METHODS
    # ============================================================
    
    def _sanitize(self, value: str) -> str:
        """Sanitize string for SQL"""
        if not value:
            return ''
        return value.replace("'", "''").replace(";", "")[:500]
    
    async def _execute_sql(self, sql: str) -> bool:
        """Execute SQL statement"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{self.api_url}/sql',
                    params={'q': sql, 'api_key': self.api_key}
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Carto SQL execution failed: {e}")
            return False
    
    async def _query_sql(self, sql: str) -> Optional[List[Dict]]:
        """Execute SQL query and return results"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f'{self.api_url}/sql',
                    params={'q': sql, 'api_key': self.api_key}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get('rows', [])
        except Exception as e:
            logger.error(f"Carto SQL query failed: {e}")
        return None


# ============================================================
# IP GEOLOCATION HELPER
# ============================================================

async def get_location_from_ip(ip_address: str) -> Optional[GeoLocation]:
    """
    Get geographic location from IP address
    Uses ipinfo.io or similar service
    """
    if ip_address in ('127.0.0.1', 'localhost', '::1'):
        # Return default for localhost
        return GeoLocation(
            latitude=0,
            longitude=0,
            city='Local',
            region='Development',
            country='Local',
            country_code='XX'
        )
    
    try:
        async with aiohttp.ClientSession() as session:
            url = f'https://ipinfo.io/{ip_address}/json'
            params = {'token': IPINFO_TOKEN} if IPINFO_TOKEN else {}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Parse location
                    loc = data.get('loc', '0,0').split(',')
                    
                    return GeoLocation(
                        latitude=float(loc[0]) if loc else 0,
                        longitude=float(loc[1]) if len(loc) > 1 else 0,
                        city=data.get('city'),
                        region=data.get('region'),
                        country=data.get('country'),
                        country_code=data.get('country')
                    )
    except Exception as e:
        logger.error(f"Failed to get location for IP {ip_address}: {e}")
    
    return None


# ============================================================
# FASTAPI INTEGRATION
# ============================================================

class CartoMiddleware:
    """
    Middleware to track verification geography
    
    Add to FastAPI:
    app.add_middleware(CartoMiddleware)
    """
    
    def __init__(self, app):
        self.app = app
        self.mapper = MisinformationMapper()
    
    async def __call__(self, scope, receive, send):
        # Only track verification endpoints
        if scope['type'] == 'http' and '/verify' in scope['path']:
            # Get client IP
            client_ip = None
            for header in scope.get('headers', []):
                if header[0] == b'x-forwarded-for':
                    client_ip = header[1].decode().split(',')[0].strip()
                    break
            
            if not client_ip:
                client_ip = scope.get('client', [None])[0]
            
            # Store IP for later use in endpoint
            scope['client_ip'] = client_ip
        
        await self.app(scope, receive, send)


# API endpoints for dashboard
async def get_misinformation_dashboard_data(days: int = 7) -> Dict[str, Any]:
    """Get all data needed for misinformation dashboard"""
    mapper = MisinformationMapper()
    
    hotspots = await mapper.get_misinformation_hotspots(days=days)
    regional_stats = await mapper.get_regional_statistics(days=days)
    
    return {
        'hotspots': hotspots,
        'regional_stats': regional_stats,
        'embed_url': mapper.get_embed_map_url('hotspots'),
        'generated_at': datetime.utcnow().isoformat()
    }


# ============================================================
# DATABASE SETUP SQL
# ============================================================

SETUP_SQL = """
-- Create table for verification events
CREATE TABLE IF NOT EXISTS verity_verifications (
    id SERIAL PRIMARY KEY,
    claim_id VARCHAR(50),
    claim_hash VARCHAR(32),
    verdict VARCHAR(20),
    confidence FLOAT,
    topic VARCHAR(100),
    sources_count INT,
    the_geom GEOMETRY(Point, 4326),
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100),
    country_code VARCHAR(5),
    verified_at TIMESTAMP DEFAULT NOW()
);

-- Create spatial index
CREATE INDEX IF NOT EXISTS idx_verifications_geom ON verity_verifications USING GIST(the_geom);

-- Create index for time-based queries
CREATE INDEX IF NOT EXISTS idx_verifications_time ON verity_verifications(verified_at);

-- Create table for claim origins
CREATE TABLE IF NOT EXISTS claim_origins (
    id SERIAL PRIMARY KEY,
    claim_hash VARCHAR(32),
    origin_url TEXT,
    topic VARCHAR(100),
    the_geom GEOMETRY(Point, 4326),
    country VARCHAR(100),
    logged_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_origins_geom ON claim_origins USING GIST(the_geom);
"""


# ============================================================
# EXAMPLE USAGE
# ============================================================

if __name__ == "__main__":
    import asyncio
    
    async def test_carto():
        mapper = MisinformationMapper()
        
        # Test location lookup
        location = await get_location_from_ip('8.8.8.8')
        if location:
            print(f"IP Location: {location.city}, {location.country}")
        
        # Test with sample data
        if CARTO_API_KEY:
            test_location = GeoLocation(
                latitude=40.7128,
                longitude=-74.0060,
                city='New York',
                region='NY',
                country='United States',
                country_code='US'
            )
            
            logged = await mapper.log_verification(
                claim_id='test-001',
                claim_text='Test claim for geographic tracking',
                verdict='FALSE',
                confidence=85.5,
                location=test_location,
                topic='test',
                sources_count=5
            )
            print(f"Logged verification: {'✅' if logged else '❌'}")
            
            # Get hotspots
            hotspots = await mapper.get_misinformation_hotspots(days=30)
            print(f"Found {len(hotspots)} hotspots")
        else:
            print("Carto API key not configured - skipping live tests")
        
        print("\n✅ Carto integration tested!")
    
    asyncio.run(test_carto())
