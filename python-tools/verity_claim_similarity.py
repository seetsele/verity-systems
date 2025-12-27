"""
Verity Claim Similarity Engine
==============================
Advanced semantic similarity detection to find related claims.

Features:
- Semantic embeddings for claim comparison
- TF-IDF vectorization for fast matching
- Fuzzy string matching
- Historical claim database
- Similar claim retrieval
"""

import re
import math
import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Set
from collections import defaultdict, Counter


@dataclass
class ClaimRecord:
    """A stored claim with its verification result"""
    claim_id: str
    claim_text: str
    normalized_text: str
    verdict: str
    confidence: float
    sources: List[str]
    timestamp: datetime
    tokens: Set[str] = field(default_factory=set)
    entities: Dict[str, List[str]] = field(default_factory=dict)
    category: str = ""


@dataclass
class SimilarityMatch:
    """A match result from similarity search"""
    claim: ClaimRecord
    similarity_score: float
    match_type: str  # "exact", "semantic", "entity", "fuzzy"
    shared_entities: List[str] = field(default_factory=list)
    shared_tokens: List[str] = field(default_factory=list)


class TextNormalizer:
    """
    Normalize text for comparison.
    """
    
    STOP_WORDS = {
        'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'can', 'must', 'shall', 'to', 'of', 'in',
        'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
        'during', 'before', 'after', 'above', 'below', 'between', 'under',
        'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
        'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than',
        'too', 'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until',
        'while', 'although', 'though', 'this', 'that', 'these', 'those',
        'it', 'its', 'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
        'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers',
        'they', 'them', 'their', 'theirs', 'what', 'which', 'who', 'whom'
    }
    
    @staticmethod
    def normalize(text: str) -> str:
        """Basic normalization"""
        # Lowercase
        text = text.lower()
        # Remove punctuation except hyphens
        text = re.sub(r'[^\w\s\-]', '', text)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
    
    @classmethod
    def tokenize(cls, text: str, remove_stopwords: bool = True) -> List[str]:
        """Tokenize text"""
        normalized = cls.normalize(text)
        tokens = normalized.split()
        
        if remove_stopwords:
            tokens = [t for t in tokens if t not in cls.STOP_WORDS]
        
        return tokens
    
    @classmethod
    def get_token_set(cls, text: str) -> Set[str]:
        """Get set of tokens"""
        return set(cls.tokenize(text))


class TFIDFVectorizer:
    """
    TF-IDF vectorizer for document similarity.
    """
    
    def __init__(self):
        self.vocabulary: Dict[str, int] = {}
        self.idf_scores: Dict[str, float] = {}
        self.document_count = 0
        self.document_frequencies: Dict[str, int] = defaultdict(int)
    
    def fit(self, documents: List[str]):
        """Fit on a corpus of documents"""
        self.document_count = len(documents)
        
        # Count document frequencies
        for doc in documents:
            tokens = set(TextNormalizer.tokenize(doc))
            for token in tokens:
                self.document_frequencies[token] += 1
        
        # Build vocabulary
        self.vocabulary = {
            token: idx for idx, token in enumerate(self.document_frequencies.keys())
        }
        
        # Calculate IDF scores
        for token, df in self.document_frequencies.items():
            self.idf_scores[token] = math.log(self.document_count / (df + 1)) + 1
    
    def transform(self, text: str) -> Dict[str, float]:
        """Transform text to TF-IDF vector"""
        tokens = TextNormalizer.tokenize(text)
        token_counts = Counter(tokens)
        total_tokens = len(tokens)
        
        vector = {}
        for token, count in token_counts.items():
            if token in self.vocabulary:
                tf = count / total_tokens if total_tokens > 0 else 0
                idf = self.idf_scores.get(token, 1.0)
                vector[token] = tf * idf
        
        return vector
    
    def cosine_similarity(self, vec1: Dict[str, float], vec2: Dict[str, float]) -> float:
        """Calculate cosine similarity between two vectors"""
        # Get common keys
        common_keys = set(vec1.keys()) & set(vec2.keys())
        
        if not common_keys:
            return 0.0
        
        # Dot product
        dot_product = sum(vec1[k] * vec2[k] for k in common_keys)
        
        # Magnitudes
        mag1 = math.sqrt(sum(v ** 2 for v in vec1.values()))
        mag2 = math.sqrt(sum(v ** 2 for v in vec2.values()))
        
        if mag1 == 0 or mag2 == 0:
            return 0.0
        
        return dot_product / (mag1 * mag2)


class JaccardSimilarity:
    """
    Jaccard similarity for set-based comparison.
    """
    
    @staticmethod
    def similarity(set1: Set[str], set2: Set[str]) -> float:
        """Calculate Jaccard similarity"""
        if not set1 and not set2:
            return 1.0
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0


class LevenshteinDistance:
    """
    Levenshtein edit distance for fuzzy matching.
    """
    
    @staticmethod
    def distance(s1: str, s2: str) -> int:
        """Calculate edit distance"""
        if len(s1) < len(s2):
            return LevenshteinDistance.distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    @staticmethod
    def similarity(s1: str, s2: str) -> float:
        """Calculate similarity ratio (0-1)"""
        max_len = max(len(s1), len(s2))
        if max_len == 0:
            return 1.0
        
        distance = LevenshteinDistance.distance(s1, s2)
        return 1.0 - (distance / max_len)


class NGramSimilarity:
    """
    N-gram based similarity for partial matching.
    """
    
    @staticmethod
    def get_ngrams(text: str, n: int = 3) -> Set[str]:
        """Get character n-grams"""
        text = TextNormalizer.normalize(text)
        text = text.replace(' ', '_')
        
        if len(text) < n:
            return {text}
        
        return {text[i:i+n] for i in range(len(text) - n + 1)}
    
    @staticmethod
    def similarity(text1: str, text2: str, n: int = 3) -> float:
        """Calculate n-gram similarity"""
        ngrams1 = NGramSimilarity.get_ngrams(text1, n)
        ngrams2 = NGramSimilarity.get_ngrams(text2, n)
        
        return JaccardSimilarity.similarity(ngrams1, ngrams2)


class EntityMatcher:
    """
    Match claims based on shared entities.
    """
    
    # Entity patterns
    PATTERNS = {
        "person": r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b',
        "date": r'\b(?:\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}|\d{4}|(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s*\d{4}?)\b',
        "number": r'\b\d+(?:,\d{3})*(?:\.\d+)?(?:\s*(?:million|billion|trillion|percent|%))?\b',
        "organization": r'\b(?:NASA|FBI|CIA|WHO|UN|EU|NATO|CDC|EPA|FDA|NIH|MIT|DARPA|NSA)\b',
        "location": r'\b(?:United States|America|China|Russia|Europe|Africa|Asia|Australia|Canada|Mexico|UK|France|Germany|Japan|India|Brazil)\b'
    }
    
    @classmethod
    def extract_entities(cls, text: str) -> Dict[str, List[str]]:
        """Extract entities from text"""
        entities = {}
        
        for entity_type, pattern in cls.PATTERNS.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                entities[entity_type] = list(set(matches))
        
        return entities
    
    @classmethod
    def entity_overlap(cls, entities1: Dict[str, List[str]], entities2: Dict[str, List[str]]) -> Tuple[float, List[str]]:
        """Calculate entity overlap between two claims"""
        all_entities1 = set()
        all_entities2 = set()
        
        for ents in entities1.values():
            all_entities1.update(e.lower() for e in ents)
        
        for ents in entities2.values():
            all_entities2.update(e.lower() for e in ents)
        
        if not all_entities1 and not all_entities2:
            return 0.0, []
        
        shared = all_entities1 & all_entities2
        total = all_entities1 | all_entities2
        
        score = len(shared) / len(total) if total else 0.0
        
        return score, list(shared)


class ClaimSimilarityEngine:
    """
    Main engine for finding similar claims.
    
    Combines multiple similarity methods:
    1. TF-IDF cosine similarity (semantic)
    2. Jaccard token similarity
    3. N-gram character similarity
    4. Entity overlap
    5. Fuzzy string matching
    """
    
    def __init__(self):
        self.claims: Dict[str, ClaimRecord] = {}
        self.tfidf = TFIDFVectorizer()
        self.tfidf_vectors: Dict[str, Dict[str, float]] = {}
        self.entity_index: Dict[str, Set[str]] = defaultdict(set)  # entity -> claim_ids
        self.token_index: Dict[str, Set[str]] = defaultdict(set)  # token -> claim_ids
        self.fitted = False
    
    def add_claim(
        self,
        claim_text: str,
        verdict: str,
        confidence: float,
        sources: List[str] = None,
        category: str = ""
    ) -> str:
        """Add a claim to the database"""
        # Generate ID
        claim_id = hashlib.sha256(claim_text.encode()).hexdigest()[:16]
        
        # Normalize
        normalized = TextNormalizer.normalize(claim_text)
        tokens = TextNormalizer.get_token_set(claim_text)
        entities = EntityMatcher.extract_entities(claim_text)
        
        # Create record
        record = ClaimRecord(
            claim_id=claim_id,
            claim_text=claim_text,
            normalized_text=normalized,
            verdict=verdict,
            confidence=confidence,
            sources=sources or [],
            timestamp=datetime.now(),
            tokens=tokens,
            entities=entities,
            category=category
        )
        
        # Store
        self.claims[claim_id] = record
        
        # Update indexes
        for token in tokens:
            self.token_index[token].add(claim_id)
        
        for entity_type, entity_list in entities.items():
            for entity in entity_list:
                self.entity_index[entity.lower()].add(claim_id)
        
        # Mark as needing refit
        self.fitted = False
        
        return claim_id
    
    def _fit_tfidf(self):
        """Fit TF-IDF on all claims"""
        if not self.claims:
            return
        
        documents = [claim.claim_text for claim in self.claims.values()]
        self.tfidf.fit(documents)
        
        # Pre-compute vectors
        for claim_id, claim in self.claims.items():
            self.tfidf_vectors[claim_id] = self.tfidf.transform(claim.claim_text)
        
        self.fitted = True
    
    def find_similar(
        self,
        query_claim: str,
        top_k: int = 5,
        min_similarity: float = 0.3,
        methods: List[str] = None
    ) -> List[SimilarityMatch]:
        """
        Find claims similar to the query.
        
        Methods:
        - "tfidf": TF-IDF cosine similarity
        - "jaccard": Jaccard token similarity
        - "ngram": N-gram character similarity
        - "entity": Entity overlap
        - "fuzzy": Levenshtein similarity
        """
        if not self.claims:
            return []
        
        if not self.fitted:
            self._fit_tfidf()
        
        methods = methods or ["tfidf", "jaccard", "entity"]
        
        query_normalized = TextNormalizer.normalize(query_claim)
        query_tokens = TextNormalizer.get_token_set(query_claim)
        query_entities = EntityMatcher.extract_entities(query_claim)
        query_tfidf = self.tfidf.transform(query_claim)
        
        # Candidate scoring
        candidates: Dict[str, Dict] = {}
        
        for claim_id, claim in self.claims.items():
            scores = {}
            
            # TF-IDF similarity
            if "tfidf" in methods and claim_id in self.tfidf_vectors:
                scores["tfidf"] = self.tfidf.cosine_similarity(
                    query_tfidf, self.tfidf_vectors[claim_id]
                )
            
            # Jaccard similarity
            if "jaccard" in methods:
                scores["jaccard"] = JaccardSimilarity.similarity(
                    query_tokens, claim.tokens
                )
            
            # N-gram similarity
            if "ngram" in methods:
                scores["ngram"] = NGramSimilarity.similarity(
                    query_claim, claim.claim_text
                )
            
            # Entity overlap
            if "entity" in methods:
                entity_score, shared_entities = EntityMatcher.entity_overlap(
                    query_entities, claim.entities
                )
                scores["entity"] = entity_score
                scores["shared_entities"] = shared_entities
            
            # Fuzzy matching
            if "fuzzy" in methods:
                scores["fuzzy"] = LevenshteinDistance.similarity(
                    query_normalized, claim.normalized_text
                )
            
            # Calculate weighted average
            # Weights emphasize semantic (TF-IDF) and entity matching
            weights = {
                "tfidf": 0.35,
                "jaccard": 0.15,
                "ngram": 0.10,
                "entity": 0.30,
                "fuzzy": 0.10
            }
            
            total_score = 0.0
            total_weight = 0.0
            
            for method, weight in weights.items():
                if method in scores and method != "shared_entities":
                    total_score += scores[method] * weight
                    total_weight += weight
            
            if total_weight > 0:
                final_score = total_score / total_weight
            else:
                final_score = 0.0
            
            if final_score >= min_similarity:
                candidates[claim_id] = {
                    "score": final_score,
                    "scores": scores,
                    "match_type": self._determine_match_type(scores),
                    "shared_entities": scores.get("shared_entities", [])
                }
        
        # Sort by score
        sorted_candidates = sorted(
            candidates.items(),
            key=lambda x: x[1]["score"],
            reverse=True
        )[:top_k]
        
        # Build results
        results = []
        for claim_id, data in sorted_candidates:
            claim = self.claims[claim_id]
            
            shared_tokens = list(query_tokens & claim.tokens)
            
            results.append(SimilarityMatch(
                claim=claim,
                similarity_score=data["score"],
                match_type=data["match_type"],
                shared_entities=data["shared_entities"],
                shared_tokens=shared_tokens[:10]  # Top 10
            ))
        
        return results
    
    def _determine_match_type(self, scores: Dict[str, float]) -> str:
        """Determine the primary match type"""
        # Check for near-exact match
        if scores.get("fuzzy", 0) > 0.9:
            return "exact"
        
        # Check for entity match
        if scores.get("entity", 0) > 0.6:
            return "entity"
        
        # Check for semantic match
        if scores.get("tfidf", 0) > 0.5:
            return "semantic"
        
        return "fuzzy"
    
    def find_exact_duplicate(self, claim_text: str) -> Optional[ClaimRecord]:
        """Check if claim is an exact duplicate"""
        normalized = TextNormalizer.normalize(claim_text)
        
        for claim in self.claims.values():
            if claim.normalized_text == normalized:
                return claim
            
            # Very high fuzzy similarity
            if LevenshteinDistance.similarity(normalized, claim.normalized_text) > 0.95:
                return claim
        
        return None
    
    def find_by_entity(self, entity: str) -> List[ClaimRecord]:
        """Find claims containing a specific entity"""
        entity_lower = entity.lower()
        claim_ids = self.entity_index.get(entity_lower, set())
        
        return [self.claims[cid] for cid in claim_ids if cid in self.claims]
    
    def get_claim_clusters(self, min_similarity: float = 0.5) -> List[List[ClaimRecord]]:
        """Group similar claims into clusters"""
        if not self.claims:
            return []
        
        # Simple greedy clustering
        assigned = set()
        clusters = []
        
        for claim_id, claim in self.claims.items():
            if claim_id in assigned:
                continue
            
            # Start new cluster
            cluster = [claim]
            assigned.add(claim_id)
            
            # Find similar claims
            similar = self.find_similar(
                claim.claim_text,
                top_k=50,
                min_similarity=min_similarity
            )
            
            for match in similar:
                if match.claim.claim_id not in assigned:
                    cluster.append(match.claim)
                    assigned.add(match.claim.claim_id)
            
            clusters.append(cluster)
        
        return clusters
    
    def export_database(self) -> List[Dict]:
        """Export all claims as JSON-serializable list"""
        return [
            {
                "claim_id": claim.claim_id,
                "claim_text": claim.claim_text,
                "verdict": claim.verdict,
                "confidence": claim.confidence,
                "sources": claim.sources,
                "timestamp": claim.timestamp.isoformat(),
                "category": claim.category,
                "entities": claim.entities
            }
            for claim in self.claims.values()
        ]
    
    def import_database(self, data: List[Dict]):
        """Import claims from JSON data"""
        for item in data:
            self.add_claim(
                claim_text=item["claim_text"],
                verdict=item["verdict"],
                confidence=item.get("confidence", 0.0),
                sources=item.get("sources", []),
                category=item.get("category", "")
            )


__all__ = [
    'ClaimSimilarityEngine', 'SimilarityMatch', 'ClaimRecord',
    'TextNormalizer', 'TFIDFVectorizer', 'JaccardSimilarity',
    'LevenshteinDistance', 'NGramSimilarity', 'EntityMatcher'
]
