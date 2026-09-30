# Samsung PRISM GenAI Hackathon 2026 - Demo Script

This folder contains the script for our 3-5 minute demo video.

## Demo Video Outline

### PART A: FDB-v3 Benchmark Interruption (0:00 - 1:30)
**Narration:** "Welcome to our Theme 05 submission. We've built an interruptible agent using LiveKit. Let's look at the core benchmark requirement."
**Action:** 
- Run `python runner.py demo_input.jsonl` in the terminal to simulate the FDB-v3 structural evaluation.
- Show the console output stopping the `Delhi -> Mumbai` task.
- Highlight the `stale_result_ignored` struct ensuring generation integrity.

### PART B: Extension Use Case (1:30 - 3:30)
**Narration:** "Now let's see our practical extension: the In-Car Destination Change Assistant."
**Action:**
- Run `python runner.py demo_extension_input.jsonl`.
- Show the agent receiving the prompt: *"Navigate to Chennai Central"*.
- Show the immediate interruption: *"Actually, take me to VIT Vellore"*.
- Highlight that the routing engine ignores the Chennai calculation and correctly outputs the route to VIT Vellore.
**Narration:** "This demonstrates real-time full-duplex self-correction without blocking the driver's UX."

### PART C: Reproduction (3:30 - 4:00)
**Narration:** "Our entire setup is easily reproducible using our one-command script."
**Action:**
- Show the command `python reproduce.py`.
- Emphasize the clean environment checking and LiveKit dependencies installing natively.
