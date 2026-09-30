# SamsungPrism Theme 05 Agent Architecture

This project provides a robust, event-driven agent architecture aligning with Samsung PRISM Theme 05.

## Architecture
The system consists of the following modules:
- `agent/core.py`: The Coordination Layer handling incoming evaluator events (user input, interruptions, multimodal results), launching tasks, validating generations, and ensuring strict concurrency control.
- `agent/state.py`: Manages the `SessionState` and incremental `StateSnapshot` handling versioned slots and intent histories to safely detect interruptions and state modifications.
- `agent/tools.py`: A `ToolRegistry` schema-driven subsystem allowing tools to mark themselves as `read_only` or `state_modifying`.
- `agent/multimodal.py`: A lightweight adapter layer to handle multimodal representations (text, audio/WAV refs, video/PNG frame refs) outputting unified perception events to feed to the Core.

## Event Protocol
The agent communicates via a structured event protocol. Every I/O event includes:
- `event_id`
- `timestamp`
- `type`
- `call_id` (where applicable)
- `state_snapshot` (where applicable)

### Input/Output Event Types
- `user_input`
- `interruption`
- `tool_call`
- `tool_cancelled`
- `tool_result`
- `stale_result_ignored`
- `clarification`
- `final_response`
- `state_snapshot`

## Interruption Handling & Stale Result Protection
The agent maintains an active generation version. An interruption is detected when:
1. `cancel_ongoing` flag is explicitly requested.
2. An event structurally changes active intent or slots (modifying generation).

When a conflict is detected:
- Existing async tool tasks are identified as obsolete.
- `tool_cancelled` events are emitted.
- If an interrupted task manages to return late, it is structurally rejected (yielding a `stale_result_ignored` event).

### Example Interruption Scenario
1. User requests: `Book a flight to Delhi` -> `book_flight(destination="Delhi")` begins execution.
2. User interrupts with: `Actually Mumbai`.
3. Agent overrides destination slot to `Mumbai`. This bumps the state generation.
4. Agent cancels the `Delhi` task execution, emits `tool_cancelled`, and launches `book_flight(destination="Mumbai")`.
5. If the `Delhi` task fails to halt in time and yields a result late, the Core ignores it due to generation mismatch and emits `stale_result_ignored`.

## Tool Schemas
The `ToolRegistry` natively integrates input argument validation. A tool defines its signature using:
- Target parameter types (`string`, `integer`, `boolean`)
- State modification flags
- List of `required` properties

Invalid inputs emitted via JSON instantly result in a structured `tool_error` rejecting execution.

## Idempotency
Duplicate active-state modifying actions are robustly prevented. The system hashes the tool namespace alongside a normalized combination of specific parameters and `session_id`, rejecting duplication events but dynamically allowing inherently different mutations (e.g. `Delhi` vs `Mumbai`).

## Multimodal Adapter
Audio/Video processing operates smoothly as an adapter mapping. It accepts explicit refs (`reference`) or structural schema blocks (`payload_metadata`). Ambiguous requests automatically trigger a `clarification` intent.

## Running the Agent
A lightweight runner is provided to test evaluator inputs via standard I/O:
```bash
python runner.py
```
*(Accepts standard JSON-line inputs and prints JSON-line outputs.)*

## Running Tests
Run the entire suite of race conditions and functionality checks:
```bash
python -m pytest tests/ -q
```
