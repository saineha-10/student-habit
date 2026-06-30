from django.db import models
class Student(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)
    def __str__(self):
        return self.email
class Dataset(models.Model):
    name = models.CharField(max_length=255)
    file = models.FileField(upload_to='datasets/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
class StudentProfile(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    study_hours_per_day = models.FloatField()
    attendance_percentage = models.FloatField()
    sleep_hours = models.FloatField()
    stress_level = models.FloatField()
    exercise_frequency = models.FloatField()
    dropout_risk = models.CharField(max_length=50)
    recommendation = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # use auto_now_add to keep history

    def __str__(self):
        return f"{self.student.full_name} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"





