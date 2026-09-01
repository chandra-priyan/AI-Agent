import pytest
import uuid
from app.db.database import SessionLocal, Base, engine
from app.repositories.analysis_repository import AnalysisRepository
from app.services.persistence_service import PersistenceService

@pytest.fixture(autouse=True)
def init_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield

def test_create_and_get_analysis():
    aid = f"test_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    try:
        repo = AnalysisRepository(db)
        repo.create_analysis(aid, "Why did revenue drop?", "sales.csv")
        
        fetched = repo.get_analysis(aid)
        assert fetched is not None
        assert fetched.id == aid
        assert fetched.question == "Why did revenue drop?"
        assert fetched.status == "CREATED"
    finally:
        db.close()

def test_list_analyses():
    aid1 = f"test_{uuid.uuid4().hex[:8]}"
    aid2 = f"test_{uuid.uuid4().hex[:8]}"
    PersistenceService.create_analysis(aid1, "Question 1")
    PersistenceService.create_analysis(aid2, "Question 2")

    analyses = PersistenceService.list_analyses()
    ids = [a["id"] for a in analyses]
    assert aid1 in ids
    assert aid2 in ids

def test_update_status():
    aid = f"test_{uuid.uuid4().hex[:8]}"
    PersistenceService.create_analysis(aid, "Test Status Update")
    
    PersistenceService.update_status(aid, "RUNNING")
    fetched = PersistenceService.get_analysis(aid)
    assert fetched["status"] == "RUNNING"

    PersistenceService.update_status(aid, "COMPLETED")
    fetched2 = PersistenceService.get_analysis(aid)
    assert fetched2["status"] == "COMPLETED"

def test_save_and_retrieve_investigation():
    aid = f"test_{uuid.uuid4().hex[:8]}"
    data = {
        "user_question": "Why did customer churn spike?",
        "status": "completed",
        "datasetProfile": {"rowCount": 1500, "filename": "churn.csv"},
        "conclusion": "Customer churn spiked due to price increases.",
        "confidence": "HIGH",
        "hypotheses": [{"id": "h1", "title": "Price increase", "isSupported": True}],
        "evidence": [{"id": "e1", "title": "Churn vs Price", "chartType": "bar", "data": []}],
        "recommendations": [{"id": "rec_1", "text": "Review pricing tiers"}]
    }

    PersistenceService.save_investigation(aid, data)
    retrieved = PersistenceService.get_analysis(aid)
    
    assert retrieved is not None
    assert retrieved["id"] == aid
    assert retrieved["conclusion"] == "Customer churn spiked due to price increases."
    assert retrieved["confidence"] == "HIGH"
    assert len(retrieved["hypotheses"]) == 1

def test_save_and_retrieve_chat_history():
    aid = f"test_{uuid.uuid4().hex[:8]}"
    PersistenceService.create_analysis(aid, "Chat Test Question")

    PersistenceService.save_chat_message(aid, "USER", "What caused the drop?")
    PersistenceService.save_chat_message(aid, "ASSISTANT", "The main driver was regional sales in North.")

    history = PersistenceService.get_chat_history(aid)
    assert len(history) == 2
    assert history[0]["sender"] == "user"
    assert history[0]["text"] == "What caused the drop?"
    assert history[1]["sender"] == "ai"

def test_delete_analysis():
    aid = f"test_{uuid.uuid4().hex[:8]}"
    PersistenceService.create_analysis(aid, "To be deleted")
    PersistenceService.save_chat_message(aid, "USER", "Message")

    assert PersistenceService.get_analysis(aid) is not None
    deleted = PersistenceService.delete_analysis(aid)
    assert deleted is True

    assert PersistenceService.get_analysis(aid) is None
    assert len(PersistenceService.get_chat_history(aid)) == 0

def test_invalid_analysis_id():
    fake_id = f"nonexistent_{uuid.uuid4().hex}"
    assert PersistenceService.get_analysis(fake_id) is None
    assert PersistenceService.delete_analysis(fake_id) is False
