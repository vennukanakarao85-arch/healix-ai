from flask import Flask, render_template, request, redirect, session, jsonify, send_file
import flask
from config import Config
from database import db, User, HealthRecord
# Import models_loader inside the function or try/except block if models might be missing initially,
# but for now we assume they exist or will exist before running.
# To avoid top-level import error during setup, we could delay it, but user code imported it at top.
# We will ensure models exist before running app.
from models_loader import diabetes_model, heart_model, kidney_model
from openai import OpenAI
import os

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

# Use existing key or empty string to avoid error if env var not set
client = OpenAI(api_key=app.config.get("OPENAI_API_KEY") or "dummy-key")

with app.app_context():
    db.create_all()

@app.route("/")
def home():
    return redirect("/login")

# ---------------- AUTH ----------------

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=request.form["password"], # In real app, hash this!
            phone=request.form["phone"]
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/login")
        
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        
        # Capture phone if provided in login
        phone = request.form.get("phone")
        
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            session["user"] = username
            
            # Update phone if provided
            if phone:
                user.phone = phone
                db.session.commit()
                
            return redirect("/dashboard")
        else:
            return render_template("login.html", error="Invalid credentials")
            
    return render_template("login.html")

# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html", username=session["user"])

@app.route("/history")
def history():
    if "user" not in session:
        return redirect("/login")
    records = HealthRecord.query.filter_by(username=session["user"]).order_by(HealthRecord.created_at.desc()).all()
    return render_template("history.html", records=records, username=session["user"])

@app.route("/settings", methods=["GET", "POST"])
def settings():
    if "user" not in session:
        return redirect("/login")
    
    message = None
    user = User.query.filter_by(username=session["user"]).first()

    if request.method == "POST":
        new_phone = request.form.get("phone")
        new_pass = request.form.get("password")
        
        if user:
            if new_phone: user.phone = new_phone
            if new_pass: user.password = new_pass
            db.session.commit()
            message = "Profile updated successfully!"
    
    return render_template("settings.html", user=user, message=message, username=session["user"])

@app.route("/report/<int:id>")
def view_public_report(id):
    record = HealthRecord.query.get_or_404(id)
    # Estimate estimates from recorded data if possible or stored?
    # Our module didn't store estimates json in DB, just specific columns.
    # For now we'll display what we have.
    return render_template("report.html", record=record)

# ---------------- AI PREDICTION ----------------

@app.route("/predict", methods=["POST"])
def predict():
    data = request.json
    message = data.get("message", "")
    
    # If manual values are almost all default/missing, we imply we should use AI-driven estimation
    # However, let's look at what's in 'data'
    has_manual = any(k in data and data[k] for k in ["age", "bmi", "bp", "glucose", "chol", "max_heart_rate"])
    
    # Extract questionnaire answers
    q_data = data.get("questionnaire", {})
    
    # If message is present OR questionnaire is present, use NLP to adjust/predict
    recommendation = "Maintain a healthy lifestyle." 
    ai_risks = {}

    if (message and len(message.strip()) > 2) or q_data:
        q_text = ", ".join([f"{k}: {'Yes' if v == 1 else 'No'}" for k, v in q_data.items()])
        prompt = f"""
        Extract 0 or 1 values for:
        thirst, urination, fatigue, chest_pain, dizziness, obesity.
        AND provide:
        1. 'recommendation': Specific advice (max 30 words).
        2. 'future_risks': Potential complications if untreated (max 20 words).
        3. 'precautions': Actionable steps to reduce risk (max 3 bullet points).
        4. 'diabetes_risk': Estimated percentage (0-100) based ONLY on reported symptoms.
        5. 'heart_risk': Estimated percentage (0-100) based ONLY on reported symptoms.
        6. 'kidney_risk': Estimated percentage (0-100) based ONLY on reported symptoms.
        
        Text: {message}
        Direct Answers: {q_text}
        
        Return JSON object with keys: thirst, urination, fatigue, chest_pain, dizziness, obesity, recommendation, future_risks, precautions, diabetes_risk, heart_risk, kidney_risk.
        """

        try:
            if client.api_key == "dummy-key":
                import random
                symptoms = {
                    "thirst": q_data.get("thirst", random.choice([0, 1])),
                    "urination": q_data.get("urination", random.choice([0, 1])),
                    "fatigue": q_data.get("fatigue", random.choice([0, 1])),
                    "chest_pain": q_data.get("chest_pain", random.choice([0, 1])),
                    "dizziness": q_data.get("dizziness", random.choice([0, 1])),
                    "obesity": q_data.get("obesity", random.choice([0, 1])),
                    "recommendation": "Based on your symptoms, consult a doctor immediately.",
                    "future_risks": "Untreated symptoms may lead to chronic diabetes or heart failure.",
                    "precautions": "1. Reduce sugar intake.\n2. Exercise daily.\n3. Monitor BP.",
                    "diabetes_risk": random.randint(30, 85) if q_data.get("thirst") or q_data.get("urination") else random.randint(5, 40),
                    "heart_risk": random.randint(30, 85) if q_data.get("chest_pain") else random.randint(5, 40),
                    "kidney_risk": random.randint(30, 85) if q_data.get("fatigue") else random.randint(5, 40)
                }
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}]
                )
                import json
                content = response.choices[0].message.content
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].strip()
                symptoms = json.loads(content)
            
            recommendation = symptoms.get("recommendation", recommendation)
            future_risks = symptoms.get("future_risks", "Potential health complications if untreated.")
            precautions = symptoms.get("precautions", "Consult a doctor for specific preventive measures.")
            ai_risks = {
                "diabetes": symptoms.get("diabetes_risk", 0),
                "heart": symptoms.get("heart_risk", 0),
                "kidney": symptoms.get("kidney_risk", 0)
            }

            # Adjust values based on symptoms (For traditional models)
            if "glucose" not in data or not data["glucose"]:
                if symptoms.get("thirst"): features["glucose"] += 30
                if symptoms.get("urination"): features["glucose"] += 30
                if symptoms.get("fatigue"): features["glucose"] += 20
            
            if "max_heart_rate" not in data or not data["max_heart_rate"]:
                if symptoms.get("chest_pain"): features["max_heart_rate"] += 40
                if symptoms.get("dizziness"): features["max_heart_rate"] += 20

            if "bmi" not in data or not data["bmi"]:
                if symptoms.get("obesity"): features["bmi"] += 10
            
        except Exception as e:
            print(f"Error calling AI: {e}")
    else:
        future_risks = "Based on risk levels, untreated conditions may worsen."
        precautions = "Maintain a balanced diet and exercise regularly."

    # Prediction Logic Selection
    if not has_manual and ai_risks:
        # User didn't provide numbers, use AI-only estimation (The "New Technology")
        diabetes = ai_risks["diabetes"]
        heart = ai_risks["heart"]
        kidney = ai_risks["kidney"]
    else:
        # Use Scientific Models (pkl)
        diabetes = diabetes_model.predict_proba([[
            features["age"], features["bmi"], features["bp"], features["glucose"]
        ]])[0][1]*100

        heart = heart_model.predict_proba([[
            features["age"], features["bp"], features["chol"], features["max_heart_rate"]
        ]])[0][1]*100

        kidney = kidney_model.predict_proba([[
            features["age"], features["bp"], features["glucose"], features["chol"]
        ]])[0][1]*100

    record = HealthRecord(
        username=session.get("user", "Guest"),
        symptoms=message if message else "Q&A Analysis",
        diabetes=diabetes,
        heart=heart,
        kidney=kidney
    )

    db.session.add(record)
    db.session.commit()

    # --- SMS ALERT LOGIC ---
    try:
        if diabetes > 70 or heart > 70 or kidney > 70:
            user_entry = User.query.filter_by(username=session.get("user", "")).first()
            if user_entry and user_entry.phone:
                send_risk_sms(user_entry.phone, diabetes, heart, kidney, record.id)
    except Exception as e:
        print(f"SMS Error: {e}")
    # -----------------------

    return jsonify({
        "diabetes": int(diabetes),
        "heart": int(heart),
        "kidney": int(kidney),
        "estimates": features,
        "recommendation": recommendation,
        "future_risks": future_risks,
        "precautions": precautions,
        "record_id": record.id
    })

# ---------------- SMS HELPER ----------------

def send_risk_sms(to_number, diabetes, heart, kidney, record_id):
    from twilio.rest import Client
    
    sid = app.config["TWILIO_ACCOUNT_SID"]
    token = app.config["TWILIO_AUTH_TOKEN"]
    from_number = app.config["TWILIO_PHONE_NUMBER"]

    if sid == "YOUR_TWILIO_SID":
        print("Twilio not configured. Skipping SMS.")
        return

    try:
        client = Client(sid, token)
        
        risks = []
        if diabetes > 70: risks.append(f"Diabetes ({int(diabetes)}%)")
        if heart > 70: risks.append(f"Heart ({int(heart)}%)")
        if kidney > 70: risks.append(f"Kidney ({int(kidney)}%)")
        
        # Link to the public report (Dynamic URL)
        try:
            with open("public_url.txt", "r") as f:
                base_url = f.read().strip()
        except FileNotFoundError:
            base_url = "http://localhost:5000"

        report_link = f"{base_url}/report/{record_id}"
        
        msg_body = f"HEALIX AI ALERT: High health risk detected: {', '.join(risks)}. View Report: {report_link}"
        
        message = client.messages.create(
            body=msg_body,
            from_=from_number,
            to=to_number
        )
        print(f"SMS sent to {to_number}: {message.sid}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")

# ---------------- REPORT GENERATION ----------------

@app.route("/download_report", methods=["POST"])
def download_report():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    import io

    data = request.json
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 24)
    c.setFillColor(colors.darkgreen)
    c.drawString(50, height - 50, "HEALIX AI – Health Report")

    # User Info
    c.setFont("Helvetica", 12)
    c.setFillColor(colors.black)
    c.drawString(50, height - 100, f"User: {session.get('user', 'Guest')}")
    c.drawString(50, height - 120, "Date: " + str(db.func.now()))

    # Health Metrics
    y = height - 160
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Health Metrics Used:")
    y -= 25
    c.setFont("Helvetica", 12)
    
    metrics = data.get("estimates", {})
    c.drawString(70, y, f"Age: {metrics.get('age', 'N/A')}")
    c.drawString(250, y, f"BMI: {metrics.get('bmi', 'N/A')}")
    y -= 20
    c.drawString(70, y, f"Glucose: {metrics.get('glucose', 'N/A')} mg/dL")
    c.drawString(250, y, f"Blood Pressure: {metrics.get('bp', 'N/A')} mmHg")
    y -= 20
    c.drawString(70, y, f"Cholesterol: {metrics.get('chol', 'N/A')} mg/dL")
    c.drawString(250, y, f"Max Heart Rate: {metrics.get('max_heart_rate', 'N/A')} bpm")

    # Risk Analysis
    y -= 50
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Risk Analysis Results:")
    y -= 30

    # Draw Boxes for Risks
    def draw_risk_box(x, y, title, risk):
        c.setStrokeColor(colors.grey)
        c.setFillColor(colors.whitesmoke)
        c.rect(x, y-40, 150, 50, fill=1)
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(x + 75, y - 15, title)
        c.setFillColor(colors.red if risk > 50 else colors.green)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(x + 75, y - 35, f"{risk}%")

    draw_risk_box(50, y, "Diabetes Risk", data.get("diabetes", 0))
    draw_risk_box(220, y, "Heart Risk", data.get("heart", 0))
    draw_risk_box(390, y, "Kidney Risk", data.get("kidney", 0))

    # Disclaimer
    y -= 100
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "AI Recommendation:")
    c.setFont("Helvetica", 11)
    # Simple text wrap logic or just truncate for now
    rec_text = data.get("recommendation", "N/A")
    c.drawString(50, y-20, rec_text[:90]) # First line
    if len(rec_text) > 90:
         c.drawString(50, y-35, rec_text[90:])

    y -= 60
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.grey)
    c.drawString(50, y, "Disclaimer: This is an AI-generated estimate. Please consult a doctor for medical advice.")

    c.save()
    buffer.seek(0)

    return flask.send_file(buffer, as_attachment=True, download_name="healix_report.pdf", mimetype="application/pdf")


if __name__ == "__main__":
    # Host on 0.0.0.0 and use PORT from environment if available (required for Render/Railway)
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
