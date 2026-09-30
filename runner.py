import sys
import json
import asyncio
from typing import Any, Dict
from agent.core import Agent
from agent.multimodal import MultimodalProcessor

async def process_event_stream():
    agent = Agent()
    processor = MultimodalProcessor()
    
    loop = asyncio.get_event_loop()
    
    async def event_reader():
        if len(sys.argv) > 1:
            # Read from file to avoid Windows connect_read_pipe bug with stdin redirection
            with open(sys.argv[1], 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        if data.get("type") in ["text", "audio", "video"]:
                            processed = processor.process(data)
                            if processed.get("type") == "clarification":
                                await agent.emit(processed)
                                continue
                            else:
                                data = processed
                        await agent.process_event(data)
                        # Small sleep to allow agent to process before next line
                        await asyncio.sleep(0.05)
                    except json.JSONDecodeError:
                        continue
            return
            
        # Fallback to stdin (fails on Windows with Proactor if redirected from file, but fine if interactive)
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)
        
        while True:
            line = await reader.readline()
            if not line:
                break
            try:
                data = json.loads(line.decode('utf-8'))
                
                # Multimodal preprocessing if applicable
                if data.get("type") in ["text", "audio", "video"]:
                    processed = processor.process(data)
                    if processed.get("type") == "clarification":
                        await agent.emit(processed)
                        continue
                    else:
                        data = processed
                
                await agent.process_event(data)
            except json.JSONDecodeError:
                continue

    async def event_writer():
        while True:
            msg = await agent.output_queue.get()
            print(json.dumps(msg), flush=True)
            
    # Run both
    reader_task = asyncio.create_task(event_reader())
    writer_task = asyncio.create_task(event_writer())
    
    await reader_task
    # Wait for background tasks to complete
    if agent.running_tasks:
        tasks = [info["task"] for info in agent.running_tasks.values()]
        await asyncio.gather(*tasks, return_exceptions=True)
    # Allow some time for final events to flush
    await asyncio.sleep(0.1)
    writer_task.cancel()

if __name__ == "__main__":
    asyncio.run(process_event_stream())
