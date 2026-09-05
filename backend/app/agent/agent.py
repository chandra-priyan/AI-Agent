import logging
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from app.services.analysis_service import AnalysisService
from app.llm.service import LLMService
from app.agent.state import (
    InvestigationState, Hypothesis, HypothesisStatus, InvestigationStep,
    AnalysisExecution, EvidenceItem, AgentValidation, AgentConfidence, ConfidenceLevel
)
from app.agent.planner import AgentPlanner
from app.agent.hypothesis import HypothesisEngine
from app.agent.analyzer import AgentAnalyzer
from app.agent.evaluator import AgentEvaluator
from app.agent.validator import AgentValidator
from app.agent.synthesizer import AgentSynthesizer

logger = logging.getLogger(__name__)

class AgentSessionStore:
    """In-memory session store for tracking autonomous agent investigation states."""
    _instance = None
    _sessions: Dict[str, InvestigationState] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AgentSessionStore, cls).__new__(cls)
            cls._sessions = {}
        return cls._instance

    def save_state(self, state: InvestigationState):
        self._sessions[state.analysis_id] = state
        try:
            from app.services.persistence_service import PersistenceService
            
            # Format hypotheses for frontend compatibility
            formatted_hypotheses = [
                {
                    "id": h.id,
                    "title": getattr(h, "title", None) or h.description,
                    "description": h.description or getattr(h, "reason", "") or "",
                    "details": getattr(h, "reason", "") or "",
                    "status": "validated" if (hasattr(h, "status") and (h.status in ("SUPPORTED", "PARTIALLY_SUPPORTED") or getattr(h.status, "name", "") in ("SUPPORTED", "PARTIALLY_SUPPORTED"))) else "rejected",
                    "evidenceLevel": h.status.value if hasattr(h.status, "value") else str(h.status),
                    "isSupported": hasattr(h, "status") and (h.status in ("SUPPORTED", "PARTIALLY_SUPPORTED") or getattr(h.status, "name", "") in ("SUPPORTED", "PARTIALLY_SUPPORTED"))
                }
                for h in state.hypotheses
            ]

            # Generate key findings from hypotheses and investigation conclusion
            formatted_findings = [
                {
                    "id": f"f_{i+1}",
                    "category": getattr(h, "title", "Variance Analysis"),
                    "title": h.description or "Primary Statistical Insight",
                    "summary": getattr(h, "reason", state.conclusion or "Analysis verified statistical metric variance."),
                    "confidence": state.confidence.level.value if hasattr(state.confidence, "level") else "HIGH"
                }
                for i, h in enumerate(state.hypotheses)
            ]
            if not formatted_findings and state.conclusion:
                formatted_findings = [
                    {
                        "id": "f_1",
                        "category": "Executive Synthesis",
                        "title": "Autonomous Investigation Conclusion",
                        "summary": state.conclusion,
                        "confidence": state.confidence.level.value if hasattr(state.confidence, "level") else "HIGH"
                    }
                ]

            # In-place deduplication of state.evidence to prevent duplicates ever slipping through
            clean_evs = []
            seen_titles = set()
            for ev in state.evidence:
                if ev.title not in seen_titles:
                    seen_titles.add(ev.title)
                    clean_evs.append(ev)
            state.evidence = clean_evs

            # Format evidence
            formatted_evidence = [
                {
                    "id": ev.id,
                    "title": ev.title,
                    "chartType": ev.chart_type,
                    "data": ev.data,
                    "explanation": ev.explanation
                }
                for ev in state.evidence
            ]

            # Format recommendations
            formatted_recs = [
                {"id": f"rec_{i}", "text": r, "priority": "high"}
                for i, r in enumerate(state.recommendations)
            ]

            data_to_save = {
                "user_question": state.user_question,
                "status": state.status,
                "datasetProfile": state.dataset_profile,
                "investigationPlan": [s.model_dump() for s in state.investigation_plan],
                "findings": formatted_findings,
                "hypotheses": formatted_hypotheses,
                "executed_analyses": [e.model_dump() for e in state.executed_analyses],
                "evidence": formatted_evidence,
                "alternative_explanations": state.alternative_explanations,
                "validation": state.validation.model_dump() if hasattr(state.validation, "model_dump") else state.validation,
                "confidence": state.confidence.level.value if hasattr(state.confidence, "level") else "HIGH",
                "conclusion": state.conclusion or "",
                "recommendations": formatted_recs,
                "limitations": [
                    "Analysis based on historical dataset snapshot.",
                    "Statistical correlation does NOT imply causation."
                ],
                "evidence_graph": getattr(state, "evidence_graph_data", None),
                "audit_trail": getattr(state, "audit_trail_data", None),
                "what_if_analysis": getattr(state, "what_if_data", None),
                "predictions": getattr(state, "predictive_data", None),
                "contradictions": getattr(state, "contradictions_data", None),
                "provider_used": state.provider_used,
                "fallback_used": state.fallback_used,
                "fallback_reason": state.fallback_reason
            }
            PersistenceService.save_investigation(state.analysis_id, data_to_save)
        except Exception as err:
            logger.warning(f"Failed to persist state to database for {state.analysis_id}: {err}")

    def get_state(self, analysis_id: str) -> Optional[InvestigationState]:
        if analysis_id in self._sessions:
            return self._sessions[analysis_id]
        
        # Database fallback
        try:
            from app.services.persistence_service import PersistenceService
            db_data = PersistenceService.get_analysis(analysis_id)
            if db_data:
                state = InvestigationState(
                    analysis_id=analysis_id,
                    dataset_id=db_data.get("dataset_id") or analysis_id,
                    user_question=db_data.get("question") or "",
                    status=db_data.get("status") or "completed",
                    conclusion=db_data.get("conclusion")
                )
                self._sessions[analysis_id] = state
                return state
        except Exception:
            pass
        return None

    def list_states(self) -> List[InvestigationState]:
        return list(self._sessions.values())


class AutonomousDataScientistAgent:
    def __init__(
        self,
        analysis_service: Optional[AnalysisService] = None,
        llm_service: Optional[LLMService] = None
    ):
        self.analysis_service = analysis_service or AnalysisService()
        self.llm_service = llm_service or LLMService()

        self.planner = AgentPlanner(self.llm_service)
        self.hypothesis_engine = HypothesisEngine(self.llm_service)
        self.analyzer = AgentAnalyzer(self.analysis_service, self.llm_service)
        self.evaluator = AgentEvaluator(self.llm_service)
        self.validator = AgentValidator(self.llm_service)
        self.synthesizer = AgentSynthesizer(self.llm_service)
        self.store = AgentSessionStore()

    async def run_investigation(
        self,
        analysis_id: str,
        dataset_id: str,
        user_question: str
    ) -> InvestigationState:
        """Runs full end-to-end autonomous investigation loop."""

        logger.info(f"Starting autonomous investigation [{analysis_id}] for question: '{user_question}'")

        # 1. Fetch dataset profile & health quality
        profile_res = await self.analysis_service.run_dataset_profiler(dataset_id)
        dataset_profile = profile_res.model_dump()

        health_res = await self.analysis_service.run_data_quality_report(dataset_id)
        data_quality = health_res.model_dump()

        # 2. Initialize State
        state = InvestigationState(
            analysis_id=analysis_id,
            dataset_id=dataset_id,
            user_question=user_question,
            dataset_profile=dataset_profile,
            data_quality=data_quality,
            status="planning"
        )
        state.logs.append(f"Started investigation for question: '{user_question}'")
        self.store.save_state(state)

        # Phase 9 core engines initialization
        from app.agent.evidence_graph import EvidenceGraph
        from app.agent.audit_trail import AuditTrailLogger
        from app.agent.whatif_predictive import WhatIfPredictiveEngine
        from app.agent.root_cause import RootCauseEngine

        audit_logger = AuditTrailLogger(analysis_id)
        evidence_graph = EvidenceGraph(user_question)
        audit_logger.log_event("goal_understood", f"Understood question intent for: '{user_question}'")

        try:
            # 3. Understand Goal & Answerability
            goal = await self.planner.understand_goal_and_dataset(user_question, dataset_profile, data_quality)
            state.investigation_goal = goal
            state.logs.append(f"Goal understood: intent='{goal.intent}', target_metric='{goal.target_metric}'")

            if not goal.is_answerable:
                logger.warning(f"Goal flagged as vague/unsupported. Falling back to exploratory dataset investigation for {dataset_id}")
                goal.is_answerable = True
                num_cols = dataset_profile.get("numerical_columns", [])
                cat_cols = dataset_profile.get("categorical_columns", [])
                goal.target_metric = num_cols[0] if num_cols else (cat_cols[0] if cat_cols else "metric")
                goal.unsupported_reason = None

            # 4. Create Plan
            plan = await self.planner.create_plan(user_question, goal, dataset_profile)
            state.investigation_plan = plan
            audit_logger.log_event("plan_created", f"Constructed investigation plan with {len(plan)} steps.")
            state.logs.append(f"Created investigation plan with {len(plan)} steps.")
            self.store.save_state(state)

            # 5. Generate Hypotheses & Prioritize
            hypotheses = await self.hypothesis_engine.generate_hypotheses(user_question, goal, dataset_profile)
            state.hypotheses = hypotheses
            state.status = "investigating"
            audit_logger.log_event("hypotheses_generated", f"Generated and prioritized {len(hypotheses)} hypotheses.")
            state.logs.append(f"Generated {len(hypotheses)} hypotheses.")
            self.store.save_state(state)

            # 6. Agent ↔ Python Investigation Loop
            max_iterations = min(3, len(hypotheses) + 1)
            for iteration in range(max_iterations):
                state.iteration_count = iteration + 1
                state.logs.append(f"Starting iteration {iteration + 1}/{max_iterations}")

                # Select and execute Python analysis
                execution, evidence_item = await self.analyzer.select_and_execute_analysis(
                    analysis_id=analysis_id,
                    dataset_id=dataset_id,
                    question=user_question,
                    goal=goal,
                    dataset_profile=dataset_profile,
                    hypotheses=state.hypotheses,
                    executed_analyses=state.executed_analyses
                )

                state.executed_analyses.append(execution)
                
                # Deduplicate charts by title, ensuring we replace empty charts if a populated one becomes available
                existing_match_idx = next((i for i, ev in enumerate(state.evidence) if ev.title == evidence_item.title), None)
                if existing_match_idx is None:
                    state.evidence.append(evidence_item)
                elif evidence_item.data and not state.evidence[existing_match_idx].data:
                    state.evidence[existing_match_idx] = evidence_item

                audit_logger.log_event("analysis_executed", f"Executed Python analysis: {execution.analysis_type}")
                state.logs.append(f"Executed Python analysis: {execution.analysis_type}")

                # Populate Evidence Graph Node
                pending_hypotheses = [h for h in state.hypotheses if h.status == HypothesisStatus.PENDING]
                target_hyp = pending_hypotheses[0] if pending_hypotheses else state.hypotheses[0]

                evidence_graph.add_evidence(
                    hypothesis_id=target_hyp.id,
                    finding=evidence_item.explanation,
                    source_analysis=execution.analysis_type,
                    supporting_metrics=execution.result or {},
                    data_quality_score=data_quality.get("quality_score", 1.0),
                    confidence="HIGH"
                )

                updated_hyp = await self.evaluator.evaluate_evidence(target_hyp, execution)
                for idx, h in enumerate(state.hypotheses):
                    if h.id == updated_hyp.id:
                        state.hypotheses[idx] = updated_hyp

                # Update step status in plan
                if iteration < len(state.investigation_plan):
                    state.investigation_plan[iteration].status = "completed"
                    if iteration + 1 < len(state.investigation_plan):
                        state.investigation_plan[iteration + 1].status = "active"

                self.store.save_state(state)

            # 7. Check Alternative Explanations & Root Cause
            supported_hyp = [
                h for h in state.hypotheses
                if h.status in (HypothesisStatus.SUPPORTED, HypothesisStatus.PARTIALLY_SUPPORTED)
            ]

            alternatives = await self.evaluator.generate_alternative_explanations(supported_hyp, dataset_profile)
            state.alternative_explanations = alternatives
            audit_logger.log_event("alternatives_evaluated", f"Evaluated {len(alternatives)} alternative explanations.")

            # Run What-If & Predictive calculations if dataset permits
            if goal.target_metric:
                try:
                    from app.analysis.loader import CSVLoader
                    df = CSVLoader.get_dataset(dataset_id)
                    if df is not None:
                        state.what_if_data = WhatIfPredictiveEngine.run_what_if_simulation(df, goal.target_metric, -10.0)
                        state.predictive_data = WhatIfPredictiveEngine.run_predictive_analysis(df, goal.target_metric)
                except Exception as ex_whatif:
                    logger.warning(f"What-If simulation skipped: {ex_whatif}")

            # 8. Validation & Confidence Assessment
            validation, confidence = await self.validator.validate_investigation(
                question=user_question,
                data_quality=data_quality,
                hypotheses=state.hypotheses,
                executed_analyses=state.executed_analyses
            )
            state.validation = validation
            state.confidence = confidence
            audit_logger.log_event("validation_completed", f"Validation complete with confidence {confidence.level.value}")

            # 9. Final Synthesis
            conclusion, recs, next_inv = await self.synthesizer.synthesize_results(
                question=user_question,
                goal=goal,
                hypotheses=state.hypotheses,
                evidence=state.evidence,
                validation=validation,
                confidence=confidence
            )

            state.conclusion = conclusion
            state.recommendations = recs
            state.next_investigation = next_inv
            state.status = "completed"

            # Mark all plan steps completed
            for step in state.investigation_plan:
                step.status = "completed"

            audit_logger.log_event("investigation_completed", "Investigation finished successfully.", status="COMPLETED")

            # Attach Phase 9 data structures to state
            state.audit_trail_data = audit_logger.to_list()
            state.evidence_graph_data = evidence_graph.to_dict()
            state.contradictions_data = evidence_graph.contradictions

            state.logs.append("Investigation completed successfully.")
            # Copy LLM provider metadata
            state.provider_used = getattr(self.llm_service, "last_provider_used", "groq")
            state.fallback_used = getattr(self.llm_service, "last_fallback_used", False)
            state.fallback_reason = getattr(self.llm_service, "last_fallback_reason", None)
            
            self.store.save_state(state)
            return state

        except Exception as e:
            logger.error(f"Error during investigation [{analysis_id}]: {e}", exc_info=True)
            state.status = "failed"
            state.conclusion = f"Investigation encountered an unexpected error: {str(e)}"
            state.confidence = AgentConfidence(
                level=ConfidenceLevel.INSUFFICIENT,
                rationale=[state.conclusion]
            )
            state.logs.append(f"Investigation failed: {str(e)}")
            
            # Copy LLM provider metadata even on failure if available
            state.provider_used = getattr(self.llm_service, "last_provider_used", "groq")
            state.fallback_used = getattr(self.llm_service, "last_fallback_used", False)
            state.fallback_reason = getattr(self.llm_service, "last_fallback_reason", None)

            self.store.save_state(state)
            return state

    async def answer_followup_chat(
        self,
        analysis_id: str,
        user_question: Optional[str],
        user_message: str
    ) -> str:
        """Grounds follow-up chat in actual CSV dataset profile and investigation findings."""
        state = self.store.get_state(analysis_id)
        
        # Check database if not in memory
        from app.services.persistence_service import PersistenceService
        db_analysis = PersistenceService.get_analysis(analysis_id)
        
        dataset_profile = state.dataset_profile if state else (db_analysis.get("datasetProfile") if db_analysis else {})
        column_names = dataset_profile.get("column_names") or []
        conclusion = state.conclusion if state else (db_analysis.get("conclusion") if db_analysis else "")
        question = user_question or (state.user_question if state else (db_analysis.get("question") if db_analysis else "Business Question"))
        
        # Inspect if user asks about a missing column
        msg_lower = user_message.lower()
        if "region" in msg_lower and not any("region" in col.lower() for col in column_names):
            return f"The dataset does not contain a 'region' field (available columns: {', '.join(column_names[:8])}), so I cannot evaluate regional differences for this analysis."
        
        if "churn" in msg_lower and not any("churn" in col.lower() for col in column_names):
            return f"The dataset does not contain a 'churn' field (available columns: {', '.join(column_names[:8])}), so I cannot evaluate customer churn."
        
        if "price" in msg_lower or "discount" in msg_lower:
            if not any(k in col.lower() for col in column_names for k in ["price", "discount", "cost"]):
                return f"The dataset does not contain pricing or discount fields (available columns: {', '.join(column_names[:8])}), so pricing impact cannot be computed."

        prompt = f"""
You are an expert Autonomous Data Scientist providing a follow-up answer to a client.

INVESTIGATION CONTEXT:
- Original Question: {question}
- Available Columns: {', '.join(column_names)}
- Key Finding / Conclusion: {conclusion}

USER FOLLOW-UP QUESTION:
"{user_message}"

INSTRUCTIONS:
1. Ground your answer strictly in the available dataset columns and conclusion above.
2. If the user asks about factors or metrics NOT present in the dataset, explicitly explain that the dataset lacks that information.
3. Be concise, precise, and professional.
"""
        try:
            response = await self.llm_service.generate(prompt)
            return response.strip()
        except Exception as err:
            logger.warning(f"Groq chat generation failed: {err}")
            return f"Based on the analysis of {question}, the calculated evidence indicates: {conclusion or 'Investigation complete.'}"

