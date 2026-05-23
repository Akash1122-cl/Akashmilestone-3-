import requests

def test_slack_endpoint():
    payload = {
        "channel": "#product-alerts",
        "message_text": "Hello World! This alert was triggered from my custom MCP tool."
    }
    
    try:
        response = requests.post(
            "http://localhost:8080/send_slack_notification",
            json=payload,
            timeout=10
        )
        print("Status:", response.status_code)
        print("Response:", response.json())
    except Exception as e:
        print(f"Error testing slack tool: {e}")

if __name__ == "__main__":
    test_slack_endpoint()
