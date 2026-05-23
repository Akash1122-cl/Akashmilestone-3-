import logging
import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from docs_tool import append_to_doc
from gmail_tool import create_email_draft
from slack_tool import post_slack_message
from drive_tool import (
    create_drive_file, 
    create_drive_document, 
    list_drive_files, 
    share_drive_file,
    create_folder,
    save_report_to_drive
)

# Re-create credentials.json from environment variable for Google libraries
if os.environ.get("GOOGLE_CREDENTIALS_JSON"):
    with open("credentials.json", "w") as f:
        f.write(os.environ.get("GOOGLE_CREDENTIALS_JSON"))

logging.basicConfig(level=logging.INFO)
# ---------------- LOGGING SETUP ---------------- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)

# ---------------- APP INIT ---------------- #
app = FastAPI(title="Google MCP Server")


# ---------------- REQUEST SCHEMAS ---------------- #
class AppendDocInput(BaseModel):
    doc_id: str
    content: str


class EmailInput(BaseModel):
    to: str 
    subject: str
    body: str


class DriveFileInput(BaseModel):
    name: str
    content: str
    folder_id: Optional[str] = None


class DriveDocInput(BaseModel):
    name: str
    content: str
    folder_id: Optional[str] = None


class DriveShareInput(BaseModel):
    file_id: str
    email: str
    role: str = "reader"


class DriveFolderInput(BaseModel):
    name: str
    parent_folder_id: Optional[str] = None


class DriveListInput(BaseModel):
    folder_id: Optional[str] = None
    file_type: str = "all"


class SlackNotificationInput(BaseModel):
    channel: str
    message_text: str
    webhook_override: Optional[str] = None


# ---------------- APPROVAL LAYER ---------------- #
def approve(action: str, payload: dict) -> bool:
    """
    Approval system:
    - Local → manual approval
    - Deployment → auto-approved
    """

    # ✅ Auto-approve in deployment (Render sets RENDER=true automatically)
    if os.getenv("AUTO_APPROVE", "false").lower() == "true" or os.getenv("RENDER"):
        logger.info(f"{action} auto-approved (deployment env)")
        return True

    # 🧪 Local CLI approval
    try:
        print("\n-----------------------------")
        print(f"ACTION: {action}")
        print(f"PAYLOAD: {payload}")
        print("-----------------------------")

        decision = input("Approve? (y/n): ").strip().lower()

        if decision == "y":
            logger.info(f"{action} approved")
            return True
        else:
            logger.warning(f"{action} rejected")
            return False

    except Exception as e:
        logger.error(f"Approval error: {e}")
        return False


# ---------------- MCP TOOL LIST ---------------- #
@app.get("/tools")
def list_tools():
    return [
        {
            "name": "append_to_doc",
            "description": "Append content to Google Doc"
        },
        {
            "name": "create_email_draft",
            "description": "Create Gmail draft"
        },
        {
            "name": "create_drive_file",
            "description": "Create a text file in Google Drive"
        },
        {
            "name": "create_drive_document",
            "description": "Create a Google Doc in Drive"
        },
        {
            "name": "list_drive_files",
            "description": "List files in Google Drive"
        },
        {
            "name": "share_drive_file",
            "description": "Share a Drive file with someone"
        },
        {
            "name": "create_drive_folder",
            "description": "Create a folder in Google Drive"
        },
        {
            "name": "send_slack_notification",
            "description": "Send a slack notification to a specific channel about review insights."
        }
    ]


# ---------------- DOC TOOL ---------------- #
@app.post("/append_to_doc")
def run_append(data: AppendDocInput):
    try:
        logger.info("Received request for append_to_doc")

        if not approve("append_to_doc", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        result = append_to_doc(
            doc_id=data.doc_id,
            content=data.content
        )

        logger.info("append_to_doc executed successfully")

        return result

    except Exception as e:
        logger.error(f"Error in append_to_doc: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- EMAIL TOOL ---------------- #
@app.post("/create_email_draft")
def run_email(data: EmailInput):
    try:
        logger.info("Received request for create_email_draft")

        if not approve("create_email_draft", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        result = create_email_draft(
            to=data.to,
            subject=data.subject,
            body=data.body
        )

        logger.info("create_email_draft executed successfully")

        return result

    except Exception as e:
        logger.error(f"Error in create_email_draft: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- DRIVE TOOLS ---------------- #
@app.post("/create_drive_file")
def run_create_drive_file(data: DriveFileInput):
    try:
        logger.info("Received request for create_drive_file")

        if not approve("create_drive_file", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        import asyncio
        result = asyncio.run(create_drive_file(
            name=data.name,
            content=data.content,
            folder_id=data.folder_id
        ))

        logger.info("create_drive_file executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in create_drive_file: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/create_drive_document")
def run_create_drive_document(data: DriveDocInput):
    try:
        logger.info("Received request for create_drive_document")

        if not approve("create_drive_document", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        import asyncio
        result = asyncio.run(create_drive_document(
            name=data.name,
            content=data.content,
            folder_id=data.folder_id
        ))

        logger.info("create_drive_document executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in create_drive_document: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/list_drive_files")
def run_list_drive_files(data: DriveListInput):
    try:
        logger.info("Received request for list_drive_files")

        if not approve("list_drive_files", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        import asyncio
        result = asyncio.run(list_drive_files(
            folder_id=data.folder_id,
            file_type=data.file_type
        ))

        logger.info("list_drive_files executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in list_drive_files: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/share_drive_file")
def run_share_drive_file(data: DriveShareInput):
    try:
        logger.info("Received request for share_drive_file")

        if not approve("share_drive_file", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        import asyncio
        result = asyncio.run(share_drive_file(
            file_id=data.file_id,
            email=data.email,
            role=data.role
        ))

        logger.info("share_drive_file executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in share_drive_file: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@app.post("/create_drive_folder")
def run_create_drive_folder(data: DriveFolderInput):
    try:
        logger.info("Received request for create_drive_folder")

        if not approve("create_drive_folder", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        import asyncio
        result = asyncio.run(create_folder(
            name=data.name,
            parent_folder_id=data.parent_folder_id
        ))

        logger.info("create_drive_folder executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in create_drive_folder: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

# ---------------- SLACK TOOL ---------------- #
@app.post("/send_slack_notification")
def run_slack_notification(data: SlackNotificationInput):
    try:
        logger.info("Received request for send_slack_notification")

        if not approve("send_slack_notification", data.dict()):
            return {
                "status": "rejected",
                "message": "User rejected the action"
            }

        webhook = data.webhook_override or os.getenv("SLACK_WEBHOOK_URL", "")
        if not webhook:
            raise HTTPException(
                status_code=400,
                detail="Slack webhook URL is missing from configuration. Please set SLACK_WEBHOOK_URL."
            )
        
        result = post_slack_message(
            webhook_url=webhook,
            channel=data.channel,
            text=data.message_text
        )

        logger.info("send_slack_notification executed successfully")
        return result

    except Exception as e:
        logger.error(f"Error in send_slack_notification: {e}")
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- HEALTH CHECK ---------------- #
@app.get("/")
def root():
    return {
        "message": "Google MCP Server is running 🚀"
    }