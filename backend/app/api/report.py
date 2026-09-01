import datetime
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import AnalysisModel, UserModel
from app.core.auth import get_optional_current_user
from app.services.persistence_service import PersistenceService

router = APIRouter(prefix="/api/v1/report", tags=["Report"])

def verify_analysis_ownership(analysis_id: str, current_user: Optional[UserModel], db: Session) -> AnalysisModel:
    """Verify analysis exists and belongs to user if bound."""
    analysis = db.query(AnalysisModel).filter(AnalysisModel.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    if analysis.user_id and current_user and analysis.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not have access to this analysis.")

    return analysis

@router.post("/generate/{analysis_id}")
async def generate_analysis_report(
    analysis_id: str,
    current_user: Optional[UserModel] = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    """Generate summary report structure from completed analysis."""
    analysis = verify_analysis_ownership(analysis_id, current_user, db)
    
    # Check if analysis is completed
    if analysis.status != "COMPLETED":
        raise HTTPException(status_code=400, detail="Analysis is not completed yet.")

    session = PersistenceService.get_analysis(analysis_id)
    if not session:
        raise HTTPException(status_code=404, detail="Analysis results details not found.")

    row_count = session.get("datasetProfile", {}).get("rowCount", 0) if session.get("datasetProfile") else 0
    
    findings = [f.get("summary") for f in session.get("findings", [])] if session.get("findings") else []
    if not findings and session.get("conclusion"):
        findings = [session.get("conclusion")]

    recommendations = [r.get("text") for r in session.get("recommendations", [])] if session.get("recommendations") else []

    report_title = f"{session.get('datasetName', 'Dataset')} Executive Investigation Report"

    return {
        "id": f"report_{analysis_id}",
        "analysisId": analysis_id,
        "title": report_title,
        "generatedAt": datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "executiveSummary": session.get("conclusion") or "Analysis completed successfully.",
        "businessQuestion": session.get("question") or "Business Query",
        "datasetOverview": f"{session.get('datasetName', 'dataset.csv')} ({row_count:,} rows)",
        "keyFindings": findings,
        "hypotheses": session.get("hypotheses") or [],
        "validation": session.get("validation") or {"isVerified": True, "metrics": {}, "rationale": ""},
        "recommendations": recommendations,
        "limitations": session.get("limitations") or [
            "Analysis based on provided historical snapshot.",
            "External macroeconomic indicators were not present in dataset schema."
        ]
    }
