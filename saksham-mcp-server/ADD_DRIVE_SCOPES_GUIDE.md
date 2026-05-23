# Step-by-Step Guide: Add Google Drive Scopes to OAuth

## 🎯 Goal
Add these two scopes to your OAuth consent screen:
- `https://www.googleapis.com/auth/drive`
- `https://www.googleapis.com/auth/drive.file`

## 📋 Prerequisites
- Google Cloud Console access
- Project: `mile-stone-3`
- Existing OAuth consent screen

---

## 🔧 Step 1: Access Google Cloud Console

### 1.1 Go to Google Cloud Console
```
https://console.cloud.google.com/
```

### 1.2 Select Your Project
1. Click the project selector at the top
2. Select: `mile-stone-3`
3. Verify you're in the correct project

---

## 🔐 Step 2: Navigate to OAuth Consent Screen

### 2.1 Go to Credentials & Consent Screen
1. In the left navigation menu, click **"APIs & Services"**
2. Click **"OAuth consent screen"**

### 2.2 Choose the Right Consent Screen
- If you have multiple, select the one for your MCP server
- Click **"EDIT APP"** or the edit button

---

## 📝 Step 3: Add Google Drive Scopes

### 3.1 Navigate to Scopes Section
1. Scroll down to the **"Scopes"** section
2. Click **"ADD OR REMOVE SCOPES"**

### 3.2 Add the First Drive Scope
1. In the search box, paste: `https://www.googleapis.com/auth/drive`
2. Click **"Add"** when it appears
3. You should see: "View and manage the files in your Google Drive"

### 3.3 Add the Second Drive Scope
1. In the search box, paste: `https://www.googleapis.com/auth/drive.file`
2. Click **"Add"** when it appears
3. You should see: "View and manage files created by this app"

### 3.4 Verify All Required Scopes
Make sure you have these 4 scopes:
- ✅ `https://www.googleapis.com/auth/documents` (Google Docs)
- ✅ `https://www.googleapis.com/auth/gmail.compose` (Gmail)
- ✅ `https://www.googleapis.com/auth/drive` (Drive - full access)
- ✅ `https://www.googleapis.com/auth/drive.file` (Drive - app files)

### 3.5 Save Scopes
1. Click **"UPDATE"** or **"SAVE"**
2. Wait for the confirmation

---

## 🧪 Step 4: Update Test Users

### 4.1 Add Your Email as Test User
1. Scroll to **"Test users"** section
2. Click **"ADD USERS"**
3. Add your email address
4. Click **"ADD"**

### 4.2 Save Consent Screen
1. Click **"SAVE AND CONTINUE"** at the bottom
2. Click **"BACK TO DASHBOARD"**

---

## ✅ Step 5: Verify the Changes

### 5.1 Check Scopes in Console
1. Go back to **"OAuth consent screen"**
2. Click on your app
3. Verify all 4 scopes are listed under "Scopes"

### 5.2 Check Publishing Status
- Should be **"In production"** or **"Testing"**
- If "Testing", make sure your email is in test users

---

## 🔑 Step 6: Regenerate Authentication Token

### 6.1 Navigate to MCP Server Directory
```bash
cd saksham-mcp-server
```

### 6.2 Backup Existing Token (Optional)
```bash
cp token.json token.json.backup
```

### 6.3 Run Authentication Script
```bash
python auth.py
```

### 6.4 Complete OAuth Flow
1. This will open a browser window
2. Sign in with your Google account
3. You'll see a consent screen with all 4 permissions:
   - Google Docs API
   - Gmail API
   - Google Drive API (full access)
   - Google Drive API (app files)
4. Click **"Allow"**
5. The script will generate a new `token.json`

---

## 🚀 Step 7: Update Production Environment

### 7.1 Generate Environment Variables
```bash
python setup_gmail_integration.py
```

### 7.2 Update Render Environment
1. Go to your Render dashboard
2. Navigate to your MCP service
3. Go to **"Environment"** tab
4. Update `GOOGLE_TOKEN_JSON` with the new token content
5. Click **"Save Changes"**

### 7.3 Redeploy the Service
1. Click **"Manual Deploy"** in Render
2. Wait for deployment to complete
3. Verify the service is running

---

## 🧪 Step 8: Test the Integration

### 8.1 Test Gmail API (Already Working)
```bash
curl -X POST https://saksham-mcp-server.onrender.com/create_email_draft \
  -H "Content-Type: application/json" \
  -d '{"to": "test@example.com", "subject": "Test", "body": "Test message"}'
```

### 8.2 Test Google Drive API (New)
```bash
curl -X POST https://saksham-mcp-server.onrender.com/create_drive_folder \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Folder"}'
```

### 8.3 Test Full Integration
```bash
python test_google_workspace.py
```

---

## 📊 Expected Results

After completing these steps:

### ✅ Success Indicators
- OAuth consent screen shows 4 scopes
- Authentication flow requests Drive permissions
- New `token.json` includes Drive scopes
- Drive API endpoints return 200 instead of 404
- All Google Workspace APIs working

### ❌ Error Indicators
- 404 errors on Drive endpoints → Need deployment
- Permission denied → Need new authentication
- Missing scopes → Need to repeat Step 3

---

## 🚨 Troubleshooting

### Issue 1: "Scope not found" error
**Solution**: Make sure you typed the scopes exactly as shown, including https://

### Issue 2: "App not published" error
**Solution**: Add your email to test users in Step 4

### Issue 3: Still getting 404 errors
**Solution**: The MCP server needs to be redeployed with new code

### Issue 4: Token doesn't include new scopes
**Solution**: Delete `token.json` and run `python auth.py` again

---

## 📋 Quick Reference

### Required Scopes (Copy & Paste):
```
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/gmail.compose
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/drive.file
```

### Important URLs:
- Google Cloud Console: https://console.cloud.google.com/
- OAuth Consent Screen: https://console.cloud.google.com/apis/credentials/consent
- MCP Server: https://saksham-mcp-server.onrender.com/

### Test Commands:
```bash
# Authentication
python auth.py

# Test integration
python test_google_workspace.py

# Setup environment
python setup_gmail_integration.py
```

---

## ⏱️ Time Estimate

- **Step 1-3**: 5 minutes (OAuth configuration)
- **Step 4-6**: 3 minutes (Authentication)
- **Step 7-8**: 5 minutes (Deployment & Testing)

**Total Time**: ~13 minutes

After completing these steps, your MCP server will have full Google Workspace integration with Gmail, Google Docs, and Google Drive APIs!
