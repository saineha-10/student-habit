from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib import messages
from .models import Student
from django.contrib.auth.hashers import check_password
from django.contrib.auth.hashers import make_password
import os
import joblib
import pandas as pd
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier
from .models import StudentProfile
def signup(request):
    if request.method == "POST":
        full_name = request.POST['full_name']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect('signup')
        if Student.objects.filter(email=email).exists():
            messages.error(request, "Email already exists")
            return redirect('signup')
        Student.objects.create(
            full_name=full_name,
            email=email,
            password=make_password(password)
        )
        messages.success(request, "Account created successfully")
        return redirect('login')
    return render(request, 'signup.html')

def login_view(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if email == "admin@gmail.com" and password == "12345678":
            request.session['admin_login'] = True
            messages.success(request, "Welcome Admin")
            return redirect('admin_dashboard')
        try:
            student = Student.objects.get(email=email)
        except Student.DoesNotExist:
            messages.error(request, "Invalid email or password")
            return redirect('login')
        if not check_password(password, student.password):
            messages.error(request, "Invalid email or password")
            return redirect('login')
        request.session['student_id'] = student.id
        messages.success(request, f"Welcome, {student.full_name}")
        return redirect('student_dashboard')
    return render(request, 'login.html')
def index(request):
    return render(request, 'index.html')
BASE_DIR = settings.BASE_DIR
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(DATASETS_DIR, exist_ok=True)

MODEL_PATH = os.path.join(MODELS_DIR, "student_model.pkl")
def load_model():
    """Load trained model if exists, else None."""
    if os.path.exists(MODEL_PATH):
        return joblib.load(MODEL_PATH)
    return None
@csrf_exempt
def retrain_model(request):
    if request.method != "POST":
        return JsonResponse(
            {"status": "error", "message": "Only POST allowed"},
            status=405,
        )
    csv_file = request.FILES.get("file")
    if not csv_file:
        return JsonResponse(
            {"status": "error", "message": "CSV file is required"},
            status=400,
        )
    try:
        saved_path = os.path.join(DATASETS_DIR, csv_file.name)
        with open(saved_path, "wb+") as dest:
            for chunk in csv_file.chunks():
                dest.write(chunk)
        data = pd.read_csv(saved_path)
        required_cols = [
            "study_hours_per_day",
            "attendance_percentage",
            "sleep_hours",
            "stress_level",
            "exercise_frequency",
            "dropout_risk",
        ]
        for col in required_cols:
            if col not in data.columns:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": f"Missing column in CSV: {col}",
                    },
                    status=400,
                )
        X = data[
            [
                "study_hours_per_day",
                "attendance_percentage",
                "sleep_hours",
                "stress_level",
                "exercise_frequency",
            ]
        ]
        y = data["dropout_risk"]
        model = RandomForestClassifier(random_state=42)
        model.fit(X, y)
        accuracy = float(model.score(X, y))
        joblib.dump(model, MODEL_PATH)
        return JsonResponse(
            {
                "status": "success",
                "message": "Model retrained and saved successfully",
                "accuracy": round(accuracy, 4),
            }
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Retraining failed: {str(e)}"},
            status=500,
        )
@csrf_exempt
def predict_student(request):
    if request.method != "POST":
        return redirect("student_dashboard")
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("login")
    student = Student.objects.get(id=student_id)
    model = load_model()
    if model is None:
        return render(
            request,
            "predict_student.html",
            {"error": "ML model not found"},
            status=500,
        )
    try:
        hours = float(request.POST.get("hours", 0))
        attendance = float(request.POST.get("attendance", 0))
        sleep = float(request.POST.get("sleep", 0))
        stress = float(request.POST.get("stress", 0))
        exercise = float(request.POST.get("exercise", 0))
        X_new = pd.DataFrame(
            [{
                "study_hours_per_day": hours,
                "attendance_percentage": attendance,
                "sleep_hours": sleep,
                "stress_level": stress,
                "exercise_frequency": exercise,
            }]
        )
        pred = model.predict(X_new)[0]
        dropout_text = "High dropout risk" if pred == "Yes" else "Low dropout risk"
        recommendations = []
        if hours < 3:
            recommendations.append("Increase study hours to at least 3–4 hours per day.")
        if attendance < 75:
            recommendations.append("Improve attendance to above 75%.")
        if sleep < 7:
            recommendations.append("Try to get at least 7 hours of sleep daily.")
        if stress > 7:
            recommendations.append("Practice stress management techniques.")
        if exercise < 3:
            recommendations.append("Exercise at least 3 days per week.")
        final_rec = (
            " ".join(recommendations)
            if recommendations
            else "Your habits are stable. Keep maintaining your routine."
        )
        StudentProfile.objects.create(
            student=student,
            study_hours_per_day=hours,
            attendance_percentage=attendance,
            sleep_hours=sleep,
            stress_level=stress,
            exercise_frequency=exercise,
            dropout_risk=dropout_text,
            recommendation=final_rec,
        )
        return render(
            request,
            "predict_student.html",
            {
                "prediction": dropout_text,
                "recommendation": final_rec,
            },
        )
    except Exception as e:
        return render(
            request,
            "predict_student.html",
            {"error": f"Prediction failed: {str(e)}"},
            status=500,
        )
def upload_dataset(request):
    return render(request, 'upload_dataset.html')

def admin_dashboard(request):
    if not request.session.get('admin_login'):
        return redirect('login')
    students = StudentProfile.objects.select_related('student').all()
    student_data = []
    for s in students:
        recs = []
        if s.recommendation:
            recs = [r.strip() for r in s.recommendation.split(',') if r.strip()]
        student_data.append({
            'full_name': s.student.full_name,  # your Student model field
            'email': s.student.email,
            'study_hours_per_day': s.study_hours_per_day,
            'attendance_percentage': s.attendance_percentage,
            'sleep_hours': s.sleep_hours,
            'stress_level': s.stress_level,
            'exercise_frequency': s.exercise_frequency,
            'dropout_risk': s.dropout_risk,
            'recommendations': recs,  # pass as list
        })

    return render(request, 'admin_dashboard.html', {'students': student_data})


def student_dashboard(request):
    student_id = request.session.get("student_id")
    if not student_id:
        return redirect("login")
    student = Student.objects.get(id=student_id)
    profiles = StudentProfile.objects.filter(student=student).order_by('-created_at')
    for profile in profiles:
        if profile.recommendation:
            profile.recommendations_list = [
                r.strip() for r in profile.recommendation.split('.') if r.strip()
            ]
        else:
            profile.recommendations_list = []
    return render(request, "student_dashboard.html", {
        "student": student,
        "profiles": profiles,
    })
def indexx(request):
    return render(request, 'indexx.html')








