# OAuth Consent Screen Troubleshooting Guide

## 🚨 Issue: "Edit App" Option Not Available

If you can't find the "Edit app" option, here are several alternative methods to update your OAuth consent screen.

---

## 🔧 Method 1: Direct URL Access

### Step 1: Go Directly to OAuth Consent Screen
```
https://console.cloud.google.com/apis/credentials/consent
```

### Step 2: Select Your Project
1. Make sure `mile-stone-3` is selected at the top
2. Look for your app in the list

### Step 3: Click on App Name
Instead of looking for "Edit app", click directly on your **app name** or the **pencil icon** next to it.

---

## 🔧 Method 2: Through Credentials Page

### Step 1: Go to Credentials
```
https://console.cloud.google.com/apis/credentials
```

### Step 2: Find OAuth 2.0 Client IDs
1. Look for your OAuth client ID
2. Click the **download icon** or **edit icon**
3. This might redirect you to the consent screen

---

## 🔧 Method 3: Create New OAuth Consent Screen

If you can't edit the existing one, create a new one:

### Step 1: Go to OAuth Consent Screen
```
https://console.cloud.google.com/apis/credentials/consent
```

### Step 2: Click "CREATE CONSENT SCREEN"
1. Choose **"External"** (for testing)
2. Fill in the required fields:
   - **App name**: Review Pulse MCP Server
   - **User support email**: your-email@gmail.com
   - **Developer contact**: your-email@gmail.com

### Step 3: Add All Required Scopes
Add these 4 scopes:
```
https://www.googleapis.com/auth/documents
https://www.googleapis.com/auth/gmail.compose
https://www.googleapis.com/auth/drive
https://www.googleapis.com/auth/drive.file
```

### Step 4: Add Test Users
Add your email address to test users

---

## 🔧 Method 4: Check App Publishing Status

### Issue: App might be in "Published" state
If your app is published, the editing options might be different.

### Solution:
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Look for **"Publishing App"** or **"Testing App"**
3. If published, you might need to create a new testing version

---

## 🔧 Method 5: Use the API Library

### Step 1: Go to API Library
```
https://console.cloud.google.com/apis/library
```

### Step 2: Search for OAuth
1. Search for "OAuth"
2. Click on **"OAuth consent screen API"**
3. This might give you access to manage consent screens

---

## 🔧 Method 6: Check User Permissions

### Issue: You might not have the right permissions
1. Make sure you're logged in with the correct Google account
2. Verify you have **"Owner"** or **"Editor"** role on the project
3. Check if you're in the correct organization

---

## 🎯 Quick Alternative Solution

If none of the above work, here's the fastest approach:

### Create Fresh OAuth Setup:
1. **Create new OAuth client ID**:
   - Go to: https://console.cloud.google.com/apis/credentials
   - Click **"Create Credentials"** → **"OAuth client ID"**
   - Choose **"Desktop application"**
   - Download as `credentials.json`

2. **Create new consent screen**:
   - Go to: https://console.cloud.google.com/apis/credentials/consent
   - Click **"CREATE CONSENT SCREEN"**
   - Add all 4 scopes
   - Add your email as test user

3. **Regenerate token**:
   ```bash
   python auth.py
   ```

---

## 📋 What to Look For

### Visual Indicators:
- **Pencil icon** (✏️) next to app name
- **Three dots menu** (⋮) with edit options
- **App name** as a clickable link
- **"Configure consent screen"** button

### Alternative Labels:
- Instead of "Edit app", look for:
  - "Configure"
  - "Manage"
  - "Settings"
  - "Edit consent screen"

---

## 🔍 Step-by-Step Alternative Process

### Step 1: Try Direct URL
```
https://console.cloud.google.com/apis/credentials/consent?project=mile-stone-3
```

### Step 2: Look for These Elements:
- App name (clickable)
- Pencil icon
- Three dots menu
- Settings gear icon

### Step 3: If Still Not Working:
1. Create new OAuth client ID
2. Create new consent screen
3. Update your MCP server with new credentials

---

## 🆘 Last Resort: Contact Support

If you still can't access the OAuth consent screen:
1. Check your Google Cloud project permissions
2. Verify you're the project owner
3. Try a different browser
4. Clear browser cache and cookies

---

## 📞 Quick Help

**Most Common Solution:**
1. Go to: https://console.cloud.google.com/apis/credentials/consent
2. Click on your **app name** (not looking for "Edit app")
3. Add the Drive scopes
4. Save and regenerate token

**If that doesn't work:**
Create a new OAuth consent screen - it only takes 5 minutes and avoids permission issues.
