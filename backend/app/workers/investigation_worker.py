import logging
import asyncio
from typing import Optional
from app.jobs.job_service import JobService
from app.agent.agent import AutonomousDataScientistAgent

logger = logging.getLogger(__name__)

async def run_background_investigation_job(
    analysis_id: str,
    user_question: str,
    dataset_id: Optional[str] = None,
    user_id: Optional[str] = None
):
    """Background worker job runner that executes the Autonomous AI Agent investigation loop."""
    logger.info(f"Background Worker starting job [{analysis_id}]")
    effective_dataset_id = dataset_id or analysis_id

    # 1. Update status to RUNNING
    JobService.update_job_status(
        analysis_id=analysis_id,
        status="RUNNING",
        stage="UNDERSTANDING_QUESTION",
        progress=10
    )

    try:
        agent = AutonomousDataScientistAgent()

        # Update progress: Profiling
        JobService.update_job_status(analysis_id, "RUNNING", "PROFILING_DATA", 25)
        await asyncio.sleep(0.05)

        # Check cancellation
        status_info = JobService.get_job_status(analysis_id)
        if status_info and status_info.get("status") == "CANCELLED":
            logger.info(f"Job [{analysis_id}] was cancelled prior to agent run.")
            return

        # Update progress: Planning
        JobService.update_job_status(analysis_id, "RUNNING", "PLANNING", 40)

        # Update progress: Generating Hypotheses
        JobService.update_job_status(analysis_id, "RUNNING", "GENERATING_HYPOTHESES", 55)

        # Update progress: Analyzing & Evaluating
        JobService.update_job_status(analysis_id, "RUNNING", "ANALYZING", 70)

        # Execute full agent investigation loop
        final_state = await agent.run_investigation(analysis_id, effective_dataset_id, user_question)

        # Check cancellation
        status_info = JobService.get_job_status(analysis_id)
        if status_info and status_info.get("status") == "CANCELLED":
            logger.info(f"Job [{analysis_id}] was cancelled during agent run.")
            return

        if final_state.status == "failed":
            JobService.update_job_status(
                analysis_id=analysis_id,
                status="FAILED",
                stage="FAILED",
                progress=100,
                error_summary="Investigation could not be completed."
            )
            return

        # Update progress: Synthesizing & Completed
        JobService.update_job_status(analysis_id, "RUNNING", "SYNTHESIZING", 95)
        await asyncio.sleep(0.05)

        JobService.update_job_status(
            analysis_id=analysis_id,
            status="COMPLETED",
            stage="COMPLETED",
            progress=100
        )
        logger.info(f"Background Worker successfully completed job [{analysis_id}]")

    except Exception as e:
        logger.error(f"Background Worker encountered error in job [{analysis_id}]: {e}", exc_info=True)
        JobService.update_job_status(
            analysis_id=analysis_id,
            status="FAILED",
            stage="FAILED",
            progress=100,
            error_summary="Investigation could not be completed."
        )
