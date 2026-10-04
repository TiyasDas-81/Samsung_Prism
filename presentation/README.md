# Samsung PRISM GenAI Hackathon 2026 - Theme 05
## Presentation Outline (8 Slides)

**Slide 1: Problem / Motivation**
- LLM agents traditionally block on tool execution.
- Real-world voice conversations (e.g. driving assistants) demand real-time interruption and self-correction.
- Theme 05 challenges us to build an interruptible agent resisting stale data mutations.

**Slide 2: Theme 05 Requirements**
- Fast Path: Acknowledge immediately.
- Slow Path: Async background tool execution.
- Full-Duplex: Graceful interruption handling and state rollback prevention.
- Evaluation: LiveKit Voice Agent via FDB-v3.

**Slide 3: Architecture**
- `livekit_agent.py`: WebRTC LiveKit Voice Pipeline (STT -> LLM -> TTS).
- `core.py`: Concurrency-safe event processing loop.
- `state.py`: Generational state snapshotting.

**Slide 4: LiveKit + FDB-v3 Integration**
- Built on `livekit-agents` and `livekit-plugins-openai`.
- Uses `llm.ai_callable` plugins delegating to our internal coordination engine to ensure tool calls do not block the VAD/STT threads.
- FDB-v3 compatibility achieved through standard LiveKit entrypoints.

**Slide 5: Interruption / Cancellation Mechanism**
- Interruptions increment the `generation` counter on `SessionState`.
- Active async tasks map to a stale generation.
- Tasks are either `asyncio.CancelledError` aborted or allowed to complete and structurally ignored (`stale_result_ignored`).

**Slide 6: Benchmark Results (FDB-v3)**
- **Status:** *Full FDB-v3 benchmark is currently in progress.*
- Single-sample end-to-end validation has been successfully completed with 100% tool selection and argument accuracy on the local pipeline.

**Slide 7: Extension Use Case - In-Car Assistant**
- **Scenario:** Driver navigates to "Chennai Central", then corrects to "VIT Vellore".
- **Execution:** The initial routing is canceled/ignored in real-time. The agent routes to the new destination without duplicate state mutation or UX blocking.

**Slide 8: Conclusion / Next Steps**
- Built a highly robust, full-duplex conversational coordinator.
- Solves LLM latency bottlenecks elegantly.
- Next Step: Enterprise-scale cloud deployment.
