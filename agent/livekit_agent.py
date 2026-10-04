"""
Samsung PRISM GenAI Hackathon 2026 – Theme 05
LiveKit Voice Agent (livekit-agents v1.8.x)

Provider map (no OpenAI key needed for the agent itself):
  LLM  → Groq  llama-3.1-70b-versatile  (via openai-compat base_url)
  STT  → Groq  whisper-large-v3          (via openai-compat base_url)
  TTS  → ElevenLabs free tier
  VAD  → Silero (local ONNX model)
"""

import asyncio
import logging
import json
import time
import os
from pathlib import Path
import contextvars
from dotenv import load_dotenv

load_dotenv()

room_name_var = contextvars.ContextVar("room_name", default="")


from livekit.agents import (
    Agent,
    AgentSession,
    AutoSubscribe,
    JobContext,
    WorkerOptions,
    cli,
    function_tool,
    RunContext,
)
from livekit.plugins import openai, silero, elevenlabs
from agent.core import Agent as CoordinationAgent
from agent.tools import registry

logger = logging.getLogger("livekit-agent")


# ---------------------------------------------------------------------------
# Telemetry helper – FDB-v3 checks tool-call timestamps
# ---------------------------------------------------------------------------
def log_tool_call(func_name: str, args: dict, t_start: float, t_end: float):
    # FDB evaluator explicitly reads from /tmp/agent_tool_calls.log
    telemetry_path = Path("/tmp/agent_tool_calls.log")
    telemetry_path.parent.mkdir(parents=True, exist_ok=True)
    with open(telemetry_path, "a") as f:
        f.write(json.dumps({
            "room": room_name_var.get(),
            "call": {
                "function": func_name,
                "args": args,
                "timestamp_start": t_start,
                "timestamp_end": t_end,
            }
        }) + "\n")


# ---------------------------------------------------------------------------
# Coordination-layer bridge
# ---------------------------------------------------------------------------
_coord_agent = CoordinationAgent()


async def _exec(tool_name: str, **kwargs) -> str:
    """Route a tool call through the CoordinationAgent and return JSON."""
    t_start = time.time()

    # Notify the coordination agent about the intent
    await _coord_agent.process_event({
        "type": "user_input",
        "intent": tool_name,
        "slots": kwargs,
        "tool": tool_name,
    })

    # Execute via the tool registry
    tool_spec = registry.tools.get(tool_name)
    if tool_spec:
        result = await tool_spec.execute(**kwargs)
    else:
        result = {"error": f"Tool '{tool_name}' not found"}

    t_end = time.time()
    log_tool_call(tool_name, kwargs, t_start, t_end)
    return json.dumps(result)


# ---------------------------------------------------------------------------
# FDB-v3 tool definitions  (decorated with @function_tool for v1.8.x)
# ---------------------------------------------------------------------------

@function_tool(description="Search for available flights to a destination.")
async def search_flights(ctx: RunContext, destination: str, date: str) -> str:
    return await _exec("search_flights", destination=destination, date=date)


@function_tool(description="Book a flight for a passenger.")
async def book_flight(ctx: RunContext, passenger_name: str, flight_id: str = "FL123") -> str:
    return await _exec("book_flight", passenger_name=passenger_name, flight_id=flight_id)


@function_tool(description="Update an identity document.")
async def update_identity_doc(ctx: RunContext, doc_type: str, doc_number: str) -> str:
    return await _exec("update_identity_doc", doc_type=doc_type, doc_number=doc_number)


@function_tool(description="Get benefits for a specific card type.")
async def get_card_benefits(ctx: RunContext, card_type: str) -> str:
    return await _exec("get_card_benefits", card_type=card_type)


@function_tool(description="Get exchange rate between currencies.")
async def get_exchange_rate(ctx: RunContext, amount: float, from_currency: str, to_currency: str) -> str:
    return await _exec("get_exchange_rate", amount=amount, from_currency=from_currency, to_currency=to_currency)


@function_tool(description="Modify autopay settings.")
async def modify_autopay(ctx: RunContext, bill_type: str, source_account: str) -> str:
    return await _exec("modify_autopay", bill_type=bill_type, source_account=source_account)


@function_tool(description="Search for apartments based on criteria.")
async def search_apartments(ctx: RunContext, city: str, bedrooms: int, max_price: float) -> str:
    return await _exec("search_apartments", city=city, bedrooms=bedrooms, max_price=max_price)


@function_tool(description="Calculate commute duration.")
async def calculate_commute(ctx: RunContext, origin_address: str, destination_address: str, mode: str = "driving") -> str:
    return await _exec("calculate_commute", origin_address=origin_address, destination_address=destination_address, mode=mode)


@function_tool(description="Update search filter.")
async def update_search_filter(ctx: RunContext, filter_name: str, value: str) -> str:
    return await _exec("update_search_filter", filter_name=filter_name, value=value)


@function_tool(description="Track a package order.")
async def track_order(ctx: RunContext, order_id: str) -> str:
    return await _exec("track_order", order_id=order_id)


@function_tool(description="Search for products.")
async def search_products(ctx: RunContext, query: str, max_price: float = None) -> str:
    return await _exec("search_products", query=query, max_price=max_price)


@function_tool(description="Add an item to shopping cart.")
async def add_to_cart(ctx: RunContext, product_id: str, quantity: int = 1) -> str:
    return await _exec("add_to_cart", product_id=product_id, quantity=quantity)


# Extension use case: in-car navigation
@function_tool(description="Navigate to a destination")
async def navigate(ctx: RunContext, destination: str) -> str:
    return await _exec("navigate", destination=destination)


# ---------------------------------------------------------------------------
# All tools collected in a list
# ---------------------------------------------------------------------------
ALL_TOOLS = [
    search_flights,
    book_flight,
    update_identity_doc,
    get_card_benefits,
    get_exchange_rate,
    modify_autopay,
    search_apartments,
    calculate_commute,
    update_search_filter,
    track_order,
    search_products,
    add_to_cart,
    navigate,
]


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
async def entrypoint(ctx: JobContext):
    room_name_var.set(ctx.room.name)
    await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)

    # Consume coordination-agent events in the background
    async def consume_events():
        while True:
            event = await _coord_agent.output_queue.get()
            logger.info(f"CoordinationAgent event: {event}")

    asyncio.create_task(consume_events())

    # Build the voice agent  ─  NO OpenAI key needed
    agent = Agent(
        instructions=(
            "You are a Samsung PRISM voice assistant. "
            "Use the provided tools to help the user. "
            "Be concise and conversational."
        ),
        tools=ALL_TOOLS,
    )

    session = AgentSession(
        stt=openai.STT(
            model="whisper-large-v3",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY"),
        ),
        llm=openai.LLM(
            model="qwen/qwen3.8-27b",
            base_url="https://api.groq.com/openai/v1",
            api_key=os.environ.get("GROQ_API_KEY"),
        ),
        tts=elevenlabs.TTS(),
        vad=silero.VAD.load(),
        allow_interruptions=True,
    )

    await session.start(agent, room=ctx.room)

    await asyncio.sleep(1)
    await session.say("I am your Samsung PRISM assistant. How can I help you?")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
