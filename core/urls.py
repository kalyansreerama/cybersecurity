# core/urls.py (SECURE)
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Generic dashboard redirect
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin URLs
    path('super-admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('super-admin/students/', views.students, name='students'),
    path('super-admin/add-lecturer/', views.add_lecturer, name='add_lecturer'),
    path('super-admin/lecturers/', views.lecturers, name='lecturers'),
    #path('super-admin/lecturer/edit/<int:lecturer_id>/', views.edit_lecturer, name='edit_lecturer'),
    #path('super-admin/lecturer/delete/<int:lecturer_id>/', views.delete_lecturer, name='delete_lecturer'),
    path('super-admin/lecturer/view/<int:lecturer_id>/', views.view_lecturer, name='view_lecturer'),
    # Lecturer URLs
    path('lecturer/dashboard/', views.lecturer_dashboard, name='lecturer_dashboard'),
    path('lecturer/grade/update/<int:student_id>/<int:course_id>/', views.update_grade, name='update_grade'),

    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    
    path('student/enroll/<int:course_id>/', views.enroll_course, name='enroll_course'),
    path('student/unenroll/<int:course_id>/', views.unenroll_course, name='unenroll_course'),
    path('student/courses/', views.student_courses, name='student_courses'),
]