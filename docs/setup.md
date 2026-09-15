# Setup & Installation Guide

## Fun Learning Kids — Developer Setup & Local Deployment

This guide explains how to configure and run the **Fun Learning Kids** automation system on a new machine.

---

## 1. Prerequisites

- **Operating System**: Windows 10 or Windows 11 (required for Task Scheduler and Windows Action Center notifications).
- **Python**: Python 3.10, 3.11, or 3.12 installed and added to your system `PATH`.
- **FFmpeg**: FFmpeg installed with `libx264` and `aac` codecs accessible from the command line.
  ```powershell
  ffmpeg -version
  ```
- **Google Cloud Account**: A project with YouTube Data API v3 enabled.

---

## 2. Repository Installation

Clone the repository and install the dependencies:

```powershell
git clone https://github.com/your-username/fun-learning-kids-automation.git
cd fun-learning-kids-automation

# Create virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

---

## 3. Google Cloud & YouTube API Configuration

To enable automated video uploads, configure OAuth 2.0 Client credentials:

1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project named `Fun Learning Kids Automation`.
3. In **APIs & Services > Library**, search for and enable **YouTube Data API v3**.
4. In **APIs & Services > OAuth consent screen**:
   - Choose **External**.
   - Fill in App Name (`Fun Learning Kids`) and User Support Email.
   - Add the following OAuth scopes:
     - `https://www.googleapis.com/auth/youtube.upload`
     - `https://www.googleapis.com/auth/youtube.readonly`
   - Add your YouTube Google account as a **Test User**.
5. In **APIs & Services > Credentials**:
   - Click **Create Credentials > OAuth client ID**.
   - Select **Desktop app**.
   - Download the generated JSON credentials.
6. Rename the downloaded file to `credentials.json` and place it in the project root:
   ```powershell
   # Expected location:
   C:\kids_automation\credentials.json
   ```

---

## 4. One-Time Headless Token Authorization

Run the interactive authentication setup script once:

```powershell
python auth_setup.py
```

- A browser window will open asking you to sign in with your YouTube Google account.
- Accept the permissions requested for YouTube upload and management.
- Once authorized, `token.json` is generated in the project root containing your reusable offline refresh token.
- All future executions will run **100% headless** without opening a browser window.

---

## 5. Local Testing & Verification (Dry-Run Mode)

Test the entire pipeline locally without uploading anything to YouTube using `--dry-run`:

### 5.1 Test Normal Educational Video Pipeline
```powershell
python run.py --dry-run --slot morning --force
```
- Selects a script from `scripts_bank.json`.
- Synthesizes Hindi voice narration via Edge-TTS.
- Synthesizes video via FFmpeg and generates thumbnail.
- Skips YouTube upload.

### 5.2 Test Cartoon Animation Pipeline (V1 Engine)
```powershell
python run.py --slot cartoon --style v1 --dry-run --force
```
- Renders 2D kinematic cartoon episode with vector characters and animated props.

### 5.3 Test Cartoon Animation Pipeline (V4 Engine)
```powershell
python run.py --slot cartoon --style v4 --dry-run --force
```
- Renders 1080p multi-plane parallax cartoon episode with dynamic gaze tracking and contact shadows.

---

## 6. Windows Task Scheduler Setup

To run the automation autonomously whenever the computer is on:

```powershell
# Run PowerShell as Administrator
powershell -ExecutionPolicy Bypass -File .\setup_tasks.ps1
```

This registers three tasks:
1. `FunLearningKids_OnLogon`: Runs automatically upon user logon / laptop boot.
2. `FunLearningKids_Morning`: Runs daily at 09:00 AM.
3. `FunLearningKids_Evening`: Runs daily at 21:30 PM.

To uninstall scheduled tasks:
```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall_tasks.ps1
```
