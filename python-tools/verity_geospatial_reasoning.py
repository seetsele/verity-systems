"""
Verity Geospatial Reasoning Engine
==================================
Location-aware fact-checking with geographic context.

Features:
- Location extraction and normalization
- Geographic claim validation
- Regional context awareness
- Distance/proximity calculations
- Jurisdictional reasoning
"""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum


class LocationType(Enum):
    """Types of geographic references"""
    COUNTRY = "country"
    STATE_PROVINCE = "state_province"
    CITY = "city"
    REGION = "region"
    LANDMARK = "landmark"
    COORDINATES = "coordinates"
    GENERIC = "generic"


@dataclass
class GeoLocation:
    """A geographic location"""
    name: str
    location_type: LocationType
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    aliases: List[str] = field(default_factory=list)


@dataclass
class GeoContext:
    """Geographic context for a claim"""
    locations: List[GeoLocation] = field(default_factory=list)
    is_location_sensitive: bool = False
    jurisdiction: Optional[str] = None
    regional_variations: List[str] = field(default_factory=list)


# Comprehensive geographic database
COUNTRY_DATABASE: Dict[str, GeoLocation] = {
    # Major countries with coordinates and population
    "united states": GeoLocation("United States", LocationType.COUNTRY, "United States", 39.8, -98.5, 331000000, ["USA", "US", "America"]),
    "china": GeoLocation("China", LocationType.COUNTRY, "China", 35.9, 104.2, 1400000000, ["PRC", "People's Republic of China"]),
    "india": GeoLocation("India", LocationType.COUNTRY, "India", 20.6, 78.9, 1380000000, ["Bharat"]),
    "russia": GeoLocation("Russia", LocationType.COUNTRY, "Russia", 61.5, 105.3, 145000000, ["Russian Federation"]),
    "japan": GeoLocation("Japan", LocationType.COUNTRY, "Japan", 36.2, 138.2, 126000000, ["Nippon"]),
    "germany": GeoLocation("Germany", LocationType.COUNTRY, "Germany", 51.2, 10.5, 83000000, ["Deutschland"]),
    "united kingdom": GeoLocation("United Kingdom", LocationType.COUNTRY, "United Kingdom", 55.4, -3.4, 67000000, ["UK", "Britain", "Great Britain"]),
    "france": GeoLocation("France", LocationType.COUNTRY, "France", 46.2, 2.2, 67000000, []),
    "italy": GeoLocation("Italy", LocationType.COUNTRY, "Italy", 41.9, 12.6, 60000000, []),
    "brazil": GeoLocation("Brazil", LocationType.COUNTRY, "Brazil", -14.2, -51.9, 212000000, ["Brasil"]),
    "canada": GeoLocation("Canada", LocationType.COUNTRY, "Canada", 56.1, -106.3, 38000000, []),
    "australia": GeoLocation("Australia", LocationType.COUNTRY, "Australia", -25.3, 133.8, 25000000, ["Oz"]),
    "south korea": GeoLocation("South Korea", LocationType.COUNTRY, "South Korea", 35.9, 128.0, 52000000, ["Korea", "ROK"]),
    "mexico": GeoLocation("Mexico", LocationType.COUNTRY, "Mexico", 23.6, -102.6, 128000000, []),
    "spain": GeoLocation("Spain", LocationType.COUNTRY, "Spain", 40.5, -3.7, 47000000, ["España"]),
}

CITY_DATABASE: Dict[str, GeoLocation] = {
    # Major world cities
    "new york": GeoLocation("New York", LocationType.CITY, "United States", 40.7, -74.0, 8400000, ["NYC", "New York City"]),
    "los angeles": GeoLocation("Los Angeles", LocationType.CITY, "United States", 34.1, -118.2, 3900000, ["LA"]),
    "chicago": GeoLocation("Chicago", LocationType.CITY, "United States", 41.9, -87.6, 2700000, []),
    "houston": GeoLocation("Houston", LocationType.CITY, "United States", 29.8, -95.4, 2300000, []),
    "london": GeoLocation("London", LocationType.CITY, "United Kingdom", 51.5, -0.1, 9000000, []),
    "paris": GeoLocation("Paris", LocationType.CITY, "France", 48.9, 2.4, 2200000, []),
    "tokyo": GeoLocation("Tokyo", LocationType.CITY, "Japan", 35.7, 139.7, 14000000, []),
    "beijing": GeoLocation("Beijing", LocationType.CITY, "China", 39.9, 116.4, 21500000, ["Peking"]),
    "shanghai": GeoLocation("Shanghai", LocationType.CITY, "China", 31.2, 121.5, 27000000, []),
    "mumbai": GeoLocation("Mumbai", LocationType.CITY, "India", 19.1, 72.9, 12500000, ["Bombay"]),
    "sydney": GeoLocation("Sydney", LocationType.CITY, "Australia", -33.9, 151.2, 5300000, []),
    "toronto": GeoLocation("Toronto", LocationType.CITY, "Canada", 43.7, -79.4, 2900000, []),
    "berlin": GeoLocation("Berlin", LocationType.CITY, "Germany", 52.5, 13.4, 3600000, []),
    "moscow": GeoLocation("Moscow", LocationType.CITY, "Russia", 55.8, 37.6, 12500000, ["Moskva"]),
    "dubai": GeoLocation("Dubai", LocationType.CITY, "UAE", 25.2, 55.3, 3400000, []),
    "singapore": GeoLocation("Singapore", LocationType.CITY, "Singapore", 1.4, 103.8, 5700000, []),
}

US_STATE_DATABASE: Dict[str, GeoLocation] = {
    "california": GeoLocation("California", LocationType.STATE_PROVINCE, "United States", 36.8, -119.4, 39500000, ["CA"]),
    "texas": GeoLocation("Texas", LocationType.STATE_PROVINCE, "United States", 31.0, -100.0, 29000000, ["TX"]),
    "florida": GeoLocation("Florida", LocationType.STATE_PROVINCE, "United States", 27.7, -81.7, 21500000, ["FL"]),
    "new york": GeoLocation("New York State", LocationType.STATE_PROVINCE, "United States", 43.0, -75.0, 19400000, ["NY"]),
    "pennsylvania": GeoLocation("Pennsylvania", LocationType.STATE_PROVINCE, "United States", 41.2, -77.2, 12800000, ["PA"]),
    "illinois": GeoLocation("Illinois", LocationType.STATE_PROVINCE, "United States", 40.6, -89.4, 12700000, ["IL"]),
    "ohio": GeoLocation("Ohio", LocationType.STATE_PROVINCE, "United States", 40.4, -82.9, 11700000, ["OH"]),
    "georgia": GeoLocation("Georgia", LocationType.STATE_PROVINCE, "United States", 32.2, -83.7, 10600000, ["GA"]),
    "washington": GeoLocation("Washington", LocationType.STATE_PROVINCE, "United States", 47.8, -120.7, 7600000, ["WA"]),
    "massachusetts": GeoLocation("Massachusetts", LocationType.STATE_PROVINCE, "United States", 42.4, -71.4, 6900000, ["MA"]),
}

REGION_DATABASE: Dict[str, GeoLocation] = {
    "europe": GeoLocation("Europe", LocationType.REGION, None, 54.5, 15.3, 750000000, ["EU"]),
    "asia": GeoLocation("Asia", LocationType.REGION, None, 34.0, 100.6, 4600000000, []),
    "africa": GeoLocation("Africa", LocationType.REGION, None, -8.8, 34.5, 1300000000, []),
    "north america": GeoLocation("North America", LocationType.REGION, None, 54.5, -105.3, 580000000, []),
    "south america": GeoLocation("South America", LocationType.REGION, None, -8.8, -55.5, 430000000, []),
    "middle east": GeoLocation("Middle East", LocationType.REGION, None, 29.3, 47.6, 370000000, ["MENA"]),
    "southeast asia": GeoLocation("Southeast Asia", LocationType.REGION, None, 7.0, 115.0, 660000000, ["ASEAN"]),
}


class LocationExtractor:
    """
    Extract geographic locations from text.
    """
    
    @classmethod
    def extract_locations(cls, text: str) -> List[GeoLocation]:
        """Extract all locations from text"""
        text_lower = text.lower()
        locations = []
        found_names = set()
        
        # Check all databases
        for db in [COUNTRY_DATABASE, CITY_DATABASE, US_STATE_DATABASE, REGION_DATABASE]:
            for name, location in db.items():
                # Check main name
                if name in text_lower and name not in found_names:
                    locations.append(location)
                    found_names.add(name)
                    continue
                
                # Check aliases
                for alias in location.aliases:
                    if alias.lower() in text_lower and name not in found_names:
                        locations.append(location)
                        found_names.add(name)
                        break
        
        # Extract coordinates if present
        coord_pattern = r'(-?\d{1,3}\.?\d*)[°\s]+([NS])?[,\s]+(-?\d{1,3}\.?\d*)[°\s]+([EW])?'
        for match in re.finditer(coord_pattern, text):
            try:
                lat = float(match.group(1))
                lon = float(match.group(3))
                
                if match.group(2) == 'S':
                    lat = -lat
                if match.group(4) == 'W':
                    lon = -lon
                
                locations.append(GeoLocation(
                    f"Coordinates ({lat}, {lon})",
                    LocationType.COORDINATES,
                    None,
                    lat,
                    lon
                ))
            except ValueError:
                pass
        
        return locations
    
    @classmethod
    def normalize_location(cls, location_text: str) -> Optional[GeoLocation]:
        """Normalize a location string to standard form"""
        text_lower = location_text.lower().strip()
        
        # Check all databases
        for db in [COUNTRY_DATABASE, CITY_DATABASE, US_STATE_DATABASE, REGION_DATABASE]:
            if text_lower in db:
                return db[text_lower]
            
            # Check aliases
            for name, location in db.items():
                if text_lower in [a.lower() for a in location.aliases]:
                    return location
        
        return None


class DistanceCalculator:
    """
    Calculate geographic distances using Haversine formula.
    """
    
    EARTH_RADIUS_KM = 6371.0
    EARTH_RADIUS_MILES = 3958.8
    
    @classmethod
    def haversine_distance(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
        unit: str = "km"
    ) -> float:
        """
        Calculate distance between two points using Haversine formula.
        """
        # Convert to radians
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        # Haversine formula
        a = math.sin(delta_lat / 2) ** 2 + \
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        radius = cls.EARTH_RADIUS_MILES if unit == "miles" else cls.EARTH_RADIUS_KM
        return radius * c
    
    @classmethod
    def distance_between_locations(
        cls,
        loc1: GeoLocation,
        loc2: GeoLocation,
        unit: str = "km"
    ) -> Optional[float]:
        """Calculate distance between two locations"""
        if loc1.latitude is None or loc1.longitude is None:
            return None
        if loc2.latitude is None or loc2.longitude is None:
            return None
        
        return cls.haversine_distance(
            loc1.latitude, loc1.longitude,
            loc2.latitude, loc2.longitude,
            unit
        )


class GeospatialReasoningEngine:
    """
    Engine for geospatial reasoning in fact-checking.
    
    Handles:
    - Location-dependent facts (laws, customs, statistics)
    - Geographic claim validation
    - Regional context awareness
    - Jurisdictional reasoning
    """
    
    # Location-sensitive claim patterns
    LOCATION_SENSITIVE_PATTERNS = [
        (r'\blegal\b', "legal_jurisdiction"),
        (r'\blaw\b', "legal_jurisdiction"),
        (r'\billegal\b', "legal_jurisdiction"),
        (r'\bmarijuana|cannabis\b', "legal_jurisdiction"),
        (r'\bdrinking\s+age\b', "legal_jurisdiction"),
        (r'\bspeed\s+limit\b', "legal_jurisdiction"),
        (r'\bminimum\s+wage\b', "economic"),
        (r'\btax\s+rate\b', "economic"),
        (r'\btemperature|weather|climate\b', "climate"),
        (r'\bpopulation\b', "demographic"),
        (r'\bcurrency\b', "economic"),
        (r'\blanguage\b', "cultural"),
        (r'\breligion\b', "cultural"),
        (r'\bholiday\b', "cultural"),
        (r'\belection|vote\b', "political"),
    ]
    
    # Regional fact variations
    REGIONAL_FACTS: Dict[str, Dict[str, str]] = {
        "drinking_age": {
            "united states": "21",
            "united kingdom": "18",
            "germany": "16 (beer/wine), 18 (spirits)",
            "japan": "20",
            "canada": "18-19 (varies by province)",
        },
        "driving_side": {
            "united states": "right",
            "united kingdom": "left",
            "japan": "left",
            "australia": "left",
            "india": "left",
            "germany": "right",
        },
        "measurement_system": {
            "united states": "imperial",
            "united kingdom": "mixed (imperial/metric)",
            "canada": "metric",
            "australia": "metric",
        },
    }
    
    def __init__(self):
        self.extractor = LocationExtractor()
        self.calculator = DistanceCalculator()
    
    def analyze_claim(self, claim: str) -> GeoContext:
        """Analyze geographic aspects of a claim"""
        context = GeoContext()
        
        # Extract locations
        context.locations = self.extractor.extract_locations(claim)
        
        # Check if location-sensitive
        context.is_location_sensitive = self._is_location_sensitive(claim)
        
        # Determine jurisdiction if applicable
        if context.is_location_sensitive and context.locations:
            context.jurisdiction = self._determine_jurisdiction(context.locations)
        
        # Find regional variations
        context.regional_variations = self._find_regional_variations(claim)
        
        return context
    
    def _is_location_sensitive(self, claim: str) -> bool:
        """Check if claim is location-sensitive"""
        claim_lower = claim.lower()
        
        for pattern, _ in self.LOCATION_SENSITIVE_PATTERNS:
            if re.search(pattern, claim_lower):
                return True
        
        return False
    
    def _determine_jurisdiction(self, locations: List[GeoLocation]) -> str:
        """Determine the relevant jurisdiction"""
        # Prefer most specific location
        for loc_type in [LocationType.CITY, LocationType.STATE_PROVINCE, LocationType.COUNTRY]:
            for loc in locations:
                if loc.location_type == loc_type:
                    if loc.country:
                        return f"{loc.name}, {loc.country}"
                    return loc.name
        
        if locations:
            return locations[0].name
        
        return "Unknown"
    
    def _find_regional_variations(self, claim: str) -> List[str]:
        """Find regional variations that might affect the claim"""
        variations = []
        claim_lower = claim.lower()
        
        # Check for regional fact topics
        if "drinking age" in claim_lower:
            variations.append("Drinking age varies by country/state")
        if "legal" in claim_lower or "illegal" in claim_lower:
            variations.append("Legality varies by jurisdiction")
        if "speed limit" in claim_lower:
            variations.append("Speed limits vary by location and road type")
        if re.search(r'\b(tax|wage|price)\b', claim_lower):
            variations.append("Economic figures vary by region")
        
        return variations
    
    def validate_geographic_claim(
        self,
        claim: str,
        claimed_location: str,
        claimed_value: str
    ) -> Dict:
        """
        Validate a geographic claim.
        
        Example: "The drinking age in Germany is 18" 
        -> validate claimed_location="Germany", claimed_value="18"
        """
        result = {
            "claim": claim,
            "location": claimed_location,
            "claimed_value": claimed_value,
            "is_valid": None,
            "actual_value": None,
            "explanation": "",
            "regional_context": []
        }
        
        # Normalize location
        normalized_loc = self.extractor.normalize_location(claimed_location)
        
        if not normalized_loc:
            result["explanation"] = f"Could not identify location: {claimed_location}"
            return result
        
        # Check if we have data for this topic and location
        topic = self._identify_topic(claim)
        
        if topic and topic in self.REGIONAL_FACTS:
            loc_key = normalized_loc.name.lower()
            if loc_key in self.REGIONAL_FACTS[topic]:
                actual = self.REGIONAL_FACTS[topic][loc_key]
                result["actual_value"] = actual
                result["is_valid"] = claimed_value.lower() in actual.lower()
                result["explanation"] = f"For {normalized_loc.name}, the {topic.replace('_', ' ')} is: {actual}"
            else:
                result["explanation"] = f"No data available for {topic.replace('_', ' ')} in {normalized_loc.name}"
        
        # Add context for all known regions
        if topic and topic in self.REGIONAL_FACTS:
            for region, value in self.REGIONAL_FACTS[topic].items():
                result["regional_context"].append(f"{region.title()}: {value}")
        
        return result
    
    def _identify_topic(self, claim: str) -> Optional[str]:
        """Identify the topic of a geographic claim"""
        claim_lower = claim.lower()
        
        if "drinking age" in claim_lower:
            return "drinking_age"
        if "drive" in claim_lower and ("left" in claim_lower or "right" in claim_lower):
            return "driving_side"
        if "metric" in claim_lower or "imperial" in claim_lower or "measurement" in claim_lower:
            return "measurement_system"
        
        return None
    
    def calculate_distance_claim(
        self,
        claim: str,
        location1_name: str,
        location2_name: str,
        claimed_distance: float,
        unit: str = "km",
        tolerance: float = 0.1
    ) -> Dict:
        """
        Validate a distance claim between two locations.
        
        tolerance: Acceptable error margin (0.1 = 10%)
        """
        result = {
            "claim": claim,
            "location1": location1_name,
            "location2": location2_name,
            "claimed_distance": claimed_distance,
            "actual_distance": None,
            "unit": unit,
            "is_valid": None,
            "error_margin": None,
            "explanation": ""
        }
        
        # Normalize locations
        loc1 = self.extractor.normalize_location(location1_name)
        loc2 = self.extractor.normalize_location(location2_name)
        
        if not loc1:
            result["explanation"] = f"Could not identify location: {location1_name}"
            return result
        
        if not loc2:
            result["explanation"] = f"Could not identify location: {location2_name}"
            return result
        
        # Calculate actual distance
        actual = self.calculator.distance_between_locations(loc1, loc2, unit)
        
        if actual is None:
            result["explanation"] = "Could not calculate distance (missing coordinates)"
            return result
        
        result["actual_distance"] = round(actual, 1)
        
        # Check if claimed distance is within tolerance
        error = abs(claimed_distance - actual) / actual if actual > 0 else 0
        result["error_margin"] = round(error * 100, 1)
        result["is_valid"] = error <= tolerance
        
        if result["is_valid"]:
            result["explanation"] = f"Distance claim is accurate (within {tolerance * 100}% tolerance)"
        else:
            result["explanation"] = f"Distance claim is off by {result['error_margin']}%. Actual: {result['actual_distance']} {unit}"
        
        return result
    
    def get_location_context(self, location_name: str) -> Dict:
        """Get comprehensive context for a location"""
        location = self.extractor.normalize_location(location_name)
        
        if not location:
            return {"error": f"Unknown location: {location_name}"}
        
        context = {
            "name": location.name,
            "type": location.location_type.value,
            "country": location.country,
            "coordinates": {
                "latitude": location.latitude,
                "longitude": location.longitude
            },
            "population": location.population,
            "aliases": location.aliases,
            "regional_facts": {}
        }
        
        # Add regional facts if available
        loc_key = location.name.lower()
        for topic, regions in self.REGIONAL_FACTS.items():
            if loc_key in regions:
                context["regional_facts"][topic] = regions[loc_key]
        
        return context
    
    def generate_geo_search_queries(self, claim: str) -> List[str]:
        """Generate location-aware search queries"""
        context = self.analyze_claim(claim)
        queries = [claim]
        
        for location in context.locations:
            # Add location-specific queries
            queries.append(f"{claim} {location.name}")
            
            if location.country and location.country != location.name:
                queries.append(f"{claim} {location.country}")
        
        if context.is_location_sensitive:
            queries.append(f"{claim} by country")
            queries.append(f"{claim} regional differences")
        
        return list(set(queries))


__all__ = [
    'GeospatialReasoningEngine', 'LocationExtractor', 'DistanceCalculator',
    'GeoLocation', 'GeoContext', 'LocationType',
    'COUNTRY_DATABASE', 'CITY_DATABASE', 'US_STATE_DATABASE', 'REGION_DATABASE'
]
