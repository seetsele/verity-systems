"""
Verity Intelligence Engine - Part 3: Evidence Graph Builder
============================================================
Builds a knowledge graph of evidence relationships.

THE EVIDENCE GRAPH:
==================
- Nodes: Claims, Evidence, Sources, Facts
- Edges: Supports, Refutes, Cites, Related-To
- Enables: Citation chains, corroboration detection, contradiction identification

This is CRITICAL for:
1. Finding citation chains (A cites B which cites C)
2. Detecting circular references (A cites B cites A)
3. Identifying independent corroboration
4. Spotting contradictions between sources
5. Building trust networks
"""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from collections import defaultdict
import hashlib

from verity_intelligence_engine import (
    Evidence, SubClaim, SourceTier, get_source_tier
)


@dataclass
class GraphNode:
    """A node in the evidence graph"""
    id: str
    node_type: str  # 'claim', 'evidence', 'source', 'fact'
    content: str
    metadata: Dict = field(default_factory=dict)
    connections: List[str] = field(default_factory=list)


@dataclass
class GraphEdge:
    """An edge connecting two nodes"""
    source_id: str
    target_id: str
    edge_type: str  # 'supports', 'refutes', 'cites', 'related'
    weight: float = 1.0
    metadata: Dict = field(default_factory=dict)


class EvidenceGraphBuilder:
    """
    Builds a knowledge graph from evidence.
    
    This allows us to:
    1. Trace citation chains
    2. Find corroborating evidence
    3. Detect contradictions
    4. Calculate trust scores
    5. Identify echo chambers
    """
    
    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self.source_trust_scores: Dict[str, float] = {}
    
    def _generate_id(self, content: str, prefix: str = "node") -> str:
        """Generate unique ID for a node"""
        hash_val = hashlib.md5(content.encode()).hexdigest()[:8]
        return f"{prefix}_{hash_val}"
    
    def add_claim(self, claim: str, sub_claims: List[SubClaim] = None) -> str:
        """Add a claim node to the graph"""
        claim_id = self._generate_id(claim, "claim")
        
        self.nodes[claim_id] = GraphNode(
            id=claim_id,
            node_type='claim',
            content=claim,
            metadata={'sub_claims': len(sub_claims or [])}
        )
        
        # Add sub-claims as related nodes
        if sub_claims:
            for sc in sub_claims:
                sub_id = self._generate_id(sc.sub_claim, "subclaim")
                self.nodes[sub_id] = GraphNode(
                    id=sub_id,
                    node_type='sub_claim',
                    content=sc.sub_claim,
                    metadata={'claim_type': sc.claim_type.value}
                )
                self.edges.append(GraphEdge(
                    source_id=claim_id,
                    target_id=sub_id,
                    edge_type='contains'
                ))
        
        return claim_id
    
    def add_evidence(self, evidence: Evidence, claim_id: str) -> str:
        """Add evidence node and connect to claim"""
        evidence_id = self._generate_id(evidence.content, "evidence")
        
        self.nodes[evidence_id] = GraphNode(
            id=evidence_id,
            node_type='evidence',
            content=evidence.content[:500],  # Truncate for storage
            metadata={
                'source': evidence.source,
                'url': evidence.url,
                'tier': evidence.source_tier.name,
                'confidence': evidence.confidence,
                'timestamp': evidence.timestamp.isoformat()
            }
        )
        
        # Connect to claim
        edge_type = 'supports' if evidence.supports_claim else 'refutes'
        self.edges.append(GraphEdge(
            source_id=evidence_id,
            target_id=claim_id,
            edge_type=edge_type,
            weight=evidence.confidence
        ))
        
        # Add source node if new
        source_id = self._generate_id(evidence.source, "source")
        if source_id not in self.nodes:
            self.nodes[source_id] = GraphNode(
                id=source_id,
                node_type='source',
                content=evidence.source,
                metadata={
                    'tier': evidence.source_tier.name,
                    'trust_score': self._calculate_source_trust(evidence.source_tier)
                }
            )
        
        # Connect evidence to source
        self.edges.append(GraphEdge(
            source_id=source_id,
            target_id=evidence_id,
            edge_type='provides'
        ))
        
        return evidence_id
    
    def _calculate_source_trust(self, tier: SourceTier) -> float:
        """Calculate trust score for a source tier"""
        tier_trust = {
            SourceTier.TIER_1_AUTHORITATIVE: 0.95,
            SourceTier.TIER_2_REPUTABLE: 0.75,
            SourceTier.TIER_3_GENERAL: 0.50,
            SourceTier.TIER_4_UNCERTAIN: 0.25,
        }
        return tier_trust.get(tier, 0.3)
    
    def find_citation_chains(self, evidence_id: str, max_depth: int = 5) -> List[List[str]]:
        """
        Find chains of citations from an evidence node.
        
        Example: PaperA cites PaperB which cites PaperC
        Returns: [['PaperA', 'PaperB', 'PaperC']]
        """
        chains = []
        visited = set()
        
        def dfs(node_id: str, current_chain: List[str], depth: int):
            if depth > max_depth or node_id in visited:
                if len(current_chain) > 1:
                    chains.append(current_chain.copy())
                return
            
            visited.add(node_id)
            current_chain.append(node_id)
            
            # Find citation edges
            cite_edges = [e for e in self.edges 
                        if e.source_id == node_id and e.edge_type == 'cites']
            
            if not cite_edges:
                if len(current_chain) > 1:
                    chains.append(current_chain.copy())
            else:
                for edge in cite_edges:
                    dfs(edge.target_id, current_chain, depth + 1)
            
            current_chain.pop()
            visited.remove(node_id)
        
        dfs(evidence_id, [], 0)
        return chains
    
    def detect_circular_references(self) -> List[List[str]]:
        """
        Detect circular citation patterns.
        
        Circular references can indicate:
        - Self-reinforcing echo chambers
        - Questionable sourcing
        - Need for original source verification
        """
        circular = []
        
        for node_id in self.nodes:
            visited = set()
            stack = [(node_id, [node_id])]
            
            while stack:
                current, path = stack.pop()
                
                cite_edges = [e for e in self.edges 
                             if e.source_id == current and e.edge_type == 'cites']
                
                for edge in cite_edges:
                    if edge.target_id == node_id:
                        # Found cycle back to start
                        circular.append(path + [edge.target_id])
                    elif edge.target_id not in visited:
                        visited.add(edge.target_id)
                        stack.append((edge.target_id, path + [edge.target_id]))
        
        return circular
    
    def find_independent_corroboration(self, claim_id: str) -> List[List[str]]:
        """
        Find evidence that supports the claim from INDEPENDENT sources.
        
        Independence = No citation relationship between sources.
        High independent corroboration = HIGH CONFIDENCE.
        """
        # Get all supporting evidence
        supporting = [e for e in self.edges 
                     if e.target_id == claim_id and e.edge_type == 'supports']
        
        if len(supporting) < 2:
            return []
        
        # Build source dependency graph
        source_deps = defaultdict(set)
        for edge in self.edges:
            if edge.edge_type == 'cites':
                # Find sources for both nodes
                source_a = self._get_source_for_evidence(edge.source_id)
                source_b = self._get_source_for_evidence(edge.target_id)
                if source_a and source_b:
                    source_deps[source_a].add(source_b)
        
        # Find independent groups
        independent_groups = []
        processed = set()
        
        for edge in supporting:
            evidence_source = self._get_source_for_evidence(edge.source_id)
            if evidence_source in processed:
                continue
            
            # Find all dependent sources
            dependent_sources = self._get_all_dependencies(evidence_source, source_deps)
            processed.add(evidence_source)
            processed.update(dependent_sources)
            
            independent_groups.append([evidence_source] + list(dependent_sources))
        
        return independent_groups
    
    def _get_source_for_evidence(self, evidence_id: str) -> Optional[str]:
        """Get the source node ID for an evidence node"""
        for edge in self.edges:
            if edge.target_id == evidence_id and edge.edge_type == 'provides':
                return edge.source_id
        return None
    
    def _get_all_dependencies(self, source_id: str, deps: Dict[str, Set[str]]) -> Set[str]:
        """Get all transitive dependencies"""
        result = set()
        stack = list(deps.get(source_id, set()))
        
        while stack:
            current = stack.pop()
            if current not in result:
                result.add(current)
                stack.extend(deps.get(current, set()))
        
        return result
    
    def detect_contradictions(self, claim_id: str) -> List[Dict]:
        """
        Find contradictions between evidence pieces.
        
        Contradiction = Same claim, opposite stance, high-tier sources.
        """
        contradictions = []
        
        supporting = [(e.source_id, e.weight) for e in self.edges 
                     if e.target_id == claim_id and e.edge_type == 'supports']
        refuting = [(e.source_id, e.weight) for e in self.edges 
                   if e.target_id == claim_id and e.edge_type == 'refutes']
        
        # Check for high-weight contradictions
        for sup_id, sup_weight in supporting:
            for ref_id, ref_weight in refuting:
                if sup_weight >= 0.7 and ref_weight >= 0.7:
                    sup_node = self.nodes.get(sup_id)
                    ref_node = self.nodes.get(ref_id)
                    
                    if sup_node and ref_node:
                        contradictions.append({
                            'supporting': {
                                'id': sup_id,
                                'source': sup_node.metadata.get('source'),
                                'confidence': sup_weight
                            },
                            'refuting': {
                                'id': ref_id,
                                'source': ref_node.metadata.get('source'),
                                'confidence': ref_weight
                            },
                            'severity': (sup_weight + ref_weight) / 2
                        })
        
        # Sort by severity
        contradictions.sort(key=lambda x: x['severity'], reverse=True)
        return contradictions
    
    def calculate_evidence_network_strength(self, claim_id: str) -> Dict:
        """
        Calculate the overall strength of the evidence network.
        
        Returns metrics about the evidence supporting/refuting the claim.
        """
        supporting = [e for e in self.edges 
                     if e.target_id == claim_id and e.edge_type == 'supports']
        refuting = [e for e in self.edges 
                   if e.target_id == claim_id and e.edge_type == 'refutes']
        
        # Calculate tier distribution
        def get_tier_distribution(evidence_edges):
            tiers = defaultdict(int)
            for e in evidence_edges:
                node = self.nodes.get(e.source_id)
                if node:
                    tier = node.metadata.get('tier', 'TIER_4_UNCERTAIN')
                    tiers[tier] += 1
            return dict(tiers)
        
        # Check for independent corroboration
        independent_groups = self.find_independent_corroboration(claim_id)
        
        # Check for contradictions
        contradictions = self.detect_contradictions(claim_id)
        
        return {
            'total_supporting': len(supporting),
            'total_refuting': len(refuting),
            'supporting_tiers': get_tier_distribution(supporting),
            'refuting_tiers': get_tier_distribution(refuting),
            'independent_corroboration_groups': len(independent_groups),
            'high_severity_contradictions': len([c for c in contradictions if c['severity'] >= 0.8]),
            'network_confidence': self._calculate_network_confidence(
                supporting, refuting, independent_groups, contradictions
            )
        }
    
    def _calculate_network_confidence(
        self,
        supporting: List[GraphEdge],
        refuting: List[GraphEdge],
        independent_groups: List[List[str]],
        contradictions: List[Dict]
    ) -> float:
        """Calculate confidence based on evidence network structure"""
        if not supporting and not refuting:
            return 0.5
        
        # Base score from support ratio
        total = len(supporting) + len(refuting)
        base_score = len(supporting) / total if total > 0 else 0.5
        
        # Bonus for independent corroboration
        independence_bonus = min(len(independent_groups) * 0.05, 0.2)
        
        # Penalty for contradictions
        contradiction_penalty = min(len(contradictions) * 0.08, 0.25)
        
        # Calculate final
        confidence = base_score + independence_bonus - contradiction_penalty
        return max(0.1, min(0.95, confidence))
    
    def export_graph(self) -> Dict:
        """Export graph for visualization or storage"""
        return {
            'nodes': [
                {
                    'id': n.id,
                    'type': n.node_type,
                    'content': n.content[:100],  # Truncate
                    'metadata': n.metadata
                }
                for n in self.nodes.values()
            ],
            'edges': [
                {
                    'source': e.source_id,
                    'target': e.target_id,
                    'type': e.edge_type,
                    'weight': e.weight
                }
                for e in self.edges
            ],
            'statistics': {
                'total_nodes': len(self.nodes),
                'total_edges': len(self.edges),
                'node_types': defaultdict(int, {
                    n.node_type: 1 for n in self.nodes.values()
                })
            }
        }


class TrustNetworkAnalyzer:
    """
    Analyzes trust relationships between sources.
    
    This helps us identify:
    - Highly trusted source clusters
    - Potentially biased source networks
    - Echo chambers
    - Information silos
    """
    
    def __init__(self, graph: EvidenceGraphBuilder):
        self.graph = graph
    
    def calculate_source_pagerank(self, damping: float = 0.85, iterations: int = 20) -> Dict[str, float]:
        """
        Calculate PageRank-style trust scores for sources.
        
        Sources cited by other trusted sources get higher scores.
        """
        # Get all source nodes
        source_nodes = [n.id for n in self.graph.nodes.values() if n.node_type == 'source']
        
        if not source_nodes:
            return {}
        
        # Initialize scores
        n = len(source_nodes)
        scores = {s: 1.0 / n for s in source_nodes}
        
        # Build citation matrix between sources
        citations = defaultdict(list)
        for edge in self.graph.edges:
            if edge.edge_type == 'cites':
                source_a = self.graph._get_source_for_evidence(edge.source_id)
                source_b = self.graph._get_source_for_evidence(edge.target_id)
                if source_a and source_b and source_a != source_b:
                    citations[source_a].append(source_b)
        
        # Iterate PageRank
        for _ in range(iterations):
            new_scores = {}
            for source in source_nodes:
                # Sum of incoming citations weighted by citing source's score
                incoming_score = sum(
                    scores.get(citing, 0) / len(citations.get(citing, [1]))
                    for citing, cited_list in citations.items()
                    if source in cited_list
                )
                new_scores[source] = (1 - damping) / n + damping * incoming_score
            
            scores = new_scores
        
        return scores
    
    def detect_echo_chambers(self, min_cluster_size: int = 3) -> List[Set[str]]:
        """
        Detect clusters of sources that primarily cite each other.
        
        Echo chambers can indicate:
        - Potential bias
        - Need for diverse sources
        - Information bubbles
        """
        # Build undirected citation graph
        connections = defaultdict(set)
        for edge in self.graph.edges:
            if edge.edge_type == 'cites':
                source_a = self.graph._get_source_for_evidence(edge.source_id)
                source_b = self.graph._get_source_for_evidence(edge.target_id)
                if source_a and source_b:
                    connections[source_a].add(source_b)
                    connections[source_b].add(source_a)
        
        # Find connected components (simple clustering)
        visited = set()
        clusters = []
        
        for source in connections:
            if source in visited:
                continue
            
            # BFS to find cluster
            cluster = set()
            queue = [source]
            
            while queue:
                current = queue.pop(0)
                if current in visited:
                    continue
                
                visited.add(current)
                cluster.add(current)
                
                for neighbor in connections[current]:
                    if neighbor not in visited:
                        queue.append(neighbor)
            
            if len(cluster) >= min_cluster_size:
                clusters.append(cluster)
        
        return clusters


__all__ = ['EvidenceGraphBuilder', 'TrustNetworkAnalyzer', 'GraphNode', 'GraphEdge']
