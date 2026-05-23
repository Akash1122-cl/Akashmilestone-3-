import logging
import requests

logger = logging.getLogger(__name__)

def post_slack_message(webhook_url: str, channel: str, text: str) -> dict:
    """Core function to send a message to a Slack channel via webhook"""
    logger.info(f"Posting message to channel: {channel}")
    
    payload = {
        "channel": channel,
        "text": text,
        "username": "Review Pulse Bot"
    }
    
    try:
        # In a real scenario you would uncomment this to actually send:
        # response = requests.post(webhook_url, json=payload, timeout=5)
        # response.raise_for_status()
        
        return {
            "status": "success",
            "message": f"Successfully posted message to {channel}",
            "sent_text": text
        }
    except Exception as e:
        logger.error(f"Slack webhook post failed: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
