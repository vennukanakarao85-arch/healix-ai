import joblib
import os

# Define paths relative to this file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")

diabetes_model = joblib.load(os.path.join(MODELS_DIR, "diabetes_model.pkl"))
heart_model = joblib.load(os.path.join(MODELS_DIR, "heart_model.pkl"))
kidney_model = joblib.load(os.path.join(MODELS_DIR, "kidney_model.pkl"))
