"""
Verity Temporal Reasoning Engine
================================
Time-aware fact-checking that understands historical context.

Features:
- Temporal claim detection
- Historical context awareness
- Time-sensitive truth evaluation
- Event timeline construction
- "When was this true?" analysis
"""

import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum


class TemporalType(Enum):
    """Types of temporal references"""
    ABSOLUTE = "absolute"  # Specific date: "January 1, 2020"
    RELATIVE = "relative"  # Relative time: "yesterday", "last year"
    RANGE = "range"        # Time range: "from 2019 to 2021"
    ONGOING = "ongoing"    # Continuous: "since 1990"
    HISTORICAL = "historical"  # Historical event: "during World War II"
    NONE = "none"          # No temporal reference


class TruthTemporality(Enum):
    """How truth varies over time"""
    ALWAYS_TRUE = "always_true"      # Immutable facts
    ALWAYS_FALSE = "always_false"    # Never true
    WAS_TRUE = "was_true"            # True in the past, not now
    IS_NOW_TRUE = "is_now_true"      # True now, wasn't before
    PERIODICALLY = "periodically"    # True at certain times
    CONTEXT_DEPENDENT = "context_dependent"  # Depends on context


@dataclass
class TemporalReference:
    """A detected temporal reference in a claim"""
    type: TemporalType
    original_text: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    confidence: float = 0.0
    is_approximate: bool = False


@dataclass
class TemporalContext:
    """Historical context for a claim"""
    claim_date: Optional[datetime] = None
    references: List[TemporalReference] = field(default_factory=list)
    historical_period: str = ""
    truth_temporality: TruthTemporality = TruthTemporality.CONTEXT_DEPENDENT
    relevant_events: List[str] = field(default_factory=list)


@dataclass
class TimelineEvent:
    """An event in a timeline"""
    date: datetime
    description: str
    source: str
    relevance_score: float = 0.0
    changes_truth_value: bool = False


class TemporalExtractor:
    """
    Extract temporal references from text.
    """
    
    MONTH_MAP = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6, 'july': 7, 'jul': 7,
        'august': 8, 'aug': 8, 'september': 9, 'sep': 9, 'sept': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    RELATIVE_PATTERNS = {
        r'\byesterday\b': -1,
        r'\btoday\b': 0,
        r'\btomorrow\b': 1,
        r'\blast\s+week\b': -7,
        r'\bthis\s+week\b': 0,
        r'\bnext\s+week\b': 7,
        r'\blast\s+month\b': -30,
        r'\bthis\s+month\b': 0,
        r'\bnext\s+month\b': 30,
        r'\blast\s+year\b': -365,
        r'\bthis\s+year\b': 0,
        r'\bnext\s+year\b': 365,
    }
    
    HISTORICAL_PERIODS = {
        r'\bduring\s+world\s+war\s+(?:one|i|1)\b': (datetime(1914, 7, 28), datetime(1918, 11, 11)),
        r'\bduring\s+world\s+war\s+(?:two|ii|2)\b': (datetime(1939, 9, 1), datetime(1945, 9, 2)),
        r'\bduring\s+the\s+cold\s+war\b': (datetime(1947, 1, 1), datetime(1991, 12, 26)),
        r'\bduring\s+the\s+great\s+depression\b': (datetime(1929, 10, 29), datetime(1939, 1, 1)),
        r'\bduring\s+the\s+civil\s+war\b': (datetime(1861, 4, 12), datetime(1865, 5, 9)),
        r'\bin\s+the\s+(?:19)?90s\b': (datetime(1990, 1, 1), datetime(1999, 12, 31)),
        r'\bin\s+the\s+(?:19)?80s\b': (datetime(1980, 1, 1), datetime(1989, 12, 31)),
        r'\bin\s+the\s+(?:19)?70s\b': (datetime(1970, 1, 1), datetime(1979, 12, 31)),
        r'\bin\s+the\s+(?:20)?00s\b': (datetime(2000, 1, 1), datetime(2009, 12, 31)),
        r'\bin\s+the\s+(?:20)?10s\b': (datetime(2010, 1, 1), datetime(2019, 12, 31)),
        r'\bin\s+the\s+(?:20)?20s\b': (datetime(2020, 1, 1), datetime(2029, 12, 31)),
    }
    
    @classmethod
    def extract_all(cls, text: str) -> List[TemporalReference]:
        """Extract all temporal references from text"""
        references = []
        text_lower = text.lower()
        
        # Check absolute dates
        references.extend(cls._extract_absolute_dates(text))
        
        # Check relative references
        references.extend(cls._extract_relative_dates(text_lower))
        
        # Check historical periods
        references.extend(cls._extract_historical_periods(text_lower))
        
        # Check ranges
        references.extend(cls._extract_date_ranges(text))
        
        # Check ongoing references
        references.extend(cls._extract_ongoing_references(text_lower))
        
        return references
    
    @classmethod
    def _extract_absolute_dates(cls, text: str) -> List[TemporalReference]:
        """Extract absolute dates"""
        references = []
        
        # Pattern: "January 15, 2020" or "January 15 2020"
        pattern1 = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{1,2}),?\s*(\d{4})\b'
        for match in re.finditer(pattern1, text, re.IGNORECASE):
            month = cls.MONTH_MAP.get(match.group(1).lower(), 1)
            day = int(match.group(2))
            year = int(match.group(3))
            
            try:
                date = datetime(year, month, day)
                references.append(TemporalReference(
                    type=TemporalType.ABSOLUTE,
                    original_text=match.group(0),
                    start_date=date,
                    end_date=date,
                    confidence=0.95
                ))
            except ValueError:
                pass
        
        # Pattern: "15/01/2020" or "01-15-2020"
        pattern2 = r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b'
        for match in re.finditer(pattern2, text):
            try:
                # Try both interpretations
                day_first = datetime(int(match.group(3)), int(match.group(2)), int(match.group(1)))
                references.append(TemporalReference(
                    type=TemporalType.ABSOLUTE,
                    original_text=match.group(0),
                    start_date=day_first,
                    end_date=day_first,
                    confidence=0.7,  # Lower confidence due to ambiguity
                    is_approximate=True
                ))
            except ValueError:
                try:
                    month_first = datetime(int(match.group(3)), int(match.group(1)), int(match.group(2)))
                    references.append(TemporalReference(
                        type=TemporalType.ABSOLUTE,
                        original_text=match.group(0),
                        start_date=month_first,
                        end_date=month_first,
                        confidence=0.7,
                        is_approximate=True
                    ))
                except ValueError:
                    pass
        
        # Pattern: just year "in 2020" or "2020"
        pattern3 = r'\b(in\s+)?(\d{4})\b'
        for match in re.finditer(pattern3, text):
            year = int(match.group(2))
            if 1800 <= year <= 2100:
                references.append(TemporalReference(
                    type=TemporalType.ABSOLUTE,
                    original_text=match.group(0),
                    start_date=datetime(year, 1, 1),
                    end_date=datetime(year, 12, 31),
                    confidence=0.8,
                    is_approximate=True
                ))
        
        return references
    
    @classmethod
    def _extract_relative_dates(cls, text: str) -> List[TemporalReference]:
        """Extract relative time references"""
        references = []
        now = datetime.now()
        
        for pattern, days_offset in cls.RELATIVE_PATTERNS.items():
            match = re.search(pattern, text)
            if match:
                date = now + timedelta(days=days_offset)
                references.append(TemporalReference(
                    type=TemporalType.RELATIVE,
                    original_text=match.group(0),
                    start_date=date.replace(hour=0, minute=0, second=0),
                    end_date=date.replace(hour=23, minute=59, second=59),
                    confidence=0.85
                ))
        
        # "X days/weeks/months/years ago"
        ago_pattern = r'(\d+)\s+(day|week|month|year)s?\s+ago'
        for match in re.finditer(ago_pattern, text):
            amount = int(match.group(1))
            unit = match.group(2)
            
            if unit == 'day':
                offset = timedelta(days=amount)
            elif unit == 'week':
                offset = timedelta(weeks=amount)
            elif unit == 'month':
                offset = timedelta(days=amount * 30)
            elif unit == 'year':
                offset = timedelta(days=amount * 365)
            
            date = now - offset
            references.append(TemporalReference(
                type=TemporalType.RELATIVE,
                original_text=match.group(0),
                start_date=date,
                end_date=date,
                confidence=0.8,
                is_approximate=True
            ))
        
        return references
    
    @classmethod
    def _extract_historical_periods(cls, text: str) -> List[TemporalReference]:
        """Extract historical period references"""
        references = []
        
        for pattern, (start, end) in cls.HISTORICAL_PERIODS.items():
            match = re.search(pattern, text)
            if match:
                references.append(TemporalReference(
                    type=TemporalType.HISTORICAL,
                    original_text=match.group(0),
                    start_date=start,
                    end_date=end,
                    confidence=0.9
                ))
        
        return references
    
    @classmethod
    def _extract_date_ranges(cls, text: str) -> List[TemporalReference]:
        """Extract date ranges"""
        references = []
        
        # "from 2019 to 2021" or "between 2019 and 2021"
        pattern = r'\b(?:from|between)\s+(\d{4})\s+(?:to|and)\s+(\d{4})\b'
        for match in re.finditer(pattern, text, re.IGNORECASE):
            start_year = int(match.group(1))
            end_year = int(match.group(2))
            
            if 1800 <= start_year <= 2100 and 1800 <= end_year <= 2100:
                references.append(TemporalReference(
                    type=TemporalType.RANGE,
                    original_text=match.group(0),
                    start_date=datetime(start_year, 1, 1),
                    end_date=datetime(end_year, 12, 31),
                    confidence=0.9
                ))
        
        return references
    
    @classmethod
    def _extract_ongoing_references(cls, text: str) -> List[TemporalReference]:
        """Extract ongoing time references"""
        references = []
        
        # "since 1990"
        since_pattern = r'\bsince\s+(\d{4})\b'
        for match in re.finditer(since_pattern, text, re.IGNORECASE):
            year = int(match.group(1))
            if 1800 <= year <= 2100:
                references.append(TemporalReference(
                    type=TemporalType.ONGOING,
                    original_text=match.group(0),
                    start_date=datetime(year, 1, 1),
                    end_date=datetime.now(),
                    confidence=0.85
                ))
        
        return references


class TemporalReasoningEngine:
    """
    Engine for temporal reasoning in fact-checking.
    
    Handles:
    - Claims that were true in the past but not now
    - Claims about future events
    - Claims that require historical context
    - Time-sensitive truth evaluation
    """
    
    # Claims that change over time
    TEMPORAL_INDICATORS = {
        "current": TruthTemporality.IS_NOW_TRUE,
        "currently": TruthTemporality.IS_NOW_TRUE,
        "now": TruthTemporality.IS_NOW_TRUE,
        "today": TruthTemporality.IS_NOW_TRUE,
        "was": TruthTemporality.WAS_TRUE,
        "were": TruthTemporality.WAS_TRUE,
        "used to": TruthTemporality.WAS_TRUE,
        "former": TruthTemporality.WAS_TRUE,
        "previously": TruthTemporality.WAS_TRUE,
        "always": TruthTemporality.ALWAYS_TRUE,
        "never": TruthTemporality.ALWAYS_FALSE,
        "every year": TruthTemporality.PERIODICALLY,
        "annually": TruthTemporality.PERIODICALLY,
    }
    
    # Types of claims that inherently change
    TIME_SENSITIVE_PATTERNS = [
        (r'\b(?:is|are)\s+the\s+(?:president|prime\s+minister|ceo|leader)\b', "leadership"),
        (r'\b(?:population|gdp|economy|temperature)\s+(?:is|are)\b', "statistics"),
        (r'\b(?:world\s+record|champion|winner)\b', "records"),
        (r'\b(?:latest|current|newest)\b', "current_state"),
        (r'\b(?:price|cost|rate|value)\s+(?:is|are)\b', "economics"),
    ]
    
    def __init__(self):
        self.extractor = TemporalExtractor()
        self.timeline_cache: Dict[str, List[TimelineEvent]] = {}
    
    def analyze_claim(self, claim: str) -> TemporalContext:
        """
        Analyze temporal aspects of a claim.
        """
        context = TemporalContext()
        
        # Extract temporal references
        context.references = self.extractor.extract_all(claim)
        
        # Determine truth temporality
        context.truth_temporality = self._determine_temporality(claim)
        
        # Identify relevant historical period
        context.historical_period = self._identify_historical_period(claim, context.references)
        
        # Note time-sensitive aspects
        context.relevant_events = self._identify_time_sensitivity(claim)
        
        return context
    
    def _determine_temporality(self, claim: str) -> TruthTemporality:
        """Determine how truth varies over time for this claim"""
        claim_lower = claim.lower()
        
        # Check temporal indicators
        for indicator, temporality in self.TEMPORAL_INDICATORS.items():
            if indicator in claim_lower:
                return temporality
        
        # Check time-sensitive patterns
        for pattern, _ in self.TIME_SENSITIVE_PATTERNS:
            if re.search(pattern, claim_lower):
                return TruthTemporality.CONTEXT_DEPENDENT
        
        return TruthTemporality.CONTEXT_DEPENDENT
    
    def _identify_historical_period(self, claim: str, references: List[TemporalReference]) -> str:
        """Identify relevant historical period"""
        for ref in references:
            if ref.type == TemporalType.HISTORICAL:
                return ref.original_text
        
        # Check if claim mentions specific dates/years
        for ref in references:
            if ref.start_date:
                year = ref.start_date.year
                if year < 1900:
                    return f"Pre-20th century ({year})"
                elif year < 1950:
                    return f"Early 20th century ({year})"
                elif year < 2000:
                    return f"Late 20th century ({year})"
                else:
                    return f"21st century ({year})"
        
        return "Contemporary"
    
    def _identify_time_sensitivity(self, claim: str) -> List[str]:
        """Identify aspects that make the claim time-sensitive"""
        sensitivities = []
        claim_lower = claim.lower()
        
        for pattern, aspect in self.TIME_SENSITIVE_PATTERNS:
            if re.search(pattern, claim_lower):
                sensitivities.append(aspect)
        
        return sensitivities
    
    def evaluate_at_time(
        self,
        claim: str,
        target_time: datetime,
        current_verdict: str,
        current_confidence: float
    ) -> Dict:
        """
        Evaluate what the verdict would be at a specific time.
        
        Returns assessment of claim validity at target time.
        """
        context = self.analyze_claim(claim)
        
        result = {
            "target_time": target_time.isoformat(),
            "temporal_context": {
                "temporality": context.truth_temporality.value,
                "historical_period": context.historical_period,
                "time_sensitivities": context.relevant_events
            },
            "original_verdict": current_verdict,
            "time_adjusted_verdict": current_verdict,
            "confidence_adjustment": 0.0,
            "explanation": ""
        }
        
        # If claim has no temporal component, verdict doesn't change
        if context.truth_temporality == TruthTemporality.ALWAYS_TRUE:
            result["explanation"] = "This claim appears to be a timeless fact."
            return result
        
        if context.truth_temporality == TruthTemporality.ALWAYS_FALSE:
            result["explanation"] = "This claim appears to be factually incorrect regardless of time."
            return result
        
        # Check if target time is within any referenced time period
        in_referenced_period = False
        for ref in context.references:
            if ref.start_date and ref.end_date:
                if ref.start_date <= target_time <= ref.end_date:
                    in_referenced_period = True
                    break
        
        # Adjust verdict based on temporality
        if context.truth_temporality == TruthTemporality.WAS_TRUE:
            if target_time < datetime.now():
                result["explanation"] = f"This claim refers to a past state. At {target_time.year}, it may have been accurate."
                result["confidence_adjustment"] = 0.1
            else:
                result["time_adjusted_verdict"] = self._reverse_verdict(current_verdict)
                result["explanation"] = "This claim about past events would not be applicable to future dates."
                result["confidence_adjustment"] = -0.3
        
        elif context.truth_temporality == TruthTemporality.IS_NOW_TRUE:
            if target_time < datetime.now() - timedelta(days=365):
                result["time_adjusted_verdict"] = "Unverified"
                result["explanation"] = "This claim about current state may not have been true at that historical time."
                result["confidence_adjustment"] = -0.2
        
        elif context.truth_temporality == TruthTemporality.CONTEXT_DEPENDENT:
            if context.relevant_events:
                result["explanation"] = f"This claim is time-sensitive ({', '.join(context.relevant_events)}). Verdict may vary."
                result["confidence_adjustment"] = -0.1
        
        # Adjust confidence
        result["adjusted_confidence"] = max(0, min(1, current_confidence + result["confidence_adjustment"]))
        
        return result
    
    def _reverse_verdict(self, verdict: str) -> str:
        """Reverse a verdict"""
        verdict_map = {
            "True": "False",
            "FALSE": "True",
            "Mostly True": "Mostly False",
            "Mostly False": "Mostly True",
        }
        return verdict_map.get(verdict, "Unverified")
    
    def build_timeline(self, claim: str, events: List[Dict]) -> List[TimelineEvent]:
        """
        Build a timeline of relevant events for a claim.
        
        events: List of dicts with 'date', 'description', 'source'
        """
        context = self.analyze_claim(claim)
        timeline = []
        
        for event in events:
            try:
                if isinstance(event.get('date'), str):
                    date = datetime.fromisoformat(event['date'])
                else:
                    date = event.get('date', datetime.now())
                
                relevance = self._calculate_event_relevance(claim, event['description'], context)
                
                timeline.append(TimelineEvent(
                    date=date,
                    description=event.get('description', ''),
                    source=event.get('source', ''),
                    relevance_score=relevance,
                    changes_truth_value=self._event_changes_truth(claim, event['description'])
                ))
            except (ValueError, TypeError):
                continue
        
        # Sort by date
        timeline.sort(key=lambda x: x.date)
        
        return timeline
    
    def _calculate_event_relevance(self, claim: str, event_desc: str, context: TemporalContext) -> float:
        """Calculate how relevant an event is to a claim"""
        # Simple word overlap for now
        claim_words = set(claim.lower().split())
        event_words = set(event_desc.lower().split())
        
        overlap = len(claim_words & event_words)
        total = len(claim_words | event_words)
        
        return overlap / total if total > 0 else 0.0
    
    def _event_changes_truth(self, claim: str, event_desc: str) -> bool:
        """Check if an event might change the truth value of a claim"""
        change_indicators = [
            'changed', 'new', 'replaced', 'ended', 'started', 'began',
            'stopped', 'announced', 'elected', 'appointed', 'resigned',
            'died', 'founded', 'dissolved', 'merged', 'acquired'
        ]
        
        event_lower = event_desc.lower()
        return any(indicator in event_lower for indicator in change_indicators)
    
    def get_temporal_search_queries(self, claim: str) -> List[str]:
        """
        Generate time-aware search queries for a claim.
        """
        context = self.analyze_claim(claim)
        queries = [claim]  # Original claim
        
        # Add temporal qualifiers
        for ref in context.references:
            if ref.start_date:
                year = ref.start_date.year
                queries.append(f"{claim} {year}")
                queries.append(f"history of {claim}")
        
        # Add queries for time-sensitive aspects
        if context.relevant_events:
            for sensitivity in context.relevant_events:
                if sensitivity == "leadership":
                    queries.append(f"list of {claim}")
                    queries.append(f"history {claim}")
                elif sensitivity == "statistics":
                    queries.append(f"{claim} historical data")
                    queries.append(f"{claim} over time")
        
        return list(set(queries))


__all__ = [
    'TemporalReasoningEngine', 'TemporalExtractor', 'TemporalContext',
    'TemporalReference', 'TemporalType', 'TruthTemporality', 'TimelineEvent'
]
