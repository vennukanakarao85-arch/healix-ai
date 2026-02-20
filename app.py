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
    
    # Default values (average healthy adult)
    features = {
        "age": 45,
        "bmi": 25,
        "bp": 120,
        "glucose": 100,
        "chol": 180,
        "max_heart_rate": 150
    }

    # Override defaults with manual inputs if present
    for key in features.keys():
        if key in data and data[key]:
            try:
                features[key] = float(data[key])
            except ValueError:
                pass # Keep default if conversion fails

    # If manual values are almost all default/missing, we imply we should use AI-driven estimation
    has_manual = any(k in data and data[k] for k in ["age", "bmi", "bp", "glucose", "chol", "max_heart_rate"])
    
    # Extract questionnaire answers
    q_data = data.get("questionnaire", {})
    
    # Extract questionnaire and language
    q_data = data.get("questionnaire", {})
    lang_code = data.get("language", "en-US")
    
    # Map language code to human names for GPT
    lang_map = {
        "en-US": "English",
        "hi-IN": "Hindi",
        "te-IN": "Telugu"
    }
    target_lang = lang_map.get(lang_code, "English")

    # If message is present OR questionnaire is present, use NLP to adjust/predict
    recommendation = "Maintain a healthy lifestyle." 
    ai_risks = {}

    if (message and len(message.strip()) > 2) or q_data:
        q_text = ", ".join([f"{k}: {'Yes' if v == 1 else 'No'}" for k, v in q_data.items()])
        prompt = f"""
        You are a health assistant for Indian conditions (urban and rural).
        Extract 0 or 1 values for the symptoms below.
        
        CRITICAL: Provide ALL text-based fields (recommendation, future_risks, precautions, causes, reduction_steps, diet_plan) in {target_lang}.
        
        Symptoms to extract: thirst, urination, fatigue, chest_pain, dizziness, obesity, blurred_vision, slow_healing, numbness, breath_shortness, swollen_legs, palpitations, foamy_urine, itchy_skin, muscle_cramps.
        
        Fields to provide (in {target_lang}):
        1. 'recommendation': Risk-based advice (max 30 words). 
           - LOW risk: Focus on maintenance and preventive health.
           - MODERATE risk: Focus on lifestyle changes and scheduling a checkup.
           - HIGH risk: Urgent medical consultation.
        2. 'future_risks': Potential complications (max 20 words).
        3. 'precautions': Actionable steps (max 3 bullet points).
        4. 'causes': Medical/lifestyle reasons (max 30 words).
        5. 'reduction_steps': Steps to lower risk proportional to risk level.
        6. 'diet_plan': Recommended foods (max 30 words).
        7. 'diabetes_risk', 'heart_risk', 'kidney_risk': Percentages (0-100).
        
        Input Text: {message}
        Direct Symptoms: {q_text}
        
        Return JSON object with all symptoms and advice keys.
        """

        try:
            if client.api_key == "dummy-key":
                import random
                
                # Mock localized advice (Risk-based)
                mock_advice = {
                    "en-US": {
                        "low": {"rec": "Your risk levels are low. Maintain a balanced diet and regular exercise.", "red": "1. Stay active.\n2. Eat greens.\n3. Annual wellness check."},
                        "high": {"rec": "High risk detected. Consult a doctor immediately for a detailed screening.", "red": "1. Immediate consultation.\n2. Diagnostic tests.\n3. Medication review."}
                    },
                    "hi-IN": {
                        "low": {"rec": "आपका जोखिम स्तर कम है। संतुलित आहार और नियमित व्यायाम बनाए रखें।", "red": "1. सक्रिय रहें।\n2. हरी सब्जियां खाएं।\n3. वार्षिक स्वास्थ्य जांच।"},
                        "high": {"rec": "उच्च जोखिम का पता चला। विस्तृत जांच के लिए तुरंत डॉक्टर से सलाह लें।", "red": "1. तत्काल परामर्श।\n2. नैदानिक परीक्षण।\n3. दवा की समीक्षा।"}
                    },
                    "te-IN": {
                        "low": {"rec": "మీ ప్రమాద స్థాయిలు తక్కువగా ఉన్నాయి. సమతుల్య ఆహారం మరియు క్రమం తప్పకుండా వ్యాయామం చేయండి.", "red": "1. యాక్టివ్ గా ఉండండి.\n2. ఆకుకూరలు తినండి.\n3. వార్షిక ఆరోగ్య పరీక్ష."},
                        "high": {"rec": "అధిక ప్రమాదం గుర్తించబడింది. వివరణాత్మక స్క్రీనింగ్ కోసం వెంటనే వైద్యుడిని సంప్రదించండి.", "red": "1. తక్షణ సంప్రదింపు.\n2. రోగనిర్ధారణ పరీక్షలు.\n3. మందుల సమీక్ష."}
                    }
                }
                
                # Mock symptoms logic
                s_thirst = q_data.get("thirst", random.choice([0, 1]))
                s_chest = q_data.get("chest_pain", random.choice([0, 1]))
                
                d_risk = random.randint(60, 95) if s_thirst else random.randint(5, 30)
                h_risk = random.randint(60, 95) if s_chest else random.randint(5, 30)
                k_risk = random.randint(5, 40)
                
                is_high = any(r > 60 for r in [d_risk, h_risk, k_risk])
                risk_level = "high" if is_high else "low"
                
                curr_advice = mock_advice.get(lang_code, mock_advice["en-US"])[risk_level]

                symptoms = {
                    "thirst": s_thirst,
                    "urination": q_data.get("urination", random.choice([0, 1])),
                    "fatigue": q_data.get("fatigue", random.choice([0, 1])),
                    "chest_pain": s_chest,
                    "dizziness": q_data.get("dizziness", random.choice([0, 1])),
                    "obesity": q_data.get("obesity", random.choice([0, 1])),
                    "blurred_vision": q_data.get("blurred_vision", random.choice([0, 1])),
                    "slow_healing": q_data.get("slow_healing", random.choice([0, 1])),
                    "numbness": q_data.get("numbness", random.choice([0, 1])),
                    "breath_shortness": q_data.get("breath_shortness", random.choice([0, 1])),
                    "swollen_legs": q_data.get("swollen_legs", random.choice([0, 1])),
                    "palpitations": q_data.get("palpitations", random.choice([0, 1])),
                    "foamy_urine": q_data.get("foamy_urine", random.choice([0, 1])),
                    "itchy_skin": q_data.get("itchy_skin", random.choice([0, 1])),
                    "muscle_cramps": q_data.get("muscle_cramps", random.choice([0, 1])),
                    "recommendation": curr_advice["rec"],
                    "future_risks": "Complications depend on lifestyle choices.",
                    "precautions": "Monitor vitals regularly.",
                    "causes": "May include environmental and genetic factors.",
                    "reduction_steps": curr_advice["red"],
                    "diet_plan": "Specific diet based on your risk profile.",
                    "diabetes_risk": d_risk,
                    "heart_risk": h_risk,
                    "kidney_risk": k_risk
                }
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role":"user","content":prompt}],
                    response_format={ "type": "json_object" }
                )
                import json
                symptoms = json.loads(response.choices[0].message.content)
            
            recommendation = symptoms.get("recommendation", recommendation)
            future_risks = symptoms.get("future_risks", "Potential health complications if untreated.")
            precautions = symptoms.get("precautions", "Consult a doctor for specific preventive measures.")
            causes = symptoms.get("causes", "Lifestyle or biological factors.")
            reduction_steps = symptoms.get("reduction_steps", "Medical management and lifestyle adjustments.")
            diet_plan = symptoms.get("diet_plan", "Balanced nutrition based on risk levels.")

            ai_risks = {
                "diabetes": symptoms.get("diabetes_risk", 0),
                "heart": symptoms.get("heart_risk", 0),
                "kidney": symptoms.get("kidney_risk", 0)
            }

            # Adjust values based on symptoms (For traditional models)
            if "glucose" not in data or not data["glucose"]:
                if symptoms.get("thirst"): features["glucose"] += 20
                if symptoms.get("urination"): features["glucose"] += 20
                if symptoms.get("blurred_vision"): features["glucose"] += 20
                if symptoms.get("slow_healing"): features["glucose"] += 20
            
            if "bp" not in data or not data["bp"]:
                if symptoms.get("breath_shortness"): features["bp"] += 10
                if symptoms.get("swollen_legs"): features["bp"] += 10

            if "max_heart_rate" not in data or not data["max_heart_rate"]:
                if symptoms.get("chest_pain"): features["max_heart_rate"] += 30
                if symptoms.get("palpitations"): features["max_heart_rate"] += 30
                if symptoms.get("breath_shortness"): features["max_heart_rate"] += 20

            if "bmi" not in data or not data["bmi"]:
                if symptoms.get("obesity"): features["bmi"] += 10
            
        except Exception as e:
            print(f"Error calling AI: {e}")
    else:
        defaults = {
            "en-US": {
                "risk": "Based on risk levels, untreated conditions may worsen.",
                "pre": "Maintain a balanced diet and exercise regularly.",
                "cause": "Further diagnosis required for specific causes.",
                "red": "Standard health optimization requested.",
                "diet": "Universal healthy diet recommended."
            },
            "hi-IN": {
                "risk": "जोखिम के स्तरों के आधार पर, अनुपचारित स्थितियां खराब हो सकती हैं।",
                "pre": "संतुलित आहार बनाए रखें और नियमित व्यायाम करें।",
                "cause": "विशिष्ट कारणों के लिए और निदान की आवश्यकता है।",
                "red": "मानक स्वास्थ्य अनुकूलन का अनुरोध किया गया।",
                "diet": "सार्वभौमिक स्वास्थ्य आहार की सिफारिश की गई।"
            },
            "te-IN": {
                "risk": "ప్రమాద స్థాయిల ఆధారంగా, చికిత్స చేయని పరిస్థితులు అధ్వాన్నంగా మారవచ్చు.",
                "pre": "సమతుల్య ఆహారం తీసుకోండి మరియు క్రమం తప్పకుండా వ్యాయామం చేయండి.",
                "cause": "నిర్దిష్ట కారణాల కోసం మరిన్ని పరీక్షలు అవసరం.",
                "red": "ప్రామాణిక ఆరోగ్య ఆప్టిమైజేషన్ అభ్యర్థించబడింది.",
                "diet": "సార్వత్రిక ఆరోగ్యకరమైన ఆహారం సిఫార్సు చేయబడింది."
            }
        }
        curr_defaults = defaults.get(lang_code, defaults["en-US"])
        future_risks = curr_defaults["risk"]
        precautions = curr_defaults["pre"]
        causes = curr_defaults["cause"]
        reduction_steps = curr_defaults["red"]
        diet_plan = curr_defaults["diet"]

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
                send_risk_sms(user_entry.phone, diabetes, heart, kidney, record.id, lang_code)
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
        "causes": causes,
        "reduction_steps": reduction_steps,
        "diet_plan": diet_plan,
        "record_id": record.id
    })

# ---------------- SMS HELPER ----------------

def send_risk_sms(to_number, diabetes, heart, kidney, record_id, lang_code="en-US"):
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
        
        if lang_code == "hi-IN":
            msg_body = f"हीलिक्स एआई अलर्ट: उच्च स्वास्थ्य जोखिम का पता चला है: {', '.join(risks)}। रिपोर्ट देखें: {report_link}"
        elif lang_code == "te-IN":
            msg_body = f"హీలిక్స్ AI అలర్ట్: అధిక ఆరోగ్య ప్రమాదం గుర్తించబడింది: {', '.join(risks)}. రిపోర్ట్ చూడండి: {report_link}"
        else:
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

    # AI Details (Causes, Reduction, Diet)
    y -= 100
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Potential Causes:")
    c.setFont("Helvetica", 11)
    causes_text = data.get("causes", "N/A")
    c.drawString(50, y-15, causes_text[:90])
    if len(causes_text) > 90: c.drawString(50, y-30, causes_text[90:180])
    
    y -= 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "How to Reduce Risk:")
    c.setFont("Helvetica", 11)
    reduction_text = data.get("reduction_steps", "N/A")
    lines = reduction_text.split('\n')
    for i, line in enumerate(lines[:3]):
        c.drawString(50, y - 15 - (i*15), line[:90])
    
    y -= 65
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Recommended Dietary Plan:")
    c.setFont("Helvetica", 11)
    diet_text = data.get("diet_plan", "N/A")
    c.drawString(50, y-15, diet_text[:90])
    if len(diet_text) > 90: c.drawString(50, y-30, diet_text[90:180])

    y -= 50
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "General Recommendations:")
    c.setFont("Helvetica", 11)
    rec_text = data.get("recommendation", "N/A")
    c.drawString(50, y-15, rec_text[:90])
    if len(rec_text) > 90: c.drawString(50, y-30, rec_text[90:180])

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
