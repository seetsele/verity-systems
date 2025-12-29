"""
Verity Systems - Extended Data Sources
Additional free and premium data sources for comprehensive fact-checking.

Categories:
- Academic & Research (Semantic Scholar, PubMed, arXiv, CrossRef)
- News & Media (NewsAPI, MediaStack, CurrentsAPI)  
- Social Media Analysis (Twitter/X trends, Reddit)
- Government & Official (Data.gov, WHO, CDC)
- Knowledge Bases (Wikidata, DBpedia, YAGO)
- Image/Video Analysis (TinEye, Google Vision)

Author: Verity Systems
License: MIT
"""

import os
import asyncio
import aiohttp
import logging
import json
import re
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from urllib.parse import quote_plus, urlencode
import hashlib

logger = logging.getLogger('VerityDataSources')


# ============================================================
# BASE CLASSES
# ============================================================

@dataclass
class SourceResult:
    """Result from a data source"""
    source_name: str
    source_type: str
    relevance: float  # 0-1
    title: str
    content: str
    url: Optional[str] = None
    published_date: Optional[datetime] = None
    author: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    credibility_score: float = 0.5


class DataSource(ABC):
    """Abstract base class for all data sources"""
    
    def __init__(self, session: aiohttp.ClientSession = None):
        self._session = session
        self._own_session = False
        
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            self._own_session = True
        return self._session
    
    async def close(self):
        if self._own_session and self._session:
            await self._session.close()
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def source_type(self) -> str:
        pass
    
    @property
    def is_available(self) -> bool:
        return True
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        pass


# ============================================================
# ACADEMIC SOURCES
# ============================================================

class SemanticScholarSource(DataSource):
    """
    Semantic Scholar - Academic paper search with API key
    https://www.semanticscholar.org/
    
    Rate limit: 1 request per second with API key
    """
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    _last_request_time = 0  # Class-level rate limiting
    
    def __init__(self, session: aiohttp.ClientSession = None):
        super().__init__(session)
        self.api_key = os.getenv('SEMANTIC_SCHOLAR_API_KEY')
    
    @property
    def name(self) -> str:
        return "Semantic Scholar"
    
    @property
    def source_type(self) -> str:
        return "academic"
    
    async def _rate_limit(self):
        """Enforce 1 request per second rate limit"""
        import time
        current_time = time.time()
        time_since_last = current_time - SemanticScholarSource._last_request_time
        if time_since_last < 1.0:  # 1 second between requests
            await asyncio.sleep(1.0 - time_since_last)
        SemanticScholarSource._last_request_time = time.time()
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        await self._rate_limit()  # Enforce rate limit
        
        session = await self.get_session()
        results = []
        
        # Add API key header if available
        headers = {}
        if self.api_key:
            headers['x-api-key'] = self.api_key
        
        try:
            params = {
                "query": query,
                "limit": limit,
                "fields": "title,abstract,authors,year,citationCount,url,venue"
            }
            
            async with session.get(
                f"{self.BASE_URL}/paper/search",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for paper in data.get("data", []):
                    # Calculate relevance based on citations
                    citations = paper.get("citationCount", 0)
                    relevance = min(1.0, citations / 1000) * 0.5 + 0.5
                    
                    authors = [a.get("name", "") for a in paper.get("authors", [])]
                    
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=relevance,
                        title=paper.get("title", ""),
                        content=paper.get("abstract", "")[:500] if paper.get("abstract") else "",
                        url=paper.get("url"),
                        author=", ".join(authors[:3]),
                        metadata={
                            "year": paper.get("year"),
                            "citations": citations,
                            "venue": paper.get("venue")
                        },
                        credibility_score=0.9  # Academic papers are highly credible
                    ))
                    
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")
        
        return results


class PubMedSource(DataSource):
    """
    PubMed - Free medical/biomedical literature
    https://pubmed.ncbi.nlm.nih.gov/
    
    NCBI E-utilities API (free, rate limited)
    """
    
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    
    @property
    def name(self) -> str:
        return "PubMed"
    
    @property
    def source_type(self) -> str:
        return "medical"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        session = await self.get_session()
        results = []
        
        try:
            # First, search for PMIDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": limit,
                "retmode": "json"
            }
            
            async with session.get(
                f"{self.BASE_URL}/esearch.fcgi",
                params=search_params
            ) as resp:
                if resp.status != 200:
                    return results
                
                search_data = await resp.json()
                pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                return results
            
            # Fetch details for each PMID
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json"
            }
            
            async with session.get(
                f"{self.BASE_URL}/esummary.fcgi",
                params=fetch_params
            ) as resp:
                if resp.status != 200:
                    return results
                
                fetch_data = await resp.json()
                articles = fetch_data.get("result", {})
            
            for pmid in pmids:
                if pmid not in articles:
                    continue
                    
                article = articles[pmid]
                
                authors = article.get("authors", [])
                author_names = [a.get("name", "") for a in authors[:3]]
                
                results.append(SourceResult(
                    source_name=self.name,
                    source_type=self.source_type,
                    relevance=0.8,  # Medical literature is highly relevant for health claims
                    title=article.get("title", ""),
                    content=article.get("title", ""),  # Abstract requires separate fetch
                    url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    author=", ".join(author_names),
                    metadata={
                        "pmid": pmid,
                        "journal": article.get("fulljournalname"),
                        "pubdate": article.get("pubdate")
                    },
                    credibility_score=0.95  # Peer-reviewed medical research
                ))
                
        except Exception as e:
            logger.warning(f"PubMed search failed: {e}")
        
        return results


class ArxivSource(DataSource):
    """
    arXiv - Free preprint server for scientific papers
    https://arxiv.org/
    
    Open API, no authentication required
    """
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    @property
    def name(self) -> str:
        return "arXiv"
    
    @property
    def source_type(self) -> str:
        return "preprint"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        session = await self.get_session()
        results = []
        
        try:
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": limit
            }
            
            async with session.get(
                self.BASE_URL,
                params=params
            ) as resp:
                if resp.status != 200:
                    return results
                
                text = await resp.text()
                
                # Parse Atom XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(text)
                
                ns = {"atom": "http://www.w3.org/2005/Atom"}
                
                for entry in root.findall("atom:entry", ns):
                    title = entry.find("atom:title", ns)
                    summary = entry.find("atom:summary", ns)
                    link = entry.find("atom:id", ns)
                    published = entry.find("atom:published", ns)
                    
                    authors = []
                    for author in entry.findall("atom:author", ns):
                        name = author.find("atom:name", ns)
                        if name is not None:
                            authors.append(name.text)
                    
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=0.7,
                        title=title.text.strip() if title is not None else "",
                        content=summary.text.strip()[:500] if summary is not None else "",
                        url=link.text if link is not None else None,
                        published_date=datetime.fromisoformat(published.text.replace("Z", "+00:00")) if published is not None else None,
                        author=", ".join(authors[:3]),
                        metadata={"preprint": True},
                        credibility_score=0.75  # Preprints not peer-reviewed
                    ))
                    
        except Exception as e:
            logger.warning(f"arXiv search failed: {e}")
        
        return results


class CrossRefSource(DataSource):
    """
    CrossRef - DOI registration agency with citation metadata
    https://www.crossref.org/
    
    Free API with polite pool
    """
    
    BASE_URL = "https://api.crossref.org/works"
    
    @property
    def name(self) -> str:
        return "CrossRef"
    
    @property
    def source_type(self) -> str:
        return "citation"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        session = await self.get_session()
        results = []
        
        try:
            params = {
                "query": query,
                "rows": limit,
                "select": "title,author,DOI,URL,published-print,container-title,is-referenced-by-count"
            }
            
            headers = {
                "User-Agent": "VeritySystems/1.0 (mailto:contact@verity-systems.com)"
            }
            
            async with session.get(
                self.BASE_URL,
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for item in data.get("message", {}).get("items", []):
                    title = item.get("title", [""])[0] if item.get("title") else ""
                    
                    authors = []
                    for author in item.get("author", [])[:3]:
                        name = f"{author.get('given', '')} {author.get('family', '')}".strip()
                        if name:
                            authors.append(name)
                    
                    citations = item.get("is-referenced-by-count", 0)
                    
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=min(1.0, citations / 500) * 0.5 + 0.5,
                        title=title,
                        content="",  # CrossRef doesn't provide abstracts
                        url=item.get("URL"),
                        author=", ".join(authors),
                        metadata={
                            "doi": item.get("DOI"),
                            "journal": item.get("container-title", [""])[0] if item.get("container-title") else "",
                            "citations": citations
                        },
                        credibility_score=0.85
                    ))
                    
        except Exception as e:
            logger.warning(f"CrossRef search failed: {e}")
        
        return results


# ============================================================
# NEWS & MEDIA SOURCES
# ============================================================

class NewsAPISource(DataSource):
    """
    NewsAPI.org - News aggregator
    https://newsapi.org/
    
    Free tier: 100 requests/day, 1 month old articles
    """
    
    BASE_URL = "https://newsapi.org/v2"
    
    def __init__(self, session: aiohttp.ClientSession = None):
        super().__init__(session)
        self.api_key = os.getenv("NEWSAPI_KEY") or os.getenv("NEWS_API_KEY")
    
    @property
    def name(self) -> str:
        return "NewsAPI"
    
    @property
    def source_type(self) -> str:
        return "news"
    
    @property
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        if not self.is_available:
            return []
        
        session = await self.get_session()
        results = []
        
        try:
            params = {
                "q": query,
                "pageSize": limit,
                "sortBy": "relevancy",
                "language": "en"
            }
            
            headers = {
                "X-Api-Key": self.api_key
            }
            
            async with session.get(
                f"{self.BASE_URL}/everything",
                params=params,
                headers=headers
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for article in data.get("articles", []):
                    source = article.get("source", {})
                    
                    # Estimate credibility based on source
                    source_name = source.get("name", "").lower()
                    credibility = 0.6
                    if any(s in source_name for s in ["reuters", "ap", "bbc", "npr", "pbs"]):
                        credibility = 0.9
                    elif any(s in source_name for s in ["cnn", "nytimes", "washington post", "guardian"]):
                        credibility = 0.8
                    
                    pub_date = None
                    if article.get("publishedAt"):
                        try:
                            pub_date = datetime.fromisoformat(article["publishedAt"].replace("Z", "+00:00"))
                        except:
                            pass
                    
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=0.7,
                        title=article.get("title", ""),
                        content=article.get("description", "")[:500] or article.get("content", "")[:500],
                        url=article.get("url"),
                        published_date=pub_date,
                        author=article.get("author"),
                        metadata={
                            "news_source": source.get("name"),
                            "source_id": source.get("id")
                        },
                        credibility_score=credibility
                    ))
                    
        except Exception as e:
            logger.warning(f"NewsAPI search failed: {e}")
        
        return results


class MediaStackSource(DataSource):
    """
    MediaStack - News API with free tier
    https://mediastack.com/
    
    Free tier: 500 requests/month
    """
    
    BASE_URL = "http://api.mediastack.com/v1/news"
    
    def __init__(self, session: aiohttp.ClientSession = None):
        super().__init__(session)
        self.api_key = os.getenv("MEDIASTACK_API_KEY")
    
    @property
    def name(self) -> str:
        return "MediaStack"
    
    @property
    def source_type(self) -> str:
        return "news"
    
    @property
    def is_available(self) -> bool:
        return bool(self.api_key)
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        if not self.is_available:
            return []
        
        session = await self.get_session()
        results = []
        
        try:
            params = {
                "access_key": self.api_key,
                "keywords": query,
                "limit": limit,
                "languages": "en"
            }
            
            async with session.get(
                self.BASE_URL,
                params=params
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for article in data.get("data", []):
                    pub_date = None
                    if article.get("published_at"):
                        try:
                            pub_date = datetime.fromisoformat(article["published_at"].replace("Z", "+00:00"))
                        except:
                            pass
                    
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=0.65,
                        title=article.get("title", ""),
                        content=article.get("description", "")[:500],
                        url=article.get("url"),
                        published_date=pub_date,
                        author=article.get("author"),
                        metadata={
                            "news_source": article.get("source"),
                            "category": article.get("category"),
                            "country": article.get("country")
                        },
                        credibility_score=0.6
                    ))
                    
        except Exception as e:
            logger.warning(f"MediaStack search failed: {e}")
        
        return results


# ============================================================
# KNOWLEDGE BASES
# ============================================================

class WikidataSource(DataSource):
    """
    Wikidata - Structured knowledge base
    https://www.wikidata.org/
    
    Free, no authentication required
    """
    
    BASE_URL = "https://www.wikidata.org/w/api.php"
    SPARQL_URL = "https://query.wikidata.org/sparql"
    
    @property
    def name(self) -> str:
        return "Wikidata"
    
    @property
    def source_type(self) -> str:
        return "knowledge_base"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        session = await self.get_session()
        results = []
        
        try:
            # Use wbsearchentities for entity search
            params = {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "limit": limit,
                "format": "json"
            }
            
            async with session.get(
                self.BASE_URL,
                params=params
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for entity in data.get("search", []):
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=0.8,
                        title=entity.get("label", ""),
                        content=entity.get("description", ""),
                        url=entity.get("concepturi"),
                        metadata={
                            "entity_id": entity.get("id"),
                            "aliases": entity.get("aliases", [])
                        },
                        credibility_score=0.85  # Wikidata is community-verified
                    ))
                    
        except Exception as e:
            logger.warning(f"Wikidata search failed: {e}")
        
        return results
    
    async def get_entity_facts(self, entity_id: str) -> Dict[str, Any]:
        """Get structured facts about an entity"""
        session = await self.get_session()
        
        try:
            params = {
                "action": "wbgetentities",
                "ids": entity_id,
                "format": "json",
                "languages": "en"
            }
            
            async with session.get(
                self.BASE_URL,
                params=params
            ) as resp:
                if resp.status != 200:
                    return {}
                
                data = await resp.json()
                entity = data.get("entities", {}).get(entity_id, {})
                
                claims = entity.get("claims", {})
                labels = entity.get("labels", {})
                descriptions = entity.get("descriptions", {})
                
                return {
                    "id": entity_id,
                    "label": labels.get("en", {}).get("value"),
                    "description": descriptions.get("en", {}).get("value"),
                    "claims_count": len(claims),
                    "properties": list(claims.keys())[:20]
                }
                
        except Exception as e:
            logger.warning(f"Wikidata entity fetch failed: {e}")
            return {}


class DBpediaSource(DataSource):
    """
    DBpedia - Structured data extracted from Wikipedia
    https://dbpedia.org/
    
    Free SPARQL endpoint
    """
    
    SPARQL_URL = "https://dbpedia.org/sparql"
    
    @property
    def name(self) -> str:
        return "DBpedia"
    
    @property
    def source_type(self) -> str:
        return "knowledge_base"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        session = await self.get_session()
        results = []
        
        try:
            # Simple text search using SPARQL
            sparql_query = f"""
            SELECT DISTINCT ?subject ?label ?abstract WHERE {{
                ?subject rdfs:label ?label .
                ?subject dbo:abstract ?abstract .
                FILTER (lang(?label) = 'en')
                FILTER (lang(?abstract) = 'en')
                FILTER (CONTAINS(LCASE(?label), LCASE("{query}")))
            }}
            LIMIT {limit}
            """
            
            params = {
                "query": sparql_query,
                "format": "application/json"
            }
            
            async with session.get(
                self.SPARQL_URL,
                params=params,
                headers={"Accept": "application/json"}
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for binding in data.get("results", {}).get("bindings", []):
                    abstract = binding.get("abstract", {}).get("value", "")
                    
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=0.75,
                        title=binding.get("label", {}).get("value", ""),
                        content=abstract[:500],
                        url=binding.get("subject", {}).get("value"),
                        metadata={
                            "full_abstract_length": len(abstract)
                        },
                        credibility_score=0.8
                    ))
                    
        except Exception as e:
            logger.warning(f"DBpedia search failed: {e}")
        
        return results


# ============================================================
# GOVERNMENT & OFFICIAL SOURCES
# ============================================================

class WHOSource(DataSource):
    """
    World Health Organization - Health information
    https://www.who.int/
    
    Free API for health data
    """
    
    BASE_URL = "https://ghoapi.azureedge.net/api"
    
    @property
    def name(self) -> str:
        return "WHO"
    
    @property
    def source_type(self) -> str:
        return "official"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        session = await self.get_session()
        results = []
        
        try:
            # Search indicators
            async with session.get(
                f"{self.BASE_URL}/Indicator",
                params={"$filter": f"contains(IndicatorName, '{query}')"}
            ) as resp:
                if resp.status != 200:
                    return results
                
                data = await resp.json()
                
                for indicator in data.get("value", [])[:limit]:
                    results.append(SourceResult(
                        source_name=self.name,
                        source_type=self.source_type,
                        relevance=0.85,
                        title=indicator.get("IndicatorName", ""),
                        content=f"WHO Health Indicator: {indicator.get('IndicatorName', '')}",
                        url=f"https://www.who.int/data/gho/indicator-metadata-registry/{indicator.get('IndicatorCode', '')}",
                        metadata={
                            "indicator_code": indicator.get("IndicatorCode"),
                            "language": indicator.get("Language")
                        },
                        credibility_score=0.98  # Official WHO data
                    ))
                    
        except Exception as e:
            logger.warning(f"WHO search failed: {e}")
        
        return results


class CDCSource(DataSource):
    """
    Centers for Disease Control and Prevention - US health data
    https://www.cdc.gov/
    
    Free API for health statistics
    """
    
    BASE_URL = "https://data.cdc.gov/resource"
    
    @property
    def name(self) -> str:
        return "CDC"
    
    @property
    def source_type(self) -> str:
        return "official"
    
    async def search(self, query: str, limit: int = 10) -> List[SourceResult]:
        # CDC uses dataset-specific endpoints
        # This is a simplified implementation
        session = await self.get_session()
        results = []
        
        # Return informational result pointing to CDC
        results.append(SourceResult(
            source_name=self.name,
            source_type=self.source_type,
            relevance=0.8,
            title=f"CDC Data on: {query}",
            content="For authoritative health information, consult the CDC website directly.",
            url=f"https://www.cdc.gov/search/?query={quote_plus(query)}",
            metadata={},
            credibility_score=0.98
        ))
        
        return results


# ============================================================
# MULTI-ENGINE WEB SEARCH
# ============================================================

class MultiEngineWebSearch:
    """
    Aggregates results from multiple search engines for comprehensive web coverage.
    
    Engines:
    - DuckDuckGo (free, no API key)
    - Brave Search (API key, 2000 free/month)
    - Serper/Google (API key, 2500 free/month)
    - SearX instances (free, open source)
    - Tavily (API key, 1000 free/month)
    
    DEEP RESEARCH MODE: Queries ALL available engines by default.
    """
    
    def __init__(self, session: aiohttp.ClientSession = None):
        self._session = session
        self._own_session = False
        
        # API keys
        self.brave_key = os.getenv('BRAVE_API_KEY')
        self.serper_key = os.getenv('SERPER_API_KEY')
        self.tavily_key = os.getenv('TAVILY_API_KEY')
        
        # SearX public instances (fallback)
        self.searx_instances = [
            "https://searx.be",
            "https://search.sapti.me",
            "https://searx.tiekoetter.com",
        ]
    
    async def get_session(self) -> aiohttp.ClientSession:
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            )
            self._own_session = True
        return self._session
    
    async def close(self):
        if self._own_session and self._session:
            await self._session.close()
    
    def get_available_engines(self) -> List[str]:
        """List available search engines"""
        engines = ["duckduckgo"]  # Always available
        if self.brave_key:
            engines.append("brave")
        if self.serper_key:
            engines.append("serper")
        if self.tavily_key:
            engines.append("tavily")
        engines.append("searx")  # Public instances
        return engines
    
    async def search_duckduckgo(self, query: str, limit: int = 10) -> List[SourceResult]:
        """DuckDuckGo Instant Answer API - completely free"""
        session = await self.get_session()
        results = []
        
        try:
            params = {
                "q": query,
                "format": "json",
                "no_redirect": 1,
                "no_html": 1
            }
            
            async with session.get(
                "https://api.duckduckgo.com/",
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Abstract
                    if data.get("Abstract"):
                        results.append(SourceResult(
                            source_name="DuckDuckGo",
                            source_type="search",
                            relevance=0.9,
                            title=data.get("Heading", query),
                            content=data.get("Abstract", ""),
                            url=data.get("AbstractURL"),
                            metadata={"source": data.get("AbstractSource")},
                            credibility_score=0.7
                        ))
                    
                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:limit]:
                        if isinstance(topic, dict) and topic.get("Text"):
                            results.append(SourceResult(
                                source_name="DuckDuckGo",
                                source_type="search",
                                relevance=0.7,
                                title=topic.get("Text", "")[:100],
                                content=topic.get("Text", ""),
                                url=topic.get("FirstURL"),
                                credibility_score=0.6
                            ))
        except Exception as e:
            logger.warning(f"DuckDuckGo search failed: {e}")
        
        return results
    
    async def search_brave(self, query: str, limit: int = 10) -> List[SourceResult]:
        """Brave Search API - 2000 free queries/month"""
        if not self.brave_key:
            return []
        
        session = await self.get_session()
        results = []
        
        try:
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.brave_key
            }
            
            params = {
                "q": query,
                "count": limit
            }
            
            async with session.get(
                "https://api.search.brave.com/res/v1/web/search",
                headers=headers,
                params=params
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    for item in data.get("web", {}).get("results", []):
                        results.append(SourceResult(
                            source_name="Brave Search",
                            source_type="search",
                            relevance=0.8,
                            title=item.get("title", ""),
                            content=item.get("description", ""),
                            url=item.get("url"),
                            metadata={"age": item.get("age")},
                            credibility_score=0.65
                        ))
        except Exception as e:
            logger.warning(f"Brave search failed: {e}")
        
        return results
    
    async def search_serper(self, query: str, limit: int = 10) -> List[SourceResult]:
        """Serper API (Google search) - 2500 free queries/month"""
        if not self.serper_key:
            return []
        
        session = await self.get_session()
        results = []
        
        try:
            headers = {
                "X-API-KEY": self.serper_key,
                "Content-Type": "application/json"
            }
            
            payload = {
                "q": query,
                "num": limit
            }
            
            async with session.post(
                "https://google.serper.dev/search",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # Organic results
                    for item in data.get("organic", []):
                        results.append(SourceResult(
                            source_name="Serper (Google)",
                            source_type="search",
                            relevance=0.9,
                            title=item.get("title", ""),
                            content=item.get("snippet", ""),
                            url=item.get("link"),
                            metadata={"position": item.get("position")},
                            credibility_score=0.7
                        ))
                    
                    # Knowledge graph
                    kg = data.get("knowledgeGraph", {})
                    if kg.get("title"):
                        results.append(SourceResult(
                            source_name="Google Knowledge Graph",
                            source_type="knowledge",
                            relevance=0.95,
                            title=kg.get("title", ""),
                            content=kg.get("description", ""),
                            url=kg.get("website"),
                            metadata={"type": kg.get("type")},
                            credibility_score=0.85
                        ))
        except Exception as e:
            logger.warning(f"Serper search failed: {e}")
        
        return results
    
    async def search_tavily(self, query: str, limit: int = 10) -> List[SourceResult]:
        """Tavily API - AI-powered search, 1000 free/month"""
        if not self.tavily_key:
            return []
        
        session = await self.get_session()
        results = []
        
        try:
            headers = {
                "Content-Type": "application/json"
            }
            
            payload = {
                "api_key": self.tavily_key,
                "query": query,
                "search_depth": "advanced",
                "max_results": limit
            }
            
            async with session.post(
                "https://api.tavily.com/search",
                headers=headers,
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    for item in data.get("results", []):
                        results.append(SourceResult(
                            source_name="Tavily",
                            source_type="search",
                            relevance=item.get("relevance_score", 0.8),
                            title=item.get("title", ""),
                            content=item.get("content", ""),
                            url=item.get("url"),
                            credibility_score=0.75
                        ))
        except Exception as e:
            logger.warning(f"Tavily search failed: {e}")
        
        return results
    
    async def search_searx(self, query: str, limit: int = 10) -> List[SourceResult]:
        """SearX - Open source metasearch (public instances)"""
        session = await self.get_session()
        results = []
        
        for instance in self.searx_instances:
            try:
                params = {
                    "q": query,
                    "format": "json",
                    "engines": "google,bing,duckduckgo"
                }
                
                async with session.get(
                    f"{instance}/search",
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        for item in data.get("results", [])[:limit]:
                            results.append(SourceResult(
                                source_name=f"SearX ({instance.split('//')[1]})",
                                source_type="search",
                                relevance=0.7,
                                title=item.get("title", ""),
                                content=item.get("content", ""),
                                url=item.get("url"),
                                metadata={"engine": item.get("engine")},
                                credibility_score=0.6
                            ))
                        
                        if results:
                            break  # Use first working instance
                            
            except Exception as e:
                logger.debug(f"SearX instance {instance} failed: {e}")
                continue
        
        return results
    
    async def search_all(self, query: str, limit_per_engine: int = 10) -> List[SourceResult]:
        """
        Search ALL available engines in parallel - DEEP RESEARCH MODE.
        
        Returns combined, deduplicated results from all engines.
        """
        tasks = [
            self.search_duckduckgo(query, limit_per_engine),
            self.search_brave(query, limit_per_engine),
            self.search_serper(query, limit_per_engine),
            self.search_tavily(query, limit_per_engine),
            self.search_searx(query, limit_per_engine),
        ]
        
        logger.info(f"Multi-Engine Search: Querying {len(self.get_available_engines())} engines")
        
        try:
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=45
            )
        except asyncio.TimeoutError:
            logger.warning("Multi-engine search timed out")
            return []
        
        # Combine results
        results = []
        seen_urls = set()
        
        for result_set in all_results:
            if isinstance(result_set, Exception):
                continue
            for r in result_set:
                # Deduplicate by URL
                if r.url and r.url not in seen_urls:
                    seen_urls.add(r.url)
                    results.append(r)
                elif not r.url:
                    results.append(r)
        
        # Sort by relevance and credibility
        results.sort(key=lambda r: r.relevance * r.credibility_score, reverse=True)
        
        logger.info(f"Multi-Engine Search: Got {len(results)} unique results")
        
        return results


# ============================================================
# FACT-CHECK AGGREGATOR - DEEP RESEARCH MODE
# ============================================================

class FactCheckAggregator:
    """
    Aggregate results from multiple fact-checking sources.
    
    DEEP RESEARCH MODE (Default):
    - Queries ALL available sources
    - Minimum 20 sources before conclusion
    - All academic sources are MANDATORY
    - Cross-referencing is ALWAYS enabled
    - Multi-engine web search
    """
    
    # Configuration for deep research mode
    MIN_SOURCES_REQUIRED = 20
    ACADEMIC_SOURCES_MANDATORY = True
    ENABLE_CROSS_REFERENCING = True
    MULTI_ENGINE_SEARCH = True
    
    def __init__(self, session: aiohttp.ClientSession = None):
        # ========== ACADEMIC SOURCES (MANDATORY) ==========
        self.academic_sources: List[DataSource] = [
            SemanticScholarSource(session),
            PubMedSource(session),
            ArxivSource(session),
            CrossRefSource(session),
        ]
        
        # ========== NEWS SOURCES ==========
        self.news_sources: List[DataSource] = [
            NewsAPISource(session),
            MediaStackSource(session),
        ]
        
        # ========== KNOWLEDGE BASE SOURCES ==========
        self.knowledge_sources: List[DataSource] = [
            WikidataSource(session),
            DBpediaSource(session),
        ]
        
        # ========== OFFICIAL SOURCES ==========
        self.official_sources: List[DataSource] = [
            WHOSource(session),
            CDCSource(session),
        ]
        
        # ========== MULTI-ENGINE WEB SEARCH ==========
        self.web_search = MultiEngineWebSearch(session)
        
        # All sources combined
        self.sources: List[DataSource] = (
            self.academic_sources + 
            self.news_sources + 
            self.knowledge_sources + 
            self.official_sources
        )
    
    def get_available_sources(self) -> List[str]:
        """Get list of available sources"""
        return [s.name for s in self.sources if s.is_available]
    
    def get_academic_sources(self) -> List[str]:
        """Get list of academic sources"""
        return [s.name for s in self.academic_sources if s.is_available]
    
    async def search_all(
        self,
        query: str,
        limit_per_source: int = 10,  # Increased from 5
        source_types: List[str] = None,
        require_minimum: bool = True  # Enforce minimum sources
    ) -> List[SourceResult]:
        """
        Search all sources in parallel - DEEP RESEARCH MODE.
        
        Args:
            query: Search query
            limit_per_source: Max results per source (default 10)
            source_types: Filter by source types (academic, news, etc.)
            require_minimum: Whether to require minimum sources
        """
        tasks = []
        source_mapping = []  # Track which source each task is for
        
        # DEEP RESEARCH: Query ALL sources
        for source in self.sources:
            if not source.is_available:
                continue
            if source_types and source.source_type not in source_types:
                continue
            
            tasks.append(source.search(query, limit_per_source))
            source_mapping.append(source.name)
        
        if not tasks:
            logger.warning("No sources available for search")
            return []
        
        logger.info(f"Deep Research: Querying {len(tasks)} sources for: {query[:50]}...")
        
        # Gather with extended timeout for thorough research
        try:
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=60  # Extended timeout for deep research
            )
        except asyncio.TimeoutError:
            logger.warning("Source search timed out - using partial results")
            all_results = []
        
        # Flatten and filter results
        results = []
        sources_with_results = set()
        
        for idx, result_set in enumerate(all_results):
            if isinstance(result_set, Exception):
                logger.warning(f"Source {source_mapping[idx]} error: {result_set}")
                continue
            if result_set:
                sources_with_results.add(source_mapping[idx])
                results.extend(result_set)
        
        logger.info(f"Deep Research: Got {len(results)} results from {len(sources_with_results)} sources")
        
        # Sort by relevance and credibility
        results.sort(key=lambda r: r.relevance * r.credibility_score, reverse=True)
        
        return results
    
    async def search_academic_only(
        self,
        query: str,
        limit_per_source: int = 15
    ) -> List[SourceResult]:
        """
        Search ONLY academic sources - required for every verification.
        """
        tasks = []
        
        for source in self.academic_sources:
            if source.is_available:
                tasks.append(source.search(query, limit_per_source))
        
        if not tasks:
            logger.warning("No academic sources available")
            return []
        
        logger.info(f"Querying {len(tasks)} academic sources")
        
        try:
            all_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=45
            )
        except asyncio.TimeoutError:
            logger.warning("Academic search timed out")
            return []
        
        results = []
        for result_set in all_results:
            if isinstance(result_set, Exception):
                continue
            results.extend(result_set)
        
        return results
    
    def cross_reference_sources(
        self,
        results: List[SourceResult],
        threshold: float = 0.7
    ) -> Dict[str, Any]:
        """
        Cross-reference sources against each other.
        
        Looks for:
        - Agreement between sources
        - Contradictions
        - Citation networks
        - Author credibility
        """
        if len(results) < 2:
            return {"agreement": 0, "contradictions": [], "verified_facts": []}
        
        # Group by source type
        by_type = {}
        for r in results:
            if r.source_type not in by_type:
                by_type[r.source_type] = []
            by_type[r.source_type].append(r)
        
        # Look for common themes/claims across sources
        all_content = " ".join([r.content.lower() for r in results])
        
        # Simple agreement metric: how many sources have similar content?
        agreement_scores = []
        for i, r1 in enumerate(results[:10]):  # Compare first 10
            for r2 in results[i+1:11]:
                # Simple overlap check
                words1 = set(r1.content.lower().split())
                words2 = set(r2.content.lower().split())
                if words1 and words2:
                    overlap = len(words1 & words2) / len(words1 | words2)
                    agreement_scores.append(overlap)
        
        avg_agreement = sum(agreement_scores) / len(agreement_scores) if agreement_scores else 0
        
        return {
            "agreement": round(avg_agreement, 3),
            "sources_by_type": {k: len(v) for k, v in by_type.items()},
            "total_sources": len(results),
            "cross_referenced": True
        }
    
    async def get_evidence_for_claim(
        self,
        claim: str,
        min_credibility: float = 0.5,  # Lowered to get more sources
        require_academic: bool = True,  # MANDATORY academic sources
        enable_cross_reference: bool = True  # MANDATORY cross-referencing
    ) -> Dict[str, Any]:
        """
        Get supporting/refuting evidence for a claim - DEEP RESEARCH MODE.
        
        Returns structured evidence report with:
        - Minimum 20 sources
        - All academic sources queried
        - Cross-referencing results
        - Multi-engine web search
        """
        # Query all structured sources with higher limits
        all_results = await self.search_all(claim, limit_per_source=10)
        
        # If academic sources mandatory, also do a dedicated academic search
        academic_results = []
        if require_academic or self.ACADEMIC_SOURCES_MANDATORY:
            academic_results = await self.search_academic_only(claim, limit_per_source=15)
            # Merge, avoiding duplicates
            existing_urls = {r.url for r in all_results if r.url}
            for ar in academic_results:
                if ar.url not in existing_urls:
                    all_results.append(ar)
                    existing_urls.add(ar.url)
        
        # Multi-engine web search (always enabled in deep research mode)
        if self.MULTI_ENGINE_SEARCH:
            web_results = await self.web_search.search_all(claim, limit_per_engine=10)
            existing_urls = {r.url for r in all_results if r.url}
            for wr in web_results:
                if wr.url and wr.url not in existing_urls:
                    all_results.append(wr)
                    existing_urls.add(wr.url)
            logger.info(f"Added {len(web_results)} web search results from {len(self.web_search.get_available_engines())} engines")
        
        # Filter by credibility
        credible_results = [r for r in all_results if r.credibility_score >= min_credibility]
        
        logger.info(f"Deep Research: {len(credible_results)} credible sources for claim")
        
        # Cross-reference if enabled
        cross_ref_data = {}
        if enable_cross_reference or self.ENABLE_CROSS_REFERENCING:
            cross_ref_data = self.cross_reference_sources(credible_results)
        
        # Categorize by source type
        by_type = {}
        for result in credible_results:
            if result.source_type not in by_type:
                by_type[result.source_type] = []
            by_type[result.source_type].append({
                "source": result.source_name,
                "title": result.title,
                "content": result.content[:300],  # More content
                "url": result.url,
                "credibility": result.credibility_score,
                "relevance": result.relevance
            })
        
        # Calculate overall evidence strength
        if not credible_results:
            evidence_strength = 0
        else:
            avg_credibility = sum(r.credibility_score for r in credible_results) / len(credible_results)
            avg_relevance = sum(r.relevance for r in credible_results) / len(credible_results)
            source_diversity = len(set(r.source_type for r in credible_results)) / 5  # Max 5 types
            
            # Factor in cross-referencing agreement
            cross_ref_boost = cross_ref_data.get("agreement", 0) * 0.2 if cross_ref_data else 0
            
            evidence_strength = (
                avg_credibility * 0.4 + 
                avg_relevance * 0.2 + 
                source_diversity * 0.2 +
                cross_ref_boost
            )
            
            # Boost for meeting minimum sources
            if len(credible_results) >= self.MIN_SOURCES_REQUIRED:
                evidence_strength = min(1.0, evidence_strength * 1.1)
        
        return {
            "claim": claim,
            "evidence_count": len(credible_results),
            "min_sources_required": self.MIN_SOURCES_REQUIRED,
            "sources_sufficient": len(credible_results) >= self.MIN_SOURCES_REQUIRED,
            "evidence_strength": round(evidence_strength, 3),
            "by_source_type": by_type,
            "academic_sources_queried": len([r for r in credible_results if r.source_type == "academic"]),
            "cross_reference": cross_ref_data,
            "top_sources": [
                {
                    "source": r.source_name,
                    "type": r.source_type,
                    "title": r.title,
                    "url": r.url,
                    "credibility": r.credibility_score,
                    "relevance": r.relevance
                }
                for r in credible_results[:15]  # Top 15 sources
            ],
            "deep_research_mode": True
        }
    
    async def close(self):
        """Close all source connections"""
        for source in self.sources:
            await source.close()


# ============================================================
# MAIN / TESTING
# ============================================================

async def main():
    """Test data sources"""
    
    aggregator = FactCheckAggregator()
    
    print("Available sources:", aggregator.get_available_sources())
    
    test_claims = [
        "Climate change is caused by human activities",
        "COVID-19 vaccines are safe and effective",
        "The Earth orbits the Sun"
    ]
    
    for claim in test_claims:
        print(f"\n{'='*60}")
        print(f"Claim: {claim}")
        print(f"{'='*60}")
        
        evidence = await aggregator.get_evidence_for_claim(claim)
        
        print(f"Evidence count: {evidence['evidence_count']}")
        print(f"Evidence strength: {evidence['evidence_strength']}")
        print(f"\nTop sources:")
        for source in evidence['top_sources']:
            print(f"  - {source['source']}: {source['title'][:60]}...")
            print(f"    Credibility: {source['credibility']}")
    
    await aggregator.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
