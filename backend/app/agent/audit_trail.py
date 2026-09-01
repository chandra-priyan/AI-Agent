import datetime
from typing import List, Dict, Any

class AuditTrailLogger:
    """Persists safe investigation action trail without revealing private chain-of-thought."""

    def __init__(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.events: List[Dict[str, Any]] = []

    def log_event(self, action: str, details: str, status: str = "COMPLETED"):
        event = {
            "timestamp": datetime.datetime.utcnow().isoformat(),
            "action": action,
            "details": details,
            "status": status
        }
        self.events.append(event)

    def to_list(self) -> List[Dict[str, Any]]:
        return self.events
