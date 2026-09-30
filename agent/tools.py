import asyncio
import inspect
from typing import Any, Callable, Dict, Optional, Awaitable, List

class Tool:
    def __init__(self, name: str, func: Callable[..., Awaitable[Any]], is_state_modifying: bool = False, schema: Optional[Dict[str, Any]] = None, required: Optional[List[str]] = None):
        self.name = name
        self.func = func
        self.is_state_modifying = is_state_modifying
        self.schema = schema or {}
        self.required = required or []

    def validate_args(self, args: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        for req in self.required:
            if req not in args:
                return False, f"Missing required argument: {req}"
        for key, val in args.items():
            if key in self.schema:
                expected_type = self.schema[key]
                if expected_type == "string" and not isinstance(val, str):
                    return False, f"Argument {key} must be a string."
                elif expected_type == "integer" and not isinstance(val, int):
                    return False, f"Argument {key} must be an integer."
                elif expected_type == "boolean" and not isinstance(val, bool):
                    return False, f"Argument {key} must be a boolean."
        return True, None

class ToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Tool] = {}

    def register(self, name: str, is_state_modifying: bool = False, schema: Optional[Dict[str, Any]] = None, required: Optional[List[str]] = None):
        def decorator(func: Callable[..., Awaitable[Any]]):
            self.tools[name] = Tool(name, func, is_state_modifying, schema, required)
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[Tool]:
        return self.tools.get(name)

registry = ToolRegistry()

@registry.register(
    name="search_flight", 
    is_state_modifying=False, 
    schema={"destination": "string"}, 
    required=["destination"]
)
async def search_flight(destination: str, **kwargs):
    await asyncio.sleep(0.5) # Simulate slow operation
    return {"status": "success", "flights": [f"Flight to {destination} 1", f"Flight to {destination} 2"]}

@registry.register(
    name="book_flight", 
    is_state_modifying=True, 
    schema={"destination": "string"}, 
    required=["destination"]
)
async def book_flight(destination: str, **kwargs):
    await asyncio.sleep(0.5)
    return {"status": "booked", "destination": destination, "confirmation": "AB123"}
