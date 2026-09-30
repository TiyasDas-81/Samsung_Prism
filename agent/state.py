import asyncio
import uuid
import logging
from typing import Any, Dict, Optional, Callable, Awaitable

logger = logging.getLogger(__name__)

class StateSnapshot:
    def __init__(self):
        self.intent: Optional[str] = None
        self.slots: Dict[str, Any] = {}
        self.generation: int = 0
        self.active_tool_calls: Dict[str, asyncio.Task] = {}
        
    def update_intent(self, intent: str):
        if self.intent != intent:
            self.intent = intent
            self.generation += 1
        
    def update_slots(self, new_slots: Dict[str, Any]):
        changed = False
        for k, v in new_slots.items():
            if self.slots.get(k) != v:
                self.slots[k] = v
                changed = True
        if changed:
            self.generation += 1
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "intent": self.intent,
            "slots": self.slots.copy(),
            "generation": self.generation,
            "active_tool_calls": list(self.active_tool_calls.keys())
        }

class SessionState:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.current = StateSnapshot()
        self.history = []
        
    def snapshot(self):
        return self.current.to_dict()
