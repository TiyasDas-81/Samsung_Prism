# Samsung PRISM Theme 05 - Demo Script

## Recording Constraints & Setup
*   **Target Duration**: 3-5 minutes
*   **Screen Layout**: Left half showing a Command Prompt/Terminal, Right half showing code or browser (if applicable).
*   **Preparation**: Ensure `reproduce.py` is ready and API keys are set securely in your environment (do not show them on screen).

---

## A. Brief Introduction (0:00 - 0:30)

**Narration**: 
"Hello, this is the demo for Samsung PRISM Theme 05. Our project solves the critical problem of LLM agents blocking on tool execution. In real-world voice conversations, such as with in-car assistants, users frequently self-correct or interrupt. Normal agents mutate state sequentially and fail gracefully. Our solution introduces a generational coordination layer that processes tools asynchronously, cleanly rejecting stale results upon user interruption."

**Visual**: Show the project `README.md` and the 8-slide PPT architecture diagram.

---

## B. REAL FDB-v3 Interruption Demo (0:30 - 2:00)

**Action**: 
In the terminal, run the deterministic simulator for FDB-v3 trace:
`python runner.py demo_input.jsonl`

**Narration**:
"First, let's look at the core FDB-v3 benchmark behavior. I am starting the agent simulator."
*(Wait for script output)*
"Here, the user asks to book a train from Delhi to Mumbai, but mid-sentence interrupts and changes the destination to Bangalore. Watch the terminal output. As the agent acknowledges the speech, the coordination layer immediately increments the generation counter. The stale async task for the 'Mumbai' booking is cleanly structurally ignored, and the new 'Bangalore' task is processed. The stale action does not incorrectly survive."

**Visual**: Highlight the terminal log line where it says `stale_result_ignored` or similar generation increment logs.

---

## C. Technical Behavior Walkthrough (2:00 - 3:00)

**Narration**:
"Under the hood, our fast-path immediately acknowledges the user's audio over LiveKit WebRTC, keeping latency low. The slow-path pushes the tool execution into `asyncio` background tasks. If the VAD detects new speech—an interruption—the active state generation increments. Any returning background task with an older generation ID is discarded. This guarantees idempotency and protects against race conditions."

**Visual**: Briefly display `agent/core.py` showing the `generation` check logic.

---

## D. Extension Demonstration: In-Car Assistant (3:00 - 4:30)

**Action**:
In the terminal, run the extension use case:
`python runner.py demo_extension_input.jsonl`

**Narration**:
"Now, let's run our extension use-case: an In-Car Destination Change Assistant. 
The driver says: 'Navigate to Chennai Central'. The agent starts the slow routing calculation. 
Then the driver interrupts: 'Actually, take me to VIT Vellore'. 
As you can see in the logs, the agent detects the interruption. It gracefully cancels the Chennai routing task, drops its stale data, and seamlessly computes and processes the route for VIT Vellore."

**Visual**: Highlight the exact logs showing `Destination: Chennai` being canceled, and `Destination: VIT Vellore` succeeding.

---

## E. Closing (4:30 - 5:00)

**Narration**:
"To summarize, we demonstrated a fully functional LiveKit WebRTC voice agent capable of handling real-world human disfluencies and interruptions. It successfully passes the strict FDB-v3 full-duplex requirements and extends perfectly into practical applications like automotive voice assistants. Thank you."

**Visual**: Show the final GitHub repository page or the `presentation/Samsung_PRISM_Theme05.pptx` concluding slide.
