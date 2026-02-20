import joblib
import os
import shutil
from sklearn.linear_model import LogisticRegression
from sklearn.datasets import make_classification

# Create models directory if it doesn't exist
MODELS_DIR = "models"
if not os.path.exists(MODELS_DIR):
    os.makedirs(MODELS_DIR)

# Generate dummy data and train simple models
# Diabetes Model
X_diabetes, y_diabetes = make_classification(n_samples=100, n_features=4, random_state=42)
diabetes_model = LogisticRegression()
diabetes_model.fit(X_diabetes, y_diabetes)
joblib.dump(diabetes_model, os.path.join(MODELS_DIR, "diabetes_model.pkl"))

# Heart Model
X_heart, y_heart = make_classification(n_samples=100, n_features=4, random_state=42)
heart_model = LogisticRegression()
heart_model.fit(X_heart, y_heart)
joblib.dump(heart_model, os.path.join(MODELS_DIR, "heart_model.pkl"))

# Kidney Model
X_kidney, y_kidney = make_classification(n_samples=100, n_features=4, random_state=42)
kidney_model = LogisticRegression()
kidney_model.fit(X_kidney, y_kidney)
joblib.dump(kidney_model, os.path.join(MODELS_DIR, "kidney_model.pkl"))

print("Dummy models created successfully in", MODELS_DIR)
