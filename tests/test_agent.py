import pytest
import asyncio
from agent.core import Agent
from agent.multimodal import MultimodalProcessor

@pytest.mark.asyncio
async def test_fast_ack():
    agent = Agent()
    await agent.process_event({
        "type": "user_input",
        "text": "Hello",
        "intent": "greet"
    })
    
    ack_event = await agent.output_queue.get()
    assert ack_event["type"] == "ack"
    
    snapshot_event = await agent.output_queue.get()
    assert snapshot_event["type"] == "state_snapshot"
    assert snapshot_event["snapshot"]["intent"] == "greet"
    assert "event_id" in ack_event
    assert "timestamp" in ack_event

@pytest.mark.asyncio
async def test_interruption_recovery():
    agent = Agent()
    # User asks for Delhi
    await agent.process_event({
        "type": "user_input",
        "text": "Navigate to Delhi",
        "intent": "navigate",
        "slots": {"destination": "Delhi"},
        "tool": "navigate"
    })
    
    ack1 = await agent.output_queue.get()
    snap1 = await agent.output_queue.get()
    call1 = await agent.output_queue.get()
    assert call1["type"] == "tool_call"
    assert call1["args"]["destination"] == "Delhi"
    
    # Interrupt with Mumbai
    await agent.process_event({
        "type": "interruption",
        "text": "Actually Mumbai",
        "intent": "navigate",
        "slots": {"destination": "Mumbai"},
        "tool": "navigate"
    })
    
    ack2 = await agent.output_queue.get()
    snap2 = await agent.output_queue.get()
    cancel_event = await agent.output_queue.get()
    assert cancel_event["type"] == "tool_cancelled"
    assert cancel_event["call_id"] == call1["call_id"]
    
    call2 = await agent.output_queue.get()
    assert call2["type"] == "tool_call"
    assert call2["args"]["destination"] == "Mumbai"

@pytest.mark.asyncio
async def test_duplicate_state_changing_action():
    agent = Agent()
    # First booking
    await agent.process_event({
        "type": "user_input",
        "intent": "navigate",
        "slots": {"destination": "Delhi"},
        "tool": "navigate"
    })
    
    ack1 = await agent.output_queue.get()
    snap1 = await agent.output_queue.get()
    call1 = await agent.output_queue.get()
    
    # Wait for completion
    await asyncio.sleep(0.6)
    res1 = await agent.output_queue.get()
    assert res1["type"] == "tool_result"
    final1 = await agent.output_queue.get()
    
    # Duplicate event
    await agent.process_event({
        "type": "user_input",
        "intent": "navigate",
        "slots": {"destination": "Delhi"},
        "tool": "navigate"
    })
    
    ack2 = await agent.output_queue.get()
    snap2 = await agent.output_queue.get()
    error = await agent.output_queue.get()
    assert error["type"] == "tool_error"
    assert "Duplicate state-changing call prevented." in error["error"]

@pytest.mark.asyncio
async def test_late_stale_result():
    agent = Agent()
    # User asks for Delhi
    await agent.process_event({
        "type": "user_input",
        "intent": "navigate",
        "slots": {"destination": "Delhi"},
        "tool": "navigate"
    })
    
    await agent.output_queue.get() # ack
    await agent.output_queue.get() # snap
    call1 = await agent.output_queue.get() # call
    
    # Interrupt with Mumbai before Delhi completes
    await agent.process_event({
        "type": "user_input",
        "intent": "navigate",
        "slots": {"destination": "Mumbai"},
        "tool": "navigate"
    })
    
    await agent.output_queue.get() # ack
    await agent.output_queue.get() # snap
    cancel = await agent.output_queue.get() # cancel
    call2 = await agent.output_queue.get() # call2
    
    # Wait for tasks to complete
    await asyncio.sleep(0.6)
    
    # The first task was invalidated so it will produce a stale_result_ignored
    stale_res = await agent.output_queue.get()
    assert stale_res["type"] == "stale_result_ignored"
    
    # The second task should complete successfully
    res2 = await agent.output_queue.get()
    assert res2["type"] == "tool_result"
    assert res2["call_id"] == call2["call_id"]
    
@pytest.mark.asyncio
async def test_slot_correction_preserves_unaffected():
    agent = Agent()
    await agent.process_event({
        "type": "user_input",
        "slots": {"destination": "Delhi", "date": "tomorrow"}
    })
    
    await agent.output_queue.get()
    snap1 = await agent.output_queue.get()
    assert snap1["snapshot"]["slots"] == {"destination": "Delhi", "date": "tomorrow"}
    
    await agent.process_event({
        "type": "user_input",
        "slots": {"destination": "Mumbai"}
    })
    
    await agent.output_queue.get()
    snap2 = await agent.output_queue.get()
    assert snap2["snapshot"]["slots"] == {"destination": "Mumbai", "date": "tomorrow"}

@pytest.mark.asyncio
async def test_invalid_tool_schema():
    agent = Agent()
    await agent.process_event({
        "type": "user_input",
        "intent": "navigate",
        "slots": {"destination": 123}, # Invalid type, should be string
        "tool": "navigate"
    })
    
    await agent.output_queue.get() # ack
    await agent.output_queue.get() # snap
    err = await agent.output_queue.get()
    assert err["type"] == "tool_error"
    assert "Argument destination must be string" in err["error"]

@pytest.mark.asyncio
async def test_multimodal_ambiguity():
    processor = MultimodalProcessor()
    res = processor.process({
        "type": "audio",
        "reference": "audio_1",
        "payload_metadata": {"ambiguous": True}
    })
    assert res["type"] == "clarification"
    
    res2 = processor.process({
        "type": "video",
        "reference": "video_1",
        "payload_metadata": {"intent": "find_object"}
    })
    assert res2["type"] == "user_input"
    assert "mock perception" in res2["text"]

@pytest.mark.asyncio
async def test_uncancellable_tool_late_result():
    agent = Agent()
    call_id = "test_call_1"
    expected_gen = agent.state.current.generation
    # Simulate generation advancing
    agent.state.current.update_slots({"new": "slot"})
    # Now manually call execute_tool_async to simulate a tool that didn't cancel and returned
    await agent.execute_tool_async(call_id, "search_flights", {"destination": "Delhi", "date": "tomorrow"}, expected_gen, "key")
    res = await agent.output_queue.get()
    assert res["type"] == "stale_result_ignored"

@pytest.mark.asyncio
async def test_different_actions_not_deduplicated():
    agent = Agent()
    await agent.process_event({"type": "user_input", "intent": "navigate", "slots": {"destination": "Delhi"}, "tool": "navigate"})
    await agent.output_queue.get()
    await agent.output_queue.get()
    await agent.output_queue.get()
    
    # Wait for first one to finish
    await asyncio.sleep(0.6)
    await agent.output_queue.get() # tool_result
    await agent.output_queue.get() # final_response
    
    await agent.process_event({"type": "user_input", "intent": "navigate", "slots": {"destination": "Mumbai"}, "tool": "navigate"})
    await agent.output_queue.get()
    await agent.output_queue.get()
    # Should emit tool_call, not tool_error because the dedup key is different
    event = await agent.output_queue.get()
    assert event["type"] == "tool_call"