# SamsungPrism Theme 05 Agent Architecture

This project provides a robust, event-driven agent architecture aligning with Samsung PRISM Theme 05. It implements a **LiveKit Voice Agent** that is designed for evaluation with **FULL-DUPLEX-BENCH v3 (FDB-v3)**.

## Architecture
The system consists of the following modules:
- `agent/livekit_agent.py`: The LiveKit Voice Pipeline Agent adapter. It interfaces with the official Python `livekit-agents` and `livekit-plugins-openai` SDKs to process real-time voice, handling STT, LLM, and TTS generation asynchronously.
- `agent/core.py`: The Coordination Layer handling incoming evaluator events (user input, interruptions, multimodal results), launching tasks, validating generations, and ensuring strict concurrency control.
- `agent/state.py`: Manages the `SessionState` and incremental `StateSnapshot` handling versioned slots and intent histories to safely detect interruptions and state modifications.
- `agent/tools.py`: A `ToolRegistry` schema-driven subsystem allowing tools to mark themselves as `read_only` or `state_modifying`.
- `agent/multimodal.py`: A lightweight adapter layer to handle multimodal representations.

## Fast Path & Slow Path
- **Fast Path**: Immediately acknowledges the user's speech while emitting an updated `state_snapshot` before queueing slow tool execution.
- **Slow Path**: Runs tool executions in the background via `asyncio`, keeping the LiveKit voice loop unblocked.

## Interruption Handling & Stale Result Protection
The agent maintains an active generation version. An interruption is detected when:
1. `cancel_ongoing` flag is explicitly requested.
2. An event structurally changes active intent or slots (modifying generation).

When a conflict is detected:
- Existing async tool tasks are identified as obsolete.
- `tool_cancelled` events are emitted.
- If an interrupted task manages to return late, it is structurally rejected (yielding a `stale_result_ignored` event).

## Idempotency
Duplicate active-state modifying actions are robustly prevented. The system hashes the tool namespace alongside a normalized combination of specific parameters and `session_id`, rejecting duplication events but dynamically allowing inherently different mutations.

## FDB-v3 Integration and Model Provider
- **Model Provider**: Groq (LLM/STT) and ElevenLabs (TTS) via `livekit-agents` plugins.
- **FDB-v3 Evaluation**: Designed to interact with the FDB-v3 benchmark suite via standard LiveKit SDK patterns.

## Installation & Setup
To run the benchmark and agent, install the exact dependencies:
```bash
pip install -r requirements.txt
```

### Setup Requirements
1. **LiveKit**: Create a project at [LiveKit Cloud](https://cloud.livekit.io/) and generate API keys.
2. **Groq**: Obtain a free API key from [Groq Console](https://console.groq.com/).
3. **ElevenLabs**: Obtain a free API key from [ElevenLabs](https://elevenlabs.io/).

You must set the following environment variables before running:
- `LIVEKIT_URL`
- `LIVEKIT_API_KEY`
- `LIVEKIT_API_SECRET`
- `GROQ_API_KEY`
- `ELEVEN_API_KEY`

### FDB-v3 Data Placement
To run the evaluation, you must manually download the FDB-v3 audio dataset and place the extracted `fdb_v3_data_released` directory inside the adjacent `../Full-Duplex-Bench/v3/` folder. The `reproduce.py` script will alert you if this is missing.

### CPU Compatibility & Environment Modifications
- **Python Version**: Python 3.11 is strictly recommended.
- **CPU Fallback**: The FDB benchmark evaluation framework (`nemo_toolkit`) natively attempts CUDA execution. We have successfully verified execution on CPU-only machines by explicitly falling back to CPU decoding where CUDA is unavailable.
- **Nemo Hotfix**: On some Python 3.11 + Windows installations, the `nemo_toolkit` library (`nemo/utils/tar_utils.py`) requires a manual removal of the `filter="data"` argument in `tarfile.extractall()` if it throws a TypeError.

## Running the Reproduction Script
A 1-command reproduction script is provided. It verifies the environment, attempts to run the FDB-v3 benchmark, and starts the LiveKit Voice Agent:
```bash
python reproduce.py
```

## Benchmark Use Case (FDB-v3)
The core benchmark trace involves booking a train (Delhi → Mumbai) and interrupting to (Mumbai → Bangalore). The system emits structured JSON protocol events mapping generation changes and rejecting stale data.

**Actual Benchmark Results (Partial due to Groq rate limits, 30 scenarios processed):**
- **Tool Selection Accuracy**: 77.3%
- **Argument Accuracy**: 47.0%
- **Strict Pass Rate**: 33.3%
- **Response Quality / Latency Metrics**: Could not be fully evaluated locally as it requires `OPENAI_API_KEY`/`GPT-4o`, which was intentionally excluded.
- **Failures**: 20/30 failed due to wrong tools/arguments, heavily influenced by the fallback open-weight model (`qwen/qwen3.8-27b` hitting limits).

## Presentation

The final presentation is available in:
presentation/Samsung_PRISM_Theme05.pptx

## Demo Video
**Samsung PRISM Theme 05 Demo Video**

Google Drive:
https://drive.google.com/file/d/1ac-vMTNtxWv0EQ23cXAe0jKAOL8omMqS/view?usp=sharing
## Extension Use Case: In-Car Destination Change Assistant
We built an end-to-end practical extension: **In-Car Destination Change Assistant**.
- User says: *"Navigate to Chennai Central."*
- Agent begins a slow routing calculation.
- User interrupts: *"Actually, take me to VIT Vellore."*
- Agent detects the interruption, increments the generation, and gracefully cancels the Chennai routing. If the Chennai routing task returns late, the coordination layer ignores it (`stale_result_ignored`) and safely calculates the route to VIT Vellore.

To view the deterministic event trace for this extension, run:
```bash
python runner.py demo_extension_input.jsonl
```

## Running Local Tests
Run the entire suite of race conditions and functionality checks:
```bash
python -m pytest tests/ -q
```

## Limitations & AI Disclosure
- See `AI_DISCLOSURE.md` for generative AI usage statements.
- The multimodal adapter is an interface routing layer; it does not currently perform native visual semantic inference but standardizes inputs for the core agent.
