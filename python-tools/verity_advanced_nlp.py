"""
Verity Advanced NLP Engine
==========================
Cutting-edge Natural Language Processing for claim analysis.

FEATURES:
- Named Entity Recognition (NER)
- Semantic Similarity Scoring
- Claim Type Classification
- Numerical Claim Extraction
- Temporal Expression Parsing
- Logical Fallacy Detection
- Sentiment & Bias Analysis
- Propaganda Technique Identification

This module uses rule-based + statistical methods for speed.
Can be enhanced with transformer models for production.
"""

import re
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from datetime import datetime, timedelta
from enum import Enum
from collections import Counter


class EntityType(Enum):
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    NUMBER = "number"
    PERCENTAGE = "percentage"
    MONEY = "money"
    SCIENTIFIC_TERM = "scientific_term"
    MEDICAL_TERM = "medical_term"
    POLITICAL_ENTITY = "political_entity"


class LogicalFallacy(Enum):
    AD_HOMINEM = "ad_hominem"
    STRAW_MAN = "straw_man"
    APPEAL_TO_AUTHORITY = "appeal_to_authority"
    FALSE_DICHOTOMY = "false_dichotomy"
    SLIPPERY_SLOPE = "slippery_slope"
    CIRCULAR_REASONING = "circular_reasoning"
    HASTY_GENERALIZATION = "hasty_generalization"
    RED_HERRING = "red_herring"
    APPEAL_TO_EMOTION = "appeal_to_emotion"
    BANDWAGON = "bandwagon"
    FALSE_CAUSE = "false_cause"
    APPEAL_TO_NATURE = "appeal_to_nature"


class PropagandaTechnique(Enum):
    LOADED_LANGUAGE = "loaded_language"
    NAME_CALLING = "name_calling"
    EXAGGERATION = "exaggeration"
    DOUBT = "doubt"
    APPEAL_TO_FEAR = "appeal_to_fear"
    FLAG_WAVING = "flag_waving"
    CAUSAL_OVERSIMPLIFICATION = "causal_oversimplification"
    WHATABOUTISM = "whataboutism"
    BLACK_WHITE_FALLACY = "black_white_fallacy"
    THOUGHT_TERMINATING_CLICHE = "thought_terminating_cliche"
    REPETITION = "repetition"
    SLOGANS = "slogans"


class BiasType(Enum):
    LEFT_BIAS = "left_bias"
    RIGHT_BIAS = "right_bias"
    SENSATIONALISM = "sensationalism"
    CONSPIRACY = "conspiracy"
    PSEUDOSCIENCE = "pseudoscience"
    SATIRE = "satire"
    NEUTRAL = "neutral"


@dataclass
class ExtractedEntity:
    text: str
    entity_type: EntityType
    start_pos: int
    end_pos: int
    confidence: float
    normalized_value: Optional[str] = None


@dataclass
class ClaimAnalysis:
    original_claim: str
    entities: List[ExtractedEntity]
    numerical_claims: List[Dict]
    temporal_expressions: List[Dict]
    detected_fallacies: List[Tuple[LogicalFallacy, float]]
    propaganda_techniques: List[Tuple[PropagandaTechnique, float]]
    bias_indicators: List[Tuple[BiasType, float]]
    sentiment_score: float  # -1 to 1
    subjectivity_score: float  # 0 to 1
    complexity_score: float  # 0 to 1
    verifiability_score: float  # 0 to 1
    key_phrases: List[str]
    suggested_searches: List[str]


class NamedEntityRecognizer:
    """
    Rule-based NER for fact-checking contexts.
    Extracts people, organizations, locations, dates, numbers, etc.
    """
    
    # Common patterns
    PATTERNS = {
        EntityType.PERCENTAGE: r'\b(\d+(?:\.\d+)?)\s*(?:%|percent|per\s*cent)\b',
        EntityType.MONEY: r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(million|billion|trillion)?|\b(\d+(?:\.\d+)?)\s*(dollars?|euros?|pounds?|yen)',
        EntityType.NUMBER: r'\b(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s*(million|billion|trillion|thousand)?\b',
        EntityType.DATE: r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?,?\s*\d{4}\b|\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b(?:19|20)\d{2}\b',
    }
    
    # Known entities (expandable)
    KNOWN_PERSONS = {
        'trump', 'biden', 'obama', 'clinton', 'bush', 'putin', 'xi jinping',
        'elon musk', 'bill gates', 'jeff bezos', 'mark zuckerberg', 'warren buffett',
        'fauci', 'tedros', 'modi', 'johnson', 'macron', 'merkel', 'trudeau'
    }
    
    KNOWN_ORGANIZATIONS = {
        'who', 'world health organization', 'cdc', 'fda', 'nih', 'nasa', 'epa',
        'fbi', 'cia', 'nsa', 'un', 'united nations', 'nato', 'eu', 'european union',
        'imf', 'world bank', 'wef', 'pfizer', 'moderna', 'johnson & johnson',
        'facebook', 'meta', 'google', 'apple', 'microsoft', 'amazon', 'twitter', 'x'
    }
    
    KNOWN_LOCATIONS = {
        'united states', 'usa', 'america', 'china', 'russia', 'india', 'brazil',
        'uk', 'united kingdom', 'germany', 'france', 'japan', 'australia',
        'wuhan', 'beijing', 'moscow', 'washington', 'new york', 'london', 'paris'
    }
    
    def extract_entities(self, text: str) -> List[ExtractedEntity]:
        """Extract all named entities from text"""
        entities = []
        text_lower = text.lower()
        
        # Extract pattern-based entities
        for entity_type, pattern in self.PATTERNS.items():
            for match in re.finditer(pattern, text, re.IGNORECASE):
                entities.append(ExtractedEntity(
                    text=match.group(0),
                    entity_type=entity_type,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    confidence=0.9,
                    normalized_value=self._normalize_value(match.group(0), entity_type)
                ))
        
        # Extract known entities
        for person in self.KNOWN_PERSONS:
            if person in text_lower:
                idx = text_lower.find(person)
                entities.append(ExtractedEntity(
                    text=text[idx:idx+len(person)],
                    entity_type=EntityType.PERSON,
                    start_pos=idx,
                    end_pos=idx+len(person),
                    confidence=0.95
                ))
        
        for org in self.KNOWN_ORGANIZATIONS:
            if org in text_lower:
                idx = text_lower.find(org)
                entities.append(ExtractedEntity(
                    text=text[idx:idx+len(org)],
                    entity_type=EntityType.ORGANIZATION,
                    start_pos=idx,
                    end_pos=idx+len(org),
                    confidence=0.95
                ))
        
        for loc in self.KNOWN_LOCATIONS:
            if loc in text_lower:
                idx = text_lower.find(loc)
                entities.append(ExtractedEntity(
                    text=text[idx:idx+len(loc)],
                    entity_type=EntityType.LOCATION,
                    start_pos=idx,
                    end_pos=idx+len(loc),
                    confidence=0.9
                ))
        
        return entities
    
    def _normalize_value(self, text: str, entity_type: EntityType) -> Optional[str]:
        """Normalize extracted values to standard format"""
        if entity_type == EntityType.NUMBER:
            # Convert "5 million" to "5000000"
            text = text.lower().replace(',', '')
            multipliers = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9, 'trillion': 1e12}
            for mult_name, mult_val in multipliers.items():
                if mult_name in text:
                    num = re.search(r'[\d.]+', text)
                    if num:
                        return str(float(num.group()) * mult_val)
            num = re.search(r'[\d.]+', text)
            return num.group() if num else text
        
        return text


class LogicalFallacyDetector:
    """
    Detects logical fallacies in claims.
    This helps identify potentially misleading arguments.
    """
    
    FALLACY_PATTERNS = {
        LogicalFallacy.AD_HOMINEM: [
            r'\b(idiot|stupid|moron|fool|liar|corrupt)\b',
            r'\bcannot be trusted\b',
            r'\bhas no credibility\b',
            r'\bjust wants\b.*(money|power|fame)',
        ],
        LogicalFallacy.APPEAL_TO_AUTHORITY: [
            r'\b(experts?|scientists?|doctors?)\s+(say|agree|confirm)\b',
            r'\baccording to\s+\w+\s+(expert|scientist|doctor)\b',
            r'\b(nobel|prize).*(winner|laureate)\s+(says?|confirms?)\b',
        ],
        LogicalFallacy.FALSE_DICHOTOMY: [
            r'\beither\s+.*\s+or\b',
            r'\bonly\s+(two|2)\s+(options?|choices?|ways?)\b',
            r'\byou\'?re\s+either\s+.*\s+or\b',
        ],
        LogicalFallacy.SLIPPERY_SLOPE: [
            r'\bwill\s+lead\s+to\b',
            r'\bnext\s+(thing|step)\s+.*\s+will\s+be\b',
            r'\bif\s+.*\s+then\s+.*\s+then\s+.*\s+then\b',
        ],
        LogicalFallacy.HASTY_GENERALIZATION: [
            r'\ball\s+(people|men|women|doctors|scientists)\b',
            r'\bno\s+one\s+(ever|can|will)\b',
            r'\beveryone\s+(knows|agrees|believes)\b',
            r'\bnobody\s+(can|ever|will)\b',
        ],
        LogicalFallacy.APPEAL_TO_EMOTION: [
            r'\bthink\s+of\s+the\s+(children|kids|elderly)\b',
            r'\bhow\s+would\s+you\s+feel\b',
            r'\bimagine\s+if\s+this\s+happened\s+to\s+you\b',
        ],
        LogicalFallacy.BANDWAGON: [
            r'\bmillions?\s+of\s+people\s+(agree|believe|support)\b',
            r'\beveryone\s+is\s+(doing|saying|believing)\b',
            r'\bjoin\s+the\s+(movement|revolution)\b',
        ],
        LogicalFallacy.FALSE_CAUSE: [
            r'\bafter\s+.*\s+therefore\s+because\b',
            r'\bsince\s+.*\s+it\s+must\s+(mean|be|cause)\b',
            r'\bcorrelation\b.*\bcausation\b',
        ],
        LogicalFallacy.APPEAL_TO_NATURE: [
            r'\bnatural\s+(is|means?)\s+(better|safer|healthier)\b',
            r'\bchemicals?\s+(are|is)\s+(bad|dangerous|harmful)\b',
            r'\bif\s+it\'?s\s+natural\b',
        ],
    }
    
    def detect(self, text: str) -> List[Tuple[LogicalFallacy, float]]:
        """Detect logical fallacies in text"""
        detected = []
        text_lower = text.lower()
        
        for fallacy, patterns in self.FALLACY_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    # Confidence based on pattern specificity
                    confidence = 0.7 + (len(pattern) / 100)  # Longer patterns = higher confidence
                    detected.append((fallacy, min(confidence, 0.95)))
                    break  # Only count each fallacy once
        
        return detected


class PropagandaDetector:
    """
    Detects propaganda techniques in text.
    Based on research from fact-checking organizations.
    """
    
    TECHNIQUE_PATTERNS = {
        PropagandaTechnique.LOADED_LANGUAGE: [
            r'\b(radical|extreme|dangerous|catastrophic|devastating|outrageous)\b',
            r'\b(evil|wicked|corrupt|sinister|nefarious)\b',
            r'\b(heroic|patriotic|freedom|liberty)\b.*\b(fight|battle|war)\b',
        ],
        PropagandaTechnique.NAME_CALLING: [
            r'\b(libtard|snowflake|nazi|fascist|communist|socialist)\b',
            r'\b(sheep|sheeple|shill|bot|troll)\b',
            r'\b(fake|phony|fraud|puppet)\b',
        ],
        PropagandaTechnique.EXAGGERATION: [
            r'\b(always|never|every|none|all|nobody|everybody)\b',
            r'\b(worst|best|biggest|smallest)\s+(ever|in\s+history)\b',
            r'\b(unprecedented|unbelievable|incredible|shocking)\b',
        ],
        PropagandaTechnique.DOUBT: [
            r'\bsome\s+(people|experts?|scientists?)\s+(say|claim|believe)\b',
            r'\bjust\s+asking\s+questions?\b',
            r'\bdo\s+your\s+own\s+research\b',
            r'\bwake\s+up\b',
        ],
        PropagandaTechnique.APPEAL_TO_FEAR: [
            r'\bthey\s+(want|are\s+coming|will)\b.*\b(destroy|take|kill)\b',
            r'\bif\s+we\s+don\'?t\s+act\s+now\b',
            r'\bour\s+(way\s+of\s+life|freedom|future)\s+is\s+(at\s+stake|threatened)\b',
        ],
        PropagandaTechnique.FLAG_WAVING: [
            r'\btrue\s+(american|patriot)\b',
            r'\bour\s+(country|nation|people)\b',
            r'\b(defend|protect)\s+(our|the)\s+(flag|country|freedom)\b',
        ],
        PropagandaTechnique.WHATABOUTISM: [
            r'\bwhat\s+about\b',
            r'\bbut\s+they\s+(also|did|do)\b',
            r'\byou\'?re\s+one\s+to\s+talk\b',
        ],
        PropagandaTechnique.BLACK_WHITE_FALLACY: [
            r'\byou\'?re\s+either\s+with\s+us\s+or\s+against\b',
            r'\bthere\'?s\s+no\s+middle\s+ground\b',
            r'\bpick\s+a\s+side\b',
        ],
        PropagandaTechnique.THOUGHT_TERMINATING_CLICHE: [
            r'\bit\s+is\s+what\s+it\s+is\b',
            r'\bdon\'?t\s+be\s+a\s+(sheep|follower)\b',
            r'\btime\s+will\s+tell\b',
            r'\bjust\s+trust\b',
        ],
    }
    
    def detect(self, text: str) -> List[Tuple[PropagandaTechnique, float]]:
        """Detect propaganda techniques in text"""
        detected = []
        text_lower = text.lower()
        
        for technique, patterns in self.TECHNIQUE_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    matches += 1
            
            if matches > 0:
                confidence = min(0.5 + matches * 0.15, 0.95)
                detected.append((technique, confidence))
        
        return detected


class BiasDetector:
    """
    Detects potential bias indicators in claims.
    """
    
    LEFT_INDICATORS = [
        'progressive', 'social justice', 'systemic racism', 'inequality',
        'climate crisis', 'universal healthcare', 'gun control', 'workers rights',
        'billionaires', 'corporations', 'capitalism bad'
    ]
    
    RIGHT_INDICATORS = [
        'traditional values', 'law and order', 'illegal immigrants', 'second amendment',
        'big government', 'socialism', 'communist', 'deep state', 'mainstream media',
        'freedom', 'liberty', 'patriot'
    ]
    
    SENSATIONALISM_INDICATORS = [
        'shocking', 'explosive', 'bombshell', 'breaking', 'you wont believe',
        'what they dont want you to know', 'secret revealed', 'exposed'
    ]
    
    CONSPIRACY_INDICATORS = [
        'they dont want you to know', 'cover up', 'the truth about', 'hidden agenda',
        'wake up', 'sheeple', 'global elite', 'new world order', 'deep state',
        'mainstream media wont tell you', 'censored', 'banned'
    ]
    
    PSEUDOSCIENCE_INDICATORS = [
        'big pharma', 'doctors dont want', 'natural cure', 'miracle treatment',
        'ancient secret', 'quantum', 'energy healing', 'toxins', 'detox',
        'suppressed research', 'alternative medicine'
    ]
    
    def detect(self, text: str) -> List[Tuple[BiasType, float]]:
        """Detect bias indicators in text"""
        text_lower = text.lower()
        detected = []
        
        # Count indicators
        left_count = sum(1 for ind in self.LEFT_INDICATORS if ind in text_lower)
        right_count = sum(1 for ind in self.RIGHT_INDICATORS if ind in text_lower)
        sensational_count = sum(1 for ind in self.SENSATIONALISM_INDICATORS if ind in text_lower)
        conspiracy_count = sum(1 for ind in self.CONSPIRACY_INDICATORS if ind in text_lower)
        pseudo_count = sum(1 for ind in self.PSEUDOSCIENCE_INDICATORS if ind in text_lower)
        
        if left_count >= 2:
            detected.append((BiasType.LEFT_BIAS, min(0.5 + left_count * 0.1, 0.9)))
        if right_count >= 2:
            detected.append((BiasType.RIGHT_BIAS, min(0.5 + right_count * 0.1, 0.9)))
        if sensational_count >= 1:
            detected.append((BiasType.SENSATIONALISM, min(0.6 + sensational_count * 0.15, 0.95)))
        if conspiracy_count >= 2:
            detected.append((BiasType.CONSPIRACY, min(0.6 + conspiracy_count * 0.12, 0.95)))
        if pseudo_count >= 2:
            detected.append((BiasType.PSEUDOSCIENCE, min(0.6 + pseudo_count * 0.12, 0.95)))
        
        if not detected:
            detected.append((BiasType.NEUTRAL, 0.7))
        
        return detected


class SentimentAnalyzer:
    """
    Analyzes sentiment and subjectivity of claims.
    """
    
    POSITIVE_WORDS = {
        'good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic',
        'beneficial', 'helpful', 'positive', 'success', 'improved', 'better',
        'effective', 'safe', 'proven', 'confirmed', 'verified', 'true'
    }
    
    NEGATIVE_WORDS = {
        'bad', 'terrible', 'awful', 'horrible', 'dangerous', 'harmful',
        'failed', 'worse', 'negative', 'disaster', 'crisis', 'threat',
        'false', 'fake', 'lie', 'hoax', 'scam', 'fraud', 'deadly'
    }
    
    SUBJECTIVE_WORDS = {
        'think', 'believe', 'feel', 'opinion', 'seems', 'appears',
        'probably', 'maybe', 'might', 'could', 'should', 'allegedly',
        'reportedly', 'supposedly', 'apparently', 'best', 'worst'
    }
    
    def analyze(self, text: str) -> Tuple[float, float]:
        """
        Returns (sentiment_score, subjectivity_score)
        sentiment: -1 (negative) to 1 (positive)
        subjectivity: 0 (objective) to 1 (subjective)
        """
        words = text.lower().split()
        word_count = len(words)
        
        if word_count == 0:
            return 0.0, 0.0
        
        positive_count = sum(1 for w in words if w in self.POSITIVE_WORDS)
        negative_count = sum(1 for w in words if w in self.NEGATIVE_WORDS)
        subjective_count = sum(1 for w in words if w in self.SUBJECTIVE_WORDS)
        
        # Sentiment score
        sentiment = (positive_count - negative_count) / max(positive_count + negative_count, 1)
        
        # Subjectivity score
        subjectivity = min(subjective_count / (word_count * 0.1), 1.0)
        
        return sentiment, subjectivity


class ClaimAnalyzer:
    """
    Master class that combines all NLP analysis.
    """
    
    def __init__(self):
        self.ner = NamedEntityRecognizer()
        self.fallacy_detector = LogicalFallacyDetector()
        self.propaganda_detector = PropagandaDetector()
        self.bias_detector = BiasDetector()
        self.sentiment_analyzer = SentimentAnalyzer()
    
    def analyze(self, claim: str) -> ClaimAnalysis:
        """Perform complete NLP analysis on a claim"""
        
        # Extract entities
        entities = self.ner.extract_entities(claim)
        
        # Extract numerical claims
        numerical_claims = self._extract_numerical_claims(claim, entities)
        
        # Extract temporal expressions
        temporal_expressions = self._extract_temporal_expressions(claim, entities)
        
        # Detect fallacies
        fallacies = self.fallacy_detector.detect(claim)
        
        # Detect propaganda
        propaganda = self.propaganda_detector.detect(claim)
        
        # Detect bias
        bias = self.bias_detector.detect(claim)
        
        # Analyze sentiment
        sentiment, subjectivity = self.sentiment_analyzer.analyze(claim)
        
        # Calculate complexity
        complexity = self._calculate_complexity(claim)
        
        # Calculate verifiability
        verifiability = self._calculate_verifiability(claim, entities)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(claim, entities)
        
        # Generate suggested searches
        suggested_searches = self._generate_searches(claim, entities, key_phrases)
        
        return ClaimAnalysis(
            original_claim=claim,
            entities=entities,
            numerical_claims=numerical_claims,
            temporal_expressions=temporal_expressions,
            detected_fallacies=fallacies,
            propaganda_techniques=propaganda,
            bias_indicators=bias,
            sentiment_score=sentiment,
            subjectivity_score=subjectivity,
            complexity_score=complexity,
            verifiability_score=verifiability,
            key_phrases=key_phrases,
            suggested_searches=suggested_searches
        )
    
    def _extract_numerical_claims(self, text: str, entities: List[ExtractedEntity]) -> List[Dict]:
        """Extract numerical claims for verification"""
        numerical = []
        
        for entity in entities:
            if entity.entity_type in [EntityType.NUMBER, EntityType.PERCENTAGE, EntityType.MONEY]:
                # Find context around the number
                start = max(0, entity.start_pos - 50)
                end = min(len(text), entity.end_pos + 50)
                context = text[start:end]
                
                numerical.append({
                    'value': entity.text,
                    'normalized': entity.normalized_value,
                    'type': entity.entity_type.value,
                    'context': context,
                    'position': entity.start_pos
                })
        
        return numerical
    
    def _extract_temporal_expressions(self, text: str, entities: List[ExtractedEntity]) -> List[Dict]:
        """Extract temporal expressions for timeline verification"""
        temporal = []
        
        for entity in entities:
            if entity.entity_type == EntityType.DATE:
                temporal.append({
                    'expression': entity.text,
                    'position': entity.start_pos
                })
        
        # Also look for relative time expressions
        relative_patterns = [
            (r'\blast\s+(year|month|week|decade)\b', 'relative_past'),
            (r'\b(\d+)\s+(years?|months?|days?)\s+ago\b', 'relative_past'),
            (r'\brecently\b', 'relative_recent'),
            (r'\bcurrently\b', 'present'),
            (r'\bhistorically\b', 'historical'),
        ]
        
        for pattern, time_type in relative_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                temporal.append({
                    'expression': match.group(0),
                    'type': time_type,
                    'position': match.start()
                })
        
        return temporal
    
    def _calculate_complexity(self, text: str) -> float:
        """Calculate claim complexity (0-1)"""
        words = text.split()
        word_count = len(words)
        
        # Factors: length, conjunctions, subclauses
        length_factor = min(word_count / 50, 1.0)
        
        conjunction_count = len(re.findall(r'\b(and|or|but|because|therefore|however|although)\b', text, re.I))
        conjunction_factor = min(conjunction_count / 5, 1.0)
        
        # Comma-separated clauses
        clause_count = text.count(',')
        clause_factor = min(clause_count / 4, 1.0)
        
        return (length_factor * 0.4 + conjunction_factor * 0.3 + clause_factor * 0.3)
    
    def _calculate_verifiability(self, text: str, entities: List[ExtractedEntity]) -> float:
        """Calculate how verifiable a claim is (0-1)"""
        score = 0.5  # Base score
        
        # More entities = more verifiable
        if entities:
            score += min(len(entities) * 0.05, 0.2)
        
        # Specific numbers are verifiable
        numbers = [e for e in entities if e.entity_type in [EntityType.NUMBER, EntityType.PERCENTAGE]]
        if numbers:
            score += 0.15
        
        # Dates make claims more verifiable
        dates = [e for e in entities if e.entity_type == EntityType.DATE]
        if dates:
            score += 0.1
        
        # Named entities (people, orgs) are verifiable
        named = [e for e in entities if e.entity_type in [EntityType.PERSON, EntityType.ORGANIZATION]]
        if named:
            score += 0.1
        
        # Vague language reduces verifiability
        vague_words = len(re.findall(r'\b(some|many|few|often|sometimes|usually|generally)\b', text, re.I))
        score -= vague_words * 0.05
        
        return max(0.1, min(0.95, score))
    
    def _extract_key_phrases(self, text: str, entities: List[ExtractedEntity]) -> List[str]:
        """Extract key phrases for search"""
        phrases = []
        
        # Add entity texts
        for entity in entities:
            if entity.entity_type in [EntityType.PERSON, EntityType.ORGANIZATION, EntityType.LOCATION]:
                phrases.append(entity.text)
        
        # Extract noun phrases (simple heuristic)
        # Look for adjective + noun patterns
        noun_phrase_pattern = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        for match in re.finditer(noun_phrase_pattern, text):
            phrases.append(match.group(0))
        
        return list(set(phrases))[:10]
    
    def _generate_searches(self, text: str, entities: List[ExtractedEntity], key_phrases: List[str]) -> List[str]:
        """Generate suggested search queries for verification"""
        searches = []
        
        # Basic claim search
        if len(text) < 100:
            searches.append(f'"{text[:50]}" fact check')
        
        # Entity-based searches
        for entity in entities[:3]:
            if entity.entity_type == EntityType.PERSON:
                searches.append(f'{entity.text} fact check')
            elif entity.entity_type == EntityType.ORGANIZATION:
                searches.append(f'{entity.text} official statement')
        
        # Key phrase searches
        for phrase in key_phrases[:2]:
            searches.append(f'{phrase} verified')
        
        # Number verification
        numbers = [e for e in entities if e.entity_type in [EntityType.NUMBER, EntityType.PERCENTAGE]]
        for num in numbers[:2]:
            searches.append(f'{num.text} statistics source')
        
        return list(set(searches))[:8]


__all__ = [
    'ClaimAnalyzer', 'ClaimAnalysis', 'ExtractedEntity', 'EntityType',
    'LogicalFallacy', 'PropagandaTechnique', 'BiasType',
    'NamedEntityRecognizer', 'LogicalFallacyDetector', 
    'PropagandaDetector', 'BiasDetector', 'SentimentAnalyzer'
]
