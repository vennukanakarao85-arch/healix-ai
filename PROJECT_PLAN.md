# Healix AI Implementation Plan

## Goal Description
Set up the Healix AI project structure as requested, populate files with provided code, create necessary missing files (dummy models, extra templates), and debug the application to ensure it runs.

## User Review Required
> [!IMPORTANT]
> The user provided code for `dashboard.html` but referenced `base.html`, `login.html`, and `register.html` in `app.py` without providing their content. I will create basic versions of these to prevent runtime errors.

> [!WARNING]
> The application requires pre-trained `.pkl` models (`diabetes_model.pkl`, etc.) which are not provided. I will generate dummy models to allow the application to start and run for debugging purposes.

## Proposed Changes

### Root Directory (`healix_ai/`)
#### [NEW] `requirements.txt`
#### [NEW] `config.py`
#### [NEW] `database.py`
#### [NEW] `models_loader.py`
#### [NEW] `app.py`

### Models (`healix_ai/models/`)
#### [NEW] `diabetes_model.pkl` (Dummy)
#### [NEW] `heart_model.pkl` (Dummy)
#### [NEW] `kidney_model.pkl` (Dummy)
#### [NEW] `create_dummy_models.py` (Script to generate the pkl files)

### Templates (`healix_ai/templates/`)
#### [NEW] `dashboard.html` (Provided)
#### [NEW] `base.html` (Inferred)
#### [NEW] `login.html` (Inferred)
#### [NEW] `register.html` (Inferred)

### Static (`healix_ai/static/`)
#### [NEW] `style.css` (Provided)
#### [NEW] `script.js` (Empty/Placeholder if strictly needed, though logic is in dashboard.html)

### Manual Input Feature
#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Add input fields for Age, BMI, Blood Pressure, Glucose, and Cholesterol.
- Add a toggle or simply display them alongside the symptom text area.

#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Update `/predict` route to check for manual inputs in the request JSON.
- If manual inputs are present, use them.
- If only text is present, use the existing NLP + estimation logic (but perhaps allow editing the estimated values).
- For now, priority: Manual Inputs > NLP Estimation (or fill missing manual inputs with estimates).

### PDF Report Feature
#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Create `/download_report` route.
- Use `reportlab` to generate a PDF containing:
    - User details (Name/Username)
    - Input/Estimated Metrics (Glucose, BP, etc.)
    - Risk Analysis Results (Diabetes, Heart, Kidney)
    - Date of Report

#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Add a "Download PDF Report" button in the results section.
- Javascript function to trigger the download (sending the current data to the server or using a GET request if data is persisted/session-based). *Strategy: Send data in POST or save last prediction in session.*

### UI Redesign & AI Advice
#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Update OpenAI prompt to return a "recommendation" string along with symptoms.
- Pass this recommendation to the frontend and include it in the saved record/PDF.

#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- restructure layout to have a Sidebar and Main Content area.
- Style the Symptom Input as a "Chat Interface" (User bubble, AI thinking...).
- Redesign Result Cards to match the image (Red/Pink for Diabetes, Orange for Heart, Green for Kidney).
- Add "Recommendations" section.

#### [MODIFY] [static/style.css](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/static/style.css)
- Add CSS variables for the specific colors in the image.
- Add styles for Chat UI (bubbles, input bar).
- Add styles for the colorful risk cards with percentage indicators.

### Dark Theme & Input Toggle
#### [MODIFY] [static/style.css](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/static/style.css)
- Update variables for Dark Theme (Dark Blue/Black backgrounds, White text).
- Style Login/Register pages to match the "Dark Blue" login reference.
- Style Dashboard to match the "Dark Dashboard" reference.

#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Add a Tab/Toggle mechanism to switch between "Manual Input" form and "Symptom Chat".
- Hide/Show respective sections based on selection.

#### [MODIFY] [templates/login.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/login.html) & [templates/register.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/register.html)
- Apply specific classes/structure to match the centered dark card design.

### History & Settings Pages
#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Add `/history` route: Query `HealthRecord` for current user.
- Add `/settings` route: Handle profile updates (phone, password).

#### [NEW] [templates/history.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/history.html)
- Display a table of past health records (Date, Symptoms, Risk %).
- Maintain Sidebar layout and Dark Theme.

#### [NEW] [templates/settings.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/settings.html)
- Form to update Phone Number.
- Form to change Password.
- Maintain Sidebar layout and Dark Theme.

#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Update Sidebar links to point to `/history` and `/settings`.

### Logo Integration
#### [NEW] [static/logo.png](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/static/logo.png)
- Generate a logo based on the user's reference (Medical Cross + DNA, Blue/Green).

#### [MODIFY] [templates/login.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/login.html) & [templates/register.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/register.html)
- Insert `<img src="/static/logo.png" ...>` at the top of the auth box.

#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html), [templates/history.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/history.html), [templates/settings.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/settings.html)
- Replace the text/SVG "HEALIX AI" in the sidebar with the logo image.

### Voice Assistant Integration
#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Add Microphone Button icon near the textarea.
- Implement `speak(text, lang)` function using `SpeechSynthesisUtterance` with female voice emphasis (Zira/Google/Samantha).
- Implement `startListening()` using `webkitSpeechRecognition` to capture voice input.
- Add logic to handle commands like "Analyze" to trigger the prediction.
- Add "Welcome" speech on load.

### Public Access & Sharing
#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Update `/dashboard`: Remove login requirement. Use `session.get("user", "Guest")`.
- Update `/predict`: Return `record_id` in response.
- Add `/report/<int:id>`: Validates ID and renders `report.html`.

#### [MODIFY] [templates/dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Sidebar: Hide History/Settings if user is "Guest". Show "Login" instead of "Sign Out".
- Results: Add "Share Link" button that copies `/report/<id>` to clipboard.

#### [NEW] [templates/report.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/report.html)
- Read-only version of the results view.
- Accessible by anyone with the link.

### Public Internet Access
#### [NEW] [start_public_access.bat](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/start_public_access.bat)
- Script to launch SSH tunnel (Serveo.net or Localhost.run).
- Exposes port 5000 to the internet.
- Displays the public URL to the user.

### SMS Notifications
#### [MODIFY] [config.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/config.py)
- Add Twilio credentials (SID, Token, Phone Number).

#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Import `twilio`.
- Add `send_sms` function.
- In `/predict`, check if risk > 70.
- If high risk, look up user's phone number and call `send_sms`.

### Refined Medical Advice
#### [MODIFY] [app.py](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/app.py)
- Update OpenAI Prompt to request: `recommendation`, `future_risks`, `precautions`.
- Update Dummy Response to include these fields.

#### [MODIFY] [dashboard.html](file:///c:/Users/shaik/OneDrive/Desktop/HEALIX%20AI/healix_ai/templates/dashboard.html)
- Add sections for "Future Implications" and "Preventive Measures" in the Results area.

## Verification Plan
### Automated Tests
- Test `/predict` with high risk values (e.g. Glucose 200). Verify console log (if mock) or real SMS.

### Manual Verification
- Log in -> Update Settings with real phone number.
- Dashboard -> Enter high risk values -> Analyze.
- Check phone for SMS (or console for log if no keys).

### Manual Verification
- Open Incognito window -> Access Dashboard.
- Run Prediction -> Click Share.
- Paste link in new tab -> Verify Report page.



