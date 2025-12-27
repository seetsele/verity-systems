"""
Verity Additional Fact-Check Providers
======================================
More integrations with fact-checking APIs and services.

Includes:
- Google Fact Check Tools API
- Snopes API (scraping)
- PolitiFact API (scraping)
- ClaimBuster API
- Reuters Fact Check
- AFP Fact Check
- Lead Stories
- MediaBiasFact Check
"""

import aiohttp
import asyncio
import re
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass
import hashlib
import json


@dataclass
class FactCheckResult:
    claim: str
    rating: str
    source: str
    url: str
    date_checked: Optional[datetime]
    explanation: str
    confidence: float


class GoogleFactCheckAPI:
    """
    Google Fact Check Tools API
    Free tier: 10,000 queries/day
    https://developers.google.com/fact-check/tools/api
    """
    
    BASE_URL = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def search(self, query: str, session: aiohttp.ClientSession, language: str = "en") -> List[FactCheckResult]:
        """Search Google's fact-check database"""
        params = {
            "query": query,
            "languageCode": language,
            "key": self.api_key
        }
        
        try:
            async with session.get(self.BASE_URL, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_results(data)
        except Exception as e:
            print(f"Google Fact Check API error: {e}")
        
        return []
    
    def _parse_results(self, data: Dict) -> List[FactCheckResult]:
        """Parse Google Fact Check API response"""
        results = []
        
        for claim in data.get("claims", []):
            claim_text = claim.get("text", "")
            
            for review in claim.get("claimReview", []):
                results.append(FactCheckResult(
                    claim=claim_text,
                    rating=review.get("textualRating", "Unknown"),
                    source=review.get("publisher", {}).get("name", "Unknown"),
                    url=review.get("url", ""),
                    date_checked=self._parse_date(review.get("reviewDate")),
                    explanation=review.get("title", ""),
                    confidence=0.85  # Google FC sources are reliable
                ))
        
        return results
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None


class ClaimBusterAPI:
    """
    ClaimBuster API - Claim detection and scoring
    Free for research use
    https://idir.uta.edu/claimbuster/
    """
    
    BASE_URL = "https://idir.uta.edu/claimbuster/api/v2"
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
    
    async def score_claim(self, claim: str, session: aiohttp.ClientSession) -> Dict:
        """
        Score how check-worthy a claim is (0-1)
        Higher score = more important to fact-check
        """
        url = f"{self.BASE_URL}/score/text/{claim}"
        headers = {}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        
        try:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    results = data.get("results", [])
                    if results:
                        return {
                            "claim": claim,
                            "score": results[0].get("score", 0),
                            "check_worthy": results[0].get("score", 0) > 0.5
                        }
        except Exception as e:
            print(f"ClaimBuster API error: {e}")
        
        return {"claim": claim, "score": 0.5, "check_worthy": False}
    
    async def detect_claims(self, text: str, session: aiohttp.ClientSession) -> List[Dict]:
        """
        Extract check-worthy claims from longer text
        """
        url = f"{self.BASE_URL}/score/text/"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["x-api-key"] = self.api_key
        
        try:
            async with session.post(url, json={"input_text": text}, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    claims = []
                    for result in data.get("results", []):
                        if result.get("score", 0) > 0.5:
                            claims.append({
                                "text": result.get("text", ""),
                                "score": result.get("score", 0)
                            })
                    return claims
        except Exception as e:
            print(f"ClaimBuster detect error: {e}")
        
        return []


class LeadStoriesAPI:
    """
    Lead Stories Trendolizer - Fact-checking trending claims
    https://leadstories.com/
    """
    
    BASE_URL = "https://leadstories.com"
    SEARCH_URL = "https://leadstories.com/page-data/search-results/page-data.json"
    
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[FactCheckResult]:
        """Search Lead Stories fact-checks"""
        # Lead Stories doesn't have a public API, so we scrape
        search_url = f"{self.BASE_URL}/?s={query.replace(' ', '+')}"
        
        try:
            async with session.get(search_url) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_search_results(html, query)
        except Exception as e:
            print(f"Lead Stories error: {e}")
        
        return []
    
    def _parse_search_results(self, html: str, query: str) -> List[FactCheckResult]:
        """Parse Lead Stories search results"""
        results = []
        
        # Simple regex parsing for article titles and URLs
        article_pattern = r'<a href="(https://leadstories\.com/[^"]+)"[^>]*>([^<]+)</a>'
        matches = re.findall(article_pattern, html)
        
        for url, title in matches[:5]:  # Limit to 5 results
            if 'hoax-alert' in url or 'fact-check' in url:
                rating = "Hoax Alert" if "hoax" in url.lower() else "Fact Check"
                results.append(FactCheckResult(
                    claim=query,
                    rating=rating,
                    source="Lead Stories",
                    url=url,
                    date_checked=datetime.now(),
                    explanation=title,
                    confidence=0.8
                ))
        
        return results


class SnopesProvider:
    """
    Snopes fact-checking (scraping approach)
    https://www.snopes.com/
    """
    
    BASE_URL = "https://www.snopes.com"
    
    RATING_MAP = {
        "true": "True",
        "mostly true": "Mostly True",
        "mixture": "Mixture",
        "mostly false": "Mostly False",
        "false": "False",
        "unproven": "Unproven",
        "outdated": "Outdated",
        "miscaptioned": "Miscaptioned",
        "legend": "Legend",
        "scam": "Scam"
    }
    
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[FactCheckResult]:
        """Search Snopes for fact-checks"""
        search_url = f"{self.BASE_URL}/?s={query.replace(' ', '+')}"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VerityBot/1.0)"
            }
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_results(html, query)
        except Exception as e:
            print(f"Snopes search error: {e}")
        
        return []
    
    def _parse_results(self, html: str, query: str) -> List[FactCheckResult]:
        """Parse Snopes search results"""
        results = []
        
        # Look for fact-check cards
        # Pattern for Snopes article links
        article_pattern = r'<a[^>]*href="(https://www\.snopes\.com/fact-check/[^"]+)"[^>]*>(.*?)</a>'
        
        matches = re.findall(article_pattern, html, re.DOTALL)
        
        for url, title_html in matches[:5]:
            # Clean title
            title = re.sub(r'<[^>]+>', '', title_html).strip()
            
            # Try to extract rating from surrounding context
            rating = "Unknown"
            for snopes_rating, display_rating in self.RATING_MAP.items():
                if snopes_rating in html.lower():
                    rating = display_rating
                    break
            
            results.append(FactCheckResult(
                claim=query,
                rating=rating,
                source="Snopes",
                url=url,
                date_checked=datetime.now(),
                explanation=title[:200],
                confidence=0.88
            ))
        
        return results


class PolitiFactProvider:
    """
    PolitiFact fact-checking
    https://www.politifact.com/
    """
    
    BASE_URL = "https://www.politifact.com"
    
    TRUTH_O_METER = {
        "true": ("True", 1.0),
        "mostly-true": ("Mostly True", 0.8),
        "half-true": ("Half True", 0.5),
        "barely-true": ("Mostly False", 0.3),
        "false": ("False", 0.1),
        "pants-fire": ("Pants on Fire", 0.0)
    }
    
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[FactCheckResult]:
        """Search PolitiFact"""
        search_url = f"{self.BASE_URL}/search/?q={query.replace(' ', '+')}"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VerityBot/1.0)"
            }
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_results(html, query)
        except Exception as e:
            print(f"PolitiFact search error: {e}")
        
        return []
    
    def _parse_results(self, html: str, query: str) -> List[FactCheckResult]:
        """Parse PolitiFact search results"""
        results = []
        
        # Pattern for fact-check links with ratings
        article_pattern = r'href="(/factchecks/\d+/[^"]+)".*?<img[^>]*alt="([^"]*)"'
        
        matches = re.findall(article_pattern, html, re.DOTALL)
        
        for path, rating_img in matches[:5]:
            url = f"{self.BASE_URL}{path}"
            
            # Extract rating from image alt text
            rating = "Unknown"
            confidence = 0.5
            
            for meter_key, (display, conf) in self.TRUTH_O_METER.items():
                if meter_key in rating_img.lower():
                    rating = display
                    confidence = conf
                    break
            
            results.append(FactCheckResult(
                claim=query,
                rating=rating,
                source="PolitiFact",
                url=url,
                date_checked=datetime.now(),
                explanation="",
                confidence=0.87
            ))
        
        return results


class ReutersFactCheck:
    """
    Reuters Fact Check
    https://www.reuters.com/fact-check/
    """
    
    BASE_URL = "https://www.reuters.com"
    FACT_CHECK_URL = "https://www.reuters.com/fact-check/"
    
    VERDICTS = {
        "false": "False",
        "partly false": "Partly False",
        "misleading": "Misleading",
        "missing context": "Missing Context",
        "altered": "Altered",
        "true": "True"
    }
    
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[FactCheckResult]:
        """Search Reuters Fact Check"""
        search_url = f"{self.BASE_URL}/site-search/?query={query.replace(' ', '+')}&section=fact-check"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VerityBot/1.0)"
            }
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_results(html, query)
        except Exception as e:
            print(f"Reuters Fact Check error: {e}")
        
        return []
    
    def _parse_results(self, html: str, query: str) -> List[FactCheckResult]:
        """Parse Reuters fact-check results"""
        results = []
        
        # Reuters uses JSON-LD for structured data
        json_ld_pattern = r'<script type="application/ld\+json">(.*?)</script>'
        matches = re.findall(json_ld_pattern, html, re.DOTALL)
        
        for json_str in matches:
            try:
                data = json.loads(json_str)
                if isinstance(data, list):
                    for item in data:
                        if item.get("@type") == "ClaimReview":
                            results.append(FactCheckResult(
                                claim=item.get("claimReviewed", query),
                                rating=item.get("reviewRating", {}).get("alternateName", "Unknown"),
                                source="Reuters Fact Check",
                                url=item.get("url", ""),
                                date_checked=self._parse_date(item.get("datePublished")),
                                explanation=item.get("reviewBody", "")[:300],
                                confidence=0.92
                            ))
            except:
                continue
        
        return results
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            return None


class AFPFactCheck:
    """
    AFP Fact Check
    https://factcheck.afp.com/
    """
    
    BASE_URL = "https://factcheck.afp.com"
    
    async def search(self, query: str, session: aiohttp.ClientSession) -> List[FactCheckResult]:
        """Search AFP Fact Check"""
        search_url = f"{self.BASE_URL}/search?search_api_fulltext={query.replace(' ', '+')}"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VerityBot/1.0)"
            }
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_results(html, query)
        except Exception as e:
            print(f"AFP Fact Check error: {e}")
        
        return []
    
    def _parse_results(self, html: str, query: str) -> List[FactCheckResult]:
        """Parse AFP fact-check results"""
        results = []
        
        # Look for article links
        article_pattern = r'<a[^>]*href="(/[^"]*)"[^>]*class="[^"]*card[^"]*"[^>]*>(.*?)</a>'
        
        matches = re.findall(article_pattern, html, re.DOTALL)
        
        for path, content in matches[:5]:
            if '/doc.' in path or '/list/' in path:
                continue
            
            url = f"{self.BASE_URL}{path}"
            title = re.sub(r'<[^>]+>', '', content).strip()[:200]
            
            results.append(FactCheckResult(
                claim=query,
                rating="Fact Check",
                source="AFP Fact Check",
                url=url,
                date_checked=datetime.now(),
                explanation=title,
                confidence=0.90
            ))
        
        return results


class MediaBiasFactCheck:
    """
    Media Bias/Fact Check - Source credibility checker
    https://mediabiasfactcheck.com/
    """
    
    BASE_URL = "https://mediabiasfactcheck.com"
    
    BIAS_RATINGS = {
        "left": "Left Bias",
        "left-center": "Left-Center Bias",
        "least-biased": "Least Biased",
        "right-center": "Right-Center Bias",
        "right": "Right Bias",
        "questionable": "Questionable Source",
        "conspiracy-pseudoscience": "Conspiracy/Pseudoscience",
        "satire": "Satire"
    }
    
    FACTUAL_RATINGS = {
        "very-high": "Very High",
        "high": "High",
        "mostly-factual": "Mostly Factual",
        "mixed": "Mixed",
        "low": "Low",
        "very-low": "Very Low"
    }
    
    async def check_source(self, source_domain: str, session: aiohttp.ClientSession) -> Optional[Dict]:
        """Check a source's bias and factual ratings"""
        # Normalize domain
        domain = source_domain.lower().replace("www.", "").replace(".com", "").replace(".org", "")
        
        search_url = f"{self.BASE_URL}/?s={domain}"
        
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; VerityBot/1.0)"
            }
            async with session.get(search_url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    return self._parse_source_rating(html, source_domain)
        except Exception as e:
            print(f"MBFC error: {e}")
        
        return None
    
    def _parse_source_rating(self, html: str, domain: str) -> Optional[Dict]:
        """Parse MBFC source rating"""
        
        # Look for bias rating
        bias = "Unknown"
        for key, value in self.BIAS_RATINGS.items():
            if key in html.lower():
                bias = value
                break
        
        # Look for factual reporting
        factual = "Unknown"
        for key, value in self.FACTUAL_RATINGS.items():
            if f"factual reporting: {key}" in html.lower():
                factual = value
                break
        
        if bias != "Unknown" or factual != "Unknown":
            return {
                "source": domain,
                "bias_rating": bias,
                "factual_rating": factual,
                "checked_by": "Media Bias/Fact Check"
            }
        
        return None


class UnifiedFactChecker:
    """
    Unified interface to query all fact-checking services
    """
    
    def __init__(self, google_api_key: str = None, claimbuster_key: str = None):
        self.google_fc = GoogleFactCheckAPI(google_api_key) if google_api_key else None
        self.claimbuster = ClaimBusterAPI(claimbuster_key)
        self.lead_stories = LeadStoriesAPI()
        self.snopes = SnopesProvider()
        self.politifact = PolitiFactProvider()
        self.reuters = ReutersFactCheck()
        self.afp = AFPFactCheck()
        self.mbfc = MediaBiasFactCheck()
    
    async def check_all(self, claim: str, session: aiohttp.ClientSession = None) -> Dict:
        """
        Query all fact-checking services for a claim
        Returns aggregated results
        """
        if session is None:
            async with aiohttp.ClientSession() as session:
                return await self._check_all_internal(claim, session)
        else:
            return await self._check_all_internal(claim, session)
    
    async def _check_all_internal(self, claim: str, session: aiohttp.ClientSession) -> Dict:
        """Internal method to check all sources"""
        tasks = []
        
        # Add all searches
        if self.google_fc:
            tasks.append(("Google Fact Check", self.google_fc.search(claim, session)))
        
        tasks.append(("ClaimBuster", self.claimbuster.score_claim(claim, session)))
        tasks.append(("Lead Stories", self.lead_stories.search(claim, session)))
        tasks.append(("Snopes", self.snopes.search(claim, session)))
        tasks.append(("PolitiFact", self.politifact.search(claim, session)))
        tasks.append(("Reuters", self.reuters.search(claim, session)))
        tasks.append(("AFP", self.afp.search(claim, session)))
        
        # Execute all in parallel
        results = {}
        all_tasks = [task for _, task in tasks]
        task_names = [name for name, _ in tasks]
        
        completed = await asyncio.gather(*all_tasks, return_exceptions=True)
        
        for name, result in zip(task_names, completed):
            if isinstance(result, Exception):
                results[name] = {"error": str(result)}
            else:
                results[name] = result
        
        # Aggregate verdict
        all_verdicts = []
        for name, data in results.items():
            if isinstance(data, list):
                for fc_result in data:
                    if isinstance(fc_result, FactCheckResult):
                        all_verdicts.append({
                            "source": fc_result.source,
                            "rating": fc_result.rating,
                            "confidence": fc_result.confidence,
                            "url": fc_result.url
                        })
        
        return {
            "claim": claim,
            "fact_checks_found": len(all_verdicts),
            "verdicts": all_verdicts,
            "raw_results": results,
            "consensus": self._calculate_consensus(all_verdicts)
        }
    
    def _calculate_consensus(self, verdicts: List[Dict]) -> Dict:
        """Calculate consensus from multiple fact-checks"""
        if not verdicts:
            return {"verdict": "No fact-checks found", "confidence": 0.0}
        
        # Count ratings
        true_count = sum(1 for v in verdicts if v["rating"].lower() in ["true", "mostly true", "correct"])
        false_count = sum(1 for v in verdicts if v["rating"].lower() in ["false", "pants on fire", "incorrect", "hoax"])
        mixed_count = sum(1 for v in verdicts if v["rating"].lower() in ["mixture", "half true", "partly false", "misleading"])
        
        total = len(verdicts)
        
        if true_count > total / 2:
            verdict = "Likely True"
            confidence = true_count / total
        elif false_count > total / 2:
            verdict = "Likely False"
            confidence = false_count / total
        elif mixed_count > 0:
            verdict = "Mixed/Disputed"
            confidence = mixed_count / total
        else:
            verdict = "Inconclusive"
            confidence = 0.5
        
        return {
            "verdict": verdict,
            "confidence": confidence,
            "true_votes": true_count,
            "false_votes": false_count,
            "mixed_votes": mixed_count,
            "total_checks": total
        }


__all__ = [
    'GoogleFactCheckAPI', 'ClaimBusterAPI', 'LeadStoriesAPI',
    'SnopesProvider', 'PolitiFactProvider', 'ReutersFactCheck',
    'AFPFactCheck', 'MediaBiasFactCheck', 'UnifiedFactChecker',
    'FactCheckResult'
]
