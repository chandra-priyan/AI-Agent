import pytest
from app.api.report import build_report_data
from app.services.persistence_service import PersistenceService

def test_build_report_data_includes_chat_and_details():
    analysis_id = "test_analysis_report_123"
    user_id = "test_user_report_123"

    # Create dummy analysis record
    PersistenceService.create_analysis(
        analysis_id=analysis_id,
        question="How did sales perform in Q3?",
        filename="sales_data.csv",
        user_id=user_id
    )

    # Save dummy chat message
    PersistenceService.save_chat_message(
        analysis_id=analysis_id,
        role="user",
        text="What was the total revenue in West region?",
        user_id=user_id
    )
    PersistenceService.save_chat_message(
        analysis_id=analysis_id,
        role="assistant",
        text="Total revenue in West region was $145,000.",
        confidence="HIGH",
        user_id=user_id
    )

    # Build report data
    current_user = {"id": user_id, "email": "test@example.com"}
    report = build_report_data(analysis_id, current_user)

    assert report["analysisId"] == analysis_id
    assert report["title"] == "sales_data.csv Executive Investigation Report"
    assert report["businessQuestion"] == "How did sales perform in Q3?"
    assert isinstance(report["chatHistory"], list)
    assert len(report["chatHistory"]) >= 2
    assert report["chatHistory"][0]["text"] == "What was the total revenue in West region?"
    assert report["chatHistory"][1]["text"] == "Total revenue in West region was $145,000."
    assert "keyFindings" in report
    assert "hypotheses" in report
    assert "recommendations" in report
    assert "evidence" in report
    assert "auditTrail" in report
