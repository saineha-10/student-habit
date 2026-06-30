
from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('index/', views.index, name='index'),
    path('upload-dataset/', views.upload_dataset, name='upload_dataset'),
    path("api/retrain/", views.retrain_model, name="retrain_model"),
    path("api/predict/", views.predict_student, name="predict_student"),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('', views.indexx, name='indexx'),
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)