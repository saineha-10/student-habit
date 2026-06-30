import os
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load dataset
csv_path = os.path.join(BASE_DIR, "enhanced_student_habits_performance_dataset.csv")
data = pd.read_csv(csv_path)

# FEATURES & TARGET (based on your CSV)
X = data[
    ['study_hours_per_day',
     'attendance_percentage',
     'sleep_hours',
     'stress_level',
     'exercise_frequency']
]

y = data['dropout_risk']   # YES / NO

# Train model
model = RandomForestClassifier(random_state=42)
model.fit(X, y)

# Save model
model_path = os.path.join(BASE_DIR, "student_model.pkl")
joblib.dump(model, model_path)

print("✅ Model trained and saved successfully")
