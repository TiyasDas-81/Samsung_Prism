import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class MultimodalProcessor:
    def __init__(self):
        pass

    def process(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process multimodal input (audio, video, text) and extract intent and slots.
        Returns a structured perception result.
        """
        event_type = event.get("type")
        
        if event_type == "text":
            return {
                "type": "user_input",
                "text": event.get("content", ""),
                "intent": event.get("intent"),
                "slots": event.get("slots", {}),
                "tool": event.get("tool"),
                "cancel_ongoing": event.get("cancel_ongoing", False)
            }
        elif event_type in ["audio", "video"]:
            logger.info(f"Processing multimodal input of type {event_type}")
            
            # Adapter mock input representing that we are processing metadata/references
            # since actual models are unavailable.
            reference = event.get("reference")
            metadata = event.get("payload_metadata", {})
            
            if event.get("ambiguous") or metadata.get("ambiguous"):
                return {
                    "type": "clarification",
                    "text": "The provided audio/video was ambiguous. Please clarify your request.",
                    "intent": "clarification_needed"
                }
            
            return {
                "type": "user_input",
                "text": f"Adapter mock perception for {event_type} (ref: {reference})",
                "intent": metadata.get("intent", "multimodal_intent"),
                "slots": metadata.get("slots", {"media": event_type}),
                "tool": metadata.get("tool"),
                "cancel_ongoing": event.get("cancel_ongoing", False)
            }
        
        return {"type": "unknown"}
