import json
import os
from typing import Any, Dict
from datetime import datetime

STORAGE_FILE = "webhook_events.json"

def store_webhook_event(event_type: str, payload: Dict[str, Any]) -> None:
    """
    Appends the received secured webhook event and payload to a local JSON file.
    """
    event_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "event": event_type,
        "payload": payload
    }
    
    events = []
    if os.path.exists(STORAGE_FILE):
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    events = json.loads(content)
        except Exception as e:
            print(f"Error reading storage file: {e}")
            
    events.append(event_entry)
    
    try:
        with open(STORAGE_FILE, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing to storage file: {e}")
