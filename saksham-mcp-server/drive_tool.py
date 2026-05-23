"""
Google Drive API integration for MCP Server
Provides file creation, upload, and management capabilities
"""

import logging
import os
from typing import Dict, Any, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload
import io

from auth import get_creds

logger = logging.getLogger(__name__)

async def create_drive_file(name: str, content: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a new text file in Google Drive"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare file metadata
        file_metadata = {
            'name': name,
            'mimeType': 'text/plain'
        }
        
        # Add folder if specified
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create file content
        media = MediaIoBaseUpload(
            io.BytesIO(content.encode('utf-8')),
            mimetype='text/plain',
            resumable=True
        )
        
        # Create the file
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,size,createdTime'
        ).execute()
        
        logger.info(f"Created Drive file: {file.get('name')} (ID: {file.get('id')})")
        
        return {
            "status": "success",
            "message": "File created in Google Drive",
            "file_id": file.get('id'),
            "file_name": file.get('name'),
            "file_size": file.get('size'),
            "created_time": file.get('createdTime')
        }
        
    except HttpError as error:
        logger.error(f"Google Drive API error: {error}")
        return {
            "status": "error",
            "message": "Google Drive API error",
            "details": str(error)
        }
    except Exception as e:
        logger.error(f"Error creating Drive file: {e}")
        return {
            "status": "error",
            "message": "Failed to create Drive file",
            "details": str(e)
        }

async def create_drive_document(name: str, content: str, folder_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a Google Doc in Google Drive"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare file metadata for Google Doc
        file_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.document'
        }
        
        # Add folder if specified
        if folder_id:
            file_metadata['parents'] = [folder_id]
        
        # Create the Google Doc
        file = service.files().create(
            body=file_metadata,
            fields='id,name,size,createdTime'
        ).execute()
        
        # Now add content to the document using Docs API
        from docs_tool import append_to_doc
        docs_result = await append_to_doc(file.get('id'), content)
        
        logger.info(f"Created Drive document: {file.get('name')} (ID: {file.get('id')})")
        
        return {
            "status": "success",
            "message": "Google Doc created in Drive",
            "file_id": file.get('id'),
            "file_name": file.get('name'),
            "created_time": file.get('createdTime'),
            "docs_result": docs_result
        }
        
    except HttpError as error:
        logger.error(f"Google Drive API error: {error}")
        return {
            "status": "error",
            "message": "Google Drive API error",
            "details": str(error)
        }
    except Exception as e:
        logger.error(f"Error creating Drive document: {e}")
        return {
            "status": "error",
            "message": "Failed to create Drive document",
            "details": str(e)
        }

async def list_drive_files(folder_id: Optional[str] = None, file_type: str = 'all') -> Dict[str, Any]:
    """List files in Google Drive"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Build query
        query = "trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"
        
        if file_type == 'docs':
            query += " and mimeType='application/vnd.google-apps.document'"
        elif file_type == 'sheets':
            query += " and mimeType='application/vnd.google-apps.spreadsheet'"
        elif file_type == 'text':
            query += " and mimeType='text/plain'"
        
        # List files
        results = service.files().list(
            q=query,
            pageSize=10,
            fields="files(id,name,size,mimeType,createdTime,modifiedTime)"
        ).execute()
        
        files = results.get('files', [])
        
        logger.info(f"Found {len(files)} files in Drive")
        
        return {
            "status": "success",
            "files": files,
            "count": len(files)
        }
        
    except HttpError as error:
        logger.error(f"Google Drive API error: {error}")
        return {
            "status": "error",
            "message": "Google Drive API error",
            "details": str(error)
        }
    except Exception as e:
        logger.error(f"Error listing Drive files: {e}")
        return {
            "status": "error",
            "message": "Failed to list Drive files",
            "details": str(e)
        }

async def share_drive_file(file_id: str, email: str, role: str = 'reader') -> Dict[str, Any]:
    """Share a Drive file with someone"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Create permission
        permission = {
            'type': 'user',
            'role': role,
            'emailAddress': email
        }
        
        result = service.permissions().create(
            fileId=file_id,
            body=permission,
            fields='id,type,role,emailAddress,displayName'
        ).execute()
        
        logger.info(f"Shared file {file_id} with {email} as {role}")
        
        return {
            "status": "success",
            "message": f"File shared with {email}",
            "permission_id": result.get('id'),
            "role": result.get('role'),
            "email": result.get('emailAddress')
        }
        
    except HttpError as error:
        logger.error(f"Google Drive API error: {error}")
        return {
            "status": "error",
            "message": "Google Drive API error",
            "details": str(error)
        }
    except Exception as e:
        logger.error(f"Error sharing Drive file: {e}")
        return {
            "status": "error",
            "message": "Failed to share Drive file",
            "details": str(e)
        }

async def create_folder(name: str, parent_folder_id: Optional[str] = None) -> Dict[str, Any]:
    """Create a folder in Google Drive"""
    try:
        creds = get_creds()
        service = build('drive', 'v3', credentials=creds)
        
        # Prepare folder metadata
        folder_metadata = {
            'name': name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        # Add parent folder if specified
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        # Create the folder
        folder = service.files().create(
            body=folder_metadata,
            fields='id,name,size,createdTime'
        ).execute()
        
        logger.info(f"Created folder: {folder.get('name')} (ID: {folder.get('id')})")
        
        return {
            "status": "success",
            "message": "Folder created in Google Drive",
            "folder_id": folder.get('id'),
            "folder_name": folder.get('name'),
            "created_time": folder.get('createdTime')
        }
        
    except HttpError as error:
        logger.error(f"Google Drive API error: {error}")
        return {
            "status": "error",
            "message": "Google Drive API error",
            "details": str(error)
        }
    except Exception as e:
        logger.error(f"Error creating folder: {e}")
        return {
            "status": "error",
            "message": "Failed to create folder",
            "details": str(e)
        }

# Utility functions for common operations
async def create_review_pulse_folder() -> Dict[str, Any]:
    """Create a main folder for Review Pulse reports"""
    return await create_folder("Review Pulse Reports")

async def create_report_folder(product_id: str, date_str: str) -> Dict[str, Any]:
    """Create a folder for a specific product report"""
    folder_name = f"Report_{product_id}_{date_str}"
    return await create_folder(folder_name)

async def save_report_to_drive(product_id: str, report_content: str, report_date: str, 
                            share_with: Optional[list] = None) -> Dict[str, Any]:
    """Complete workflow to save a report to Drive"""
    try:
        # Create main folder if needed
        main_folder = await create_review_pulse_folder()
        if main_folder.get("status") != "success":
            return main_folder
        
        # Create product-specific folder
        product_folder = await create_report_folder(product_id, report_date)
        if product_folder.get("status") != "success":
            return product_folder
        
        # Create the report document
        doc_name = f"Review_Report_{product_id}_{report_date}"
        doc_result = await create_drive_document(
            doc_name, 
            report_content, 
            product_folder.get("folder_id")
        )
        
        # Share with stakeholders if specified
        if share_with and doc_result.get("status") == "success":
            file_id = doc_result.get("file_id")
            for email in share_with:
                await share_drive_file(file_id, email, 'reader')
        
        return doc_result
        
    except Exception as e:
        logger.error(f"Error in save_report_to_drive workflow: {e}")
        return {
            "status": "error",
            "message": "Failed to save report to Drive",
            "details": str(e)
        }
