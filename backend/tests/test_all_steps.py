import requests
import json
import time
import os
from pathlib import Path

BASE_URL = "http://localhost:5001"
TEST_FILES_DIR = Path("backend/tests/test_assets")
TEST_FILES_DIR.mkdir(parents=True, exist_ok=True)

test_file_path = TEST_FILES_DIR / "test_doc.txt"
test_file_path.write_text("MiroFish Enterprise is a powerful simulation platform for public opinion analysis. It uses GraphRAG and Swarm agents.", encoding="utf-8")

def log(msg):
    print(f"[TEST] {msg}")

def run_all_steps():
    try:
        # Step 0: Research
        log("Step 0: Testing Web Research...")
        resp0 = requests.post(f"{BASE_URL}/api/research/searchxng", json={
            "query": "MiroFish Enterprise",
            "research_type": "general",
            "max_results": 2
        })
        assert resp0.status_code == 200 and resp0.json()["success"] is True
        log("Step 0 PASSED")

        # Step 1: Graph Extraction
        log("Step 1: Testing Graph Extraction...")
        with open(test_file_path, 'rb') as f:
            files = {'files': (test_file_path.name, f, 'text/plain')}
            data = {
                'simulation_requirement': 'Analyze the impact of MiroFish on the industry',
                'project_name': 'Test Project'
            }
            resp1_1 = requests.post(f"{BASE_URL}/api/graph/ontology/generate", data=data, files=files)

        assert resp1_1.status_code == 200 and resp1_1.json()["success"] is True
        project_id = resp1_1.json()["data"]["project_id"]
        log(f"Ontology generated. Project ID: {project_id}")

        resp1_2 = requests.post(f"{BASE_URL}/api/graph/build", json={
            "project_id": project_id,
            "graph_name": "Test Graph"
        })
        assert resp1_2.status_code == 200 and resp1_2.json()["success"] is True
        task_id = resp1_2.json()["data"]["task_id"]

        while True:
            status_resp = requests.get(f"{BASE_URL}/api/graph/task/{task_id}")
            status_data = status_resp.json()["data"]
            if status_data["status"] == "completed": break
            if status_data["status"] == "failed": raise Exception("Graph build failed")
            time.sleep(2)

        proj_resp = requests.get(f"{BASE_URL}/api/graph/project/{project_id}")
        graph_id = proj_resp.json()["data"]["graph_id"]
        log(f"Graph completed. Graph ID: {graph_id}")

        # Step 2: Simulation Setup
        log("Step 2: Testing Simulation Setup...")
        resp2_1 = requests.post(f"{BASE_URL}/api/simulation/create", json={
            "project_id": project_id,
            "graph_id": graph_id
        })
        assert resp2_1.status_code == 200 and resp2_1.json()["success"] is True
        sim_id = resp2_1.json()["data"]["simulation_id"]

        resp2_2 = requests.post(f"{BASE_URL}/api/simulation/prepare", json={
            "simulation_id": sim_id
        })
        assert resp2_2.status_code == 200 and resp2_2.json()["success"] is True
        prep_task_id = resp2_2.json()["data"]["task_id"]

        while True:
            status_resp = requests.post(f"{BASE_URL}/api/simulation/prepare/status", json={"task_id": prep_task_id})
            status_data = status_resp.json()["data"]
            if status_data["status"] in ["completed", "ready"]: break
            if status_data["status"] == "failed": raise Exception("Simulation prepare failed")
            time.sleep(2)
        log("Simulation prepared.")

        # Step 3: Execution
        log("Step 3: Testing Simulation Execution...")
        resp3 = requests.post(f"{BASE_URL}/api/simulation/start", json={
            "simulation_id": sim_id,
            "max_rounds": 1,
            "force": True
        })
        assert resp3.status_code == 200 and resp3.json()["success"] is True
        time.sleep(5)
        requests.post(f"{BASE_URL}/api/simulation/stop", json={"simulation_id": sim_id})
        log("Simulation run and stopped.")

        # Step 4: Report
        log("Step 4: Testing Report Generation...")
        resp4 = requests.post(f"{BASE_URL}/api/report/generate", json={
            "simulation_id": sim_id
        })
        assert resp4.status_code == 200 and resp4.json()["success"] is True
        rep_task_id = resp4.json()["data"]["task_id"]

        while True:
            status_resp = requests.post(f"{BASE_URL}/api/report/generate/status", json={"task_id": rep_task_id})
            status_data = status_resp.json()["data"]
            if status_data["status"] == "completed": break
            if status_data["status"] == "failed": raise Exception("Report generation failed")
            time.sleep(2)
        log("Report generated.")

        # Step 5: Interview
        log("Step 5: Testing Interview...")
        resp5 = requests.post(f"{BASE_URL}/api/report/chat", json={
            "simulation_id": sim_id,
            "message": "What is the main conclusion?"
        })
        assert resp5.status_code == 200 and resp5.json()["success"] is True
        log("Interview successful.")

        log("\nALL STEPS PASSED SUCCESSFULLY")
    except Exception as e:
        log(f"\nTEST SEQUENCE FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    run_all_steps()
