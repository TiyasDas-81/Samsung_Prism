import asyncio
import uuid
import logging
import time
import json
from typing import Any, Dict, Optional
from .state import SessionState
from .tools import registry

logger = logging.getLogger(__name__)

class Agent:
    def __init__(self):
        self.state = SessionState()
        self.output_queue = asyncio.Queue()
        self.running_tasks: Dict[str, Dict[str, Any]] = {}
        self.completed_state_modifications = set() # To prevent duplicates
    
    async def process_event(self, event: Dict[str, Any]):
        event_type = event.get("type")
        
        if event_type in ["user_input", "interruption"]:
            await self.handle_user_input(event)
        elif event_type == "tool_result":
            await self.handle_tool_result(event)
        else:
            logger.warning(f"Unknown event type: {event_type}")

    async def emit(self, msg: Dict[str, Any]):
        if "event_id" not in msg:
            msg["event_id"] = str(uuid.uuid4())
        if "timestamp" not in msg:
            msg["timestamp"] = time.time()
        await self.output_queue.put(msg)

    async def handle_user_input(self, event: Dict[str, Any]):
        text = event.get("text", "")
        intent = event.get("intent")
        slots = event.get("slots", {})
        
        # Acknowledge immediately (Fast Path)
        await self.emit({"type": "ack", "text": "Got it."})
        
        initial_generation = self.state.current.generation
        
        # Update State Snapshot
        if intent:
            self.state.current.update_intent(intent)
        if slots:
            self.state.current.update_slots(slots)
            
        new_generation = self.state.current.generation
            
        await self.emit({"type": "state_snapshot", "snapshot": self.state.snapshot()})

        # Interruption logic
        # If generation increased or cancel requested
        if new_generation > initial_generation or event.get("cancel_ongoing"):
            for call_id, info in list(self.running_tasks.items()):
                if info["generation"] < new_generation or event.get("cancel_ongoing"):
                    # We intentionally do not call info["task"].cancel() here 
                    # in order to demonstrate stale_result_ignored when the late result arrives.
                    del self.running_tasks[call_id]
                    if call_id in self.state.current.active_tool_calls:
                        del self.state.current.active_tool_calls[call_id]
                    await self.emit({"type": "tool_cancelled", "call_id": call_id, "tool_name": info["tool_name"]})
                
        # Handle Slow Path Tool execution
        tool_name = event.get("tool")
        if tool_name:
            tool = registry.get_tool(tool_name)
            if not tool:
                await self.emit({"type": "tool_error", "error": f"Unknown tool: {tool_name}"})
                return
                
            call_id = str(uuid.uuid4())
            
            # Use current state slots for arguments
            args = self.state.current.slots.copy()
            
            is_valid, err_msg = tool.validate_args(args)
            if not is_valid:
                await self.emit({"type": "tool_error", "call_id": call_id, "error": err_msg})
                return
                
            expected_generation = self.state.current.generation
            
            # Prevent duplicate state modification
            sorted_args = json.dumps(args, sort_keys=True)
            dedup_key = f"{tool_name}_{sorted_args}_{self.state.session_id}"
            
            if tool.is_state_modifying and dedup_key in self.completed_state_modifications:
                await self.emit({"type": "tool_error", "call_id": call_id, "error": "Duplicate state-changing call prevented."})
                return

            # Execute tool asynchronously
            task = asyncio.create_task(
                self.execute_tool_async(call_id, tool_name, args, expected_generation, dedup_key)
            )
            self.running_tasks[call_id] = {"task": task, "generation": expected_generation, "tool_name": tool_name}
            self.state.current.active_tool_calls[call_id] = task
            
            await self.emit({"type": "tool_call", "call_id": call_id, "tool_name": tool_name, "args": args})

    async def execute_tool_async(self, call_id: str, tool_name: str, args: Dict[str, Any], expected_generation: int, dedup_key: str):
        try:
            tool = registry.get_tool(tool_name)
            result = await tool.func(**args)
            
            # Post-execution validation for stale results
            if self.state.current.generation != expected_generation:
                logger.info(f"Stale result ignored for call {call_id}")
                await self.emit({
                    "type": "stale_result_ignored",
                    "call_id": call_id,
                    "tool_name": tool_name,
                    "expected_generation": expected_generation,
                    "current_generation": self.state.current.generation
                })
                return
                
            if tool.is_state_modifying:
                self.completed_state_modifications.add(dedup_key)

            await self.emit({
                "type": "tool_result",
                "call_id": call_id,
                "result": result,
                "generation": expected_generation
            })
            await self.emit({"type": "final_response", "text": f"Finished {tool_name} with result {result}"})
            
        except asyncio.CancelledError:
            logger.info(f"Tool {tool_name} cancelled")
        finally:
            if call_id in self.running_tasks:
                del self.running_tasks[call_id]
            if call_id in self.state.current.active_tool_calls:
                del self.state.current.active_tool_calls[call_id]

    async def handle_tool_result(self, event: Dict[str, Any]):
        pass
