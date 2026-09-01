import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class EvidenceNode:
    def __init__(
        self,
        node_id: str,
        hypothesis_id: str,
        finding: str,
        source_analysis: str,
        supporting_metrics: Dict[str, Any],
        data_quality_score: float = 1.0,
        limitations: Optional[List[str]] = None,
        confidence: str = "HIGH"
    ):
        self.node_id = node_id
        self.hypothesis_id = hypothesis_id
        self.finding = finding
        self.source_analysis = source_analysis
        self.supporting_metrics = supporting_metrics
        self.data_quality_score = data_quality_score
        self.limitations = limitations or []
        self.confidence = confidence

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "hypothesis_id": self.hypothesis_id,
            "finding": self.finding,
            "source_analysis": self.source_analysis,
            "supporting_metrics": self.supporting_metrics,
            "data_quality_score": self.data_quality_score,
            "limitations": self.limitations,
            "confidence": self.confidence
        }

class EvidenceGraph:
    """Maintains structured relationship between Question -> Hypothesis -> Analysis -> Evidence -> Conclusion."""

    def __init__(self, question: str):
        self.question = question
        self.nodes: List[EvidenceNode] = []
        self.contradictions: List[Dict[str, Any]] = []

    def add_evidence(
        self,
        hypothesis_id: str,
        finding: str,
        source_analysis: str,
        supporting_metrics: Dict[str, Any],
        data_quality_score: float = 1.0,
        limitations: Optional[List[str]] = None,
        confidence: str = "HIGH"
    ) -> EvidenceNode:
        node_id = f"ev_node_{len(self.nodes) + 1}"
        node = EvidenceNode(
            node_id=node_id,
            hypothesis_id=hypothesis_id,
            finding=finding,
            source_analysis=source_analysis,
            supporting_metrics=supporting_metrics,
            data_quality_score=data_quality_score,
            limitations=limitations,
            confidence=confidence
        )
        self.nodes.append(node)
        self._check_for_contradictions(node)
        return node

    def _check_for_contradictions(self, new_node: EvidenceNode):
        """Scans existing evidence nodes for conflicting findings or metrics."""
        for existing in self.nodes[:-1]:
            # Detect contradiction if same target metric yields opposing trends or high variance conflict
            existing_metrics = existing.supporting_metrics
            new_metrics = new_node.supporting_metrics

            # Example: numerical direction conflict
            if "change_pct" in existing_metrics and "change_pct" in new_metrics:
                if (existing_metrics["change_pct"] > 0 and new_metrics["change_pct"] < 0) or \
                   (existing_metrics["change_pct"] < 0 and new_metrics["change_pct"] > 0):
                    contradiction = {
                        "id": f"conflict_{len(self.contradictions) + 1}",
                        "node_a": existing.node_id,
                        "node_b": new_node.node_id,
                        "status": "CONFLICTING_EVIDENCE",
                        "description": f"Conflicting directional evidence between {existing.source_analysis} and {new_node.source_analysis}.",
                        "resolution_needed": True
                    }
                    self.contradictions.append(contradiction)
                    logger.warning(f"Contradiction detected: {contradiction['description']}")

    def get_quality_summary(self) -> Dict[str, Any]:
        """Calculates evidence quality distribution."""
        high_cnt = sum(1 for n in self.nodes if n.confidence == "HIGH")
        med_cnt = sum(1 for n in self.nodes if n.confidence == "MEDIUM")
        low_cnt = sum(1 for n in self.nodes if n.confidence in ("LOW", "INSUFFICIENT"))
        return {
            "total_nodes": len(self.nodes),
            "high_confidence_count": high_cnt,
            "medium_confidence_count": med_cnt,
            "low_confidence_count": low_cnt,
            "contradiction_count": len(self.contradictions),
            "contradictions": self.contradictions
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "question": self.question,
            "nodes": [node.to_dict() for node in self.nodes],
            "contradictions": self.contradictions,
            "quality_summary": self.get_quality_summary()
        }
