import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

FDB_REPO_URL = "https://github.com/DanielLin94144/Full-Duplex-Bench.git"
FDB_DIR = Path("../Full-Duplex-Bench")
FDB_V3_DIR = FDB_DIR / "v3"
DATA_DIR = FDB_V3_DIR / "fdb_v3_data_released"
BENCHMARK_JSON = FDB_V3_DIR / "benchmark_data_v2.json"

def check_env():
    print("=== Step 1: Environment Setup ===")
    required_vars = ["LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "GROQ_API_KEY", "ELEVEN_API_KEY"]
    missing = [var for var in required_vars if not os.environ.get(var)]
    if missing:
        print(f"ERROR: Missing required environment variables: {', '.join(missing)}")
        print("Please set these variables to run the FDB-v3 evaluation.")
        sys.exit(1)
    
    # Ensure Windows telemetry log path exists
    Path("C:/tmp").mkdir(exist_ok=True)
    print("Environment variables present. C:/tmp created for telemetry.")

def setup_fdb_repo():
    print("\n=== Step 2: Benchmark Data Preparation ===")
    if not FDB_DIR.exists():
        print("Cloning FDB-v3 repository...")
        subprocess.check_call(["git", "clone", FDB_REPO_URL, str(FDB_DIR)])
    else:
        print("FDB-v3 repository already exists.")

    if not DATA_DIR.exists():
        print(f"ERROR: Benchmark data missing.")
        print(f"Please manually download the FDB-v3 audio dataset and place it in:\n  {DATA_DIR.resolve()}")
        print("This is required to run the inference step.")
        sys.exit(1)
    
    if not BENCHMARK_JSON.exists():
        print(f"ERROR: Benchmark JSON missing at {BENCHMARK_JSON.resolve()}")
        sys.exit(1)

def run_fdb_benchmark():
    print("\n=== Step 3 & 4: Starting Agent & Running Inference ===")
    # Starting our custom agent in the background
    print("Starting agent/livekit_agent.py as the target...")
    agent_process = subprocess.Popen([sys.executable, "agent/livekit_agent.py", "start"])
    
    try:
        # Give the agent a few seconds to connect to the LiveKit room
        print("Waiting for agent to connect to LiveKit Cloud...")
        import time; time.sleep(5)
        
        print("\nStarting FDB-v3 Inference...")
        subprocess.check_call(
            [sys.executable, "run_tool_benchmark_all_released.py", "--provider", "gpt_realtime"],
            cwd=str(FDB_V3_DIR)
        )
    finally:
        print("Stopping agent...")
        agent_process.terminate()
        agent_process.wait()

def run_fdb_evaluation():
    print("\n=== Step 5 & 6: Running Evaluation & Producing Metrics ===")
    print("Running Tool Accuracy Evaluation...")
    subprocess.check_call([
        sys.executable, "evaluate_tool_calls.py",
        "--benchmark", "benchmark_data_v2.json",
        "--results-dir", "fdb_v3_data_released",
        "--provider", "gpt_realtime",
        "--output", "gpt_realtime_evaluation_report.json",
        "--use-llm"
    ], cwd=str(FDB_V3_DIR))
    
    print("\nRunning Pass Rate Evaluation...")
    subprocess.check_call([
        sys.executable, "evaluate_pass_rate.py",
        "--benchmark", "benchmark_data_v2.json",
        "--results-dir", "fdb_v3_data_released",
        "--provider", "gpt_realtime",
        "--output", "gpt_realtime_pass_rate_report.json",
        "--use-llm"
    ], cwd=str(FDB_V3_DIR))

    print("\nFDB-v3 Pipeline complete. Reports generated in the FDB repository directory.")

if __name__ == "__main__":
    print("=== Samsung PRISM Theme 05 FDB-v3 Reproduction Script ===")
    check_env()
    setup_fdb_repo()
    run_fdb_benchmark()
    run_fdb_evaluation()
