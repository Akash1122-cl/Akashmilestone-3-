
import requests
import time
import subprocess
import os
import json
import webbrowser

# Configuration
PHASE2_URL = "http://localhost:8001"
PHASE4_URL = "http://localhost:8003"

def start_service(path, port):
    print(f"Starting service in {path} on port {port}...")
    # Use python directly since we are in a script
    process = subprocess.Popen(
        ["python", "src/main.py"],
        cwd=path,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return process

def wait_for_service(url, name):
    print(f"Waiting for {name} to be ready at {url}...")
    for _ in range(30):
        try:
            response = requests.get(f"{url}/health")
            if response.status_code == 200:
                print(f"{name} is ready!")
                return True
        except:
            pass
        time.sleep(2)
    print(f"{name} failed to start.")
    return False

def run_demo():
    # 1. Start services
    p2 = start_service("phase2", 8001)
    p4 = start_service("phase4", 8003)
    
    try:
        if not wait_for_service(PHASE2_URL, "Phase 2") or not wait_for_service(PHASE4_URL, "Phase 4"):
            return

        # 2. Sample Data
        reviews = [
            {
                "external_review_id": "rev1",
                "title": "Great App",
                "review_text": "I love the UI and the performance is smooth.",
                "author_name": "John Doe",
                "rating": 5,
                "review_date": "2024-01-01",
                "review_url": "http://example.com",
                "version": "1.0.0",
                "source": "App Store",
                "product_id": 123
            },
            {
                "external_review_id": "rev2",
                "title": "Buggy",
                "review_text": "The app crashes when I open the settings.",
                "author_name": "Jane Smith",
                "rating": 2,
                "review_date": "2024-01-02",
                "review_url": "http://example.com",
                "version": "1.0.0",
                "source": "Google Play",
                "product_id": 123
            }
        ]

        print("Step 1: Processing reviews through Phase 2...")
        response = requests.post(f"{PHASE2_URL}/process/complete", json={"reviews": reviews})
        if response.status_code != 200:
            print(f"Phase 2 processing failed: {response.text}")
            return
        
        processing_result = response.json()
        print("Phase 2 processing successful!")
        
        # 3. Mock Analysis Result
        # Since Phase 3 (Analysis) requires Postgres, we mock its output for Phase 4
        analysis_result = {
            "product_id": 123,
            "total_reviews": 2,
            "sentiment_summary": {"positive": 1, "negative": 1, "neutral": 0},
            "timestamp": "2024-01-01T00:00:00"
        }
        themes = [
            {
                "name": "User Interface",
                "sentiment": "positive",
                "description": "Users are happy with the visual design.",
                "reviews_count": 1
            },
            {
                "name": "Stability",
                "sentiment": "negative",
                "description": "Frequent crashes reported in settings.",
                "reviews_count": 1
            }
        ]

        print("Step 2: Generating report through Phase 4...")
        report_request = {
            "analysis_result": analysis_result,
            "themes": themes,
            "output_format": "html"
        }
        response = requests.post(f"{PHASE4_URL}/api/v1/generate-full-report", json=report_request)
        if response.status_code != 200:
            print(f"Phase 4 report generation failed: {response.text}")
            return
        
        report_result = response.json()
        print("Phase 4 report generation successful!")
        
        # 4. Save and Show Report
        html_content = report_result.get("formatted_report", {}).get("content", "")
        if html_content:
            report_file = "demo_report.html"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            print(f"Demo report saved to {os.path.abspath(report_file)}")
            # webbrowser.open(f"file://{os.path.abspath(report_file)}")
        else:
            print("No HTML content found in report result.")

    finally:
        print("Cleaning up services...")
        p2.terminate()
        p4.terminate()

if __name__ == "__main__":
    run_demo()
