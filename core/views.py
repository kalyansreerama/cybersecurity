# core/views.py (SECURE VERSION)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Student, Course, Grade, User, AuditLog, Lecturer, Enrollment

from django.http import JsonResponse, Http404


from django.core.exceptions import PermissionDenied

from .decorators import admin_required, lecturer_required, student_required

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .forms import LecturerForm


# core/views.py



@admin_required
def admin_dashboard(request):
    context = {
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lecturers': Lecturer.objects.count(),
        'lecturers': Lecturer.objects.all(),
        'students': Student.objects.all(),
        'audit_logs': AuditLog.objects.all().order_by('-timestamp')[:10],  # Display last 10 audit logs
        'recent_courses': Course.objects.all().order_by('-created_at')[:5],
    }
    return render(request, 'admin/dashboard.html', context)
@admin_required
def students(request):
    context = {
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lecturers': Lecturer.objects.count(),
        'lecturers': Lecturer.objects.all(),
        'students': Student.objects.all(),
    }
    return render(request, 'admin/students.html', context)


@admin_required
def lecturers(request):
    context = {
        'total_students': Student.objects.count(),
        'total_courses': Course.objects.count(),
        'total_lecturers': Lecturer.objects.count(),
        'lecturers': Lecturer.objects.all(),
    }
    return render(request, 'admin/lecturers.html', context)


@admin_required
def add_lecturer(request):
    if request.method == 'POST':
        form = LecturerForm(request.POST)
        if form.is_valid():
            lecturer = form.save()
            AuditLog.objects.create(
                user=request.user,
                action="Lecturer added"
            )
            print(f"Lecturer {lecturer.username} added successfully.")
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            messages.success(request, "Lecturer added successfully.")
            return redirect('admin_dashboard')
        else:
            print("Form errors:", form.errors)
            print(form)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors.as_json()
                }, status=400)
    else:
        print("GET request for add lecturer form")
        form = LecturerForm()
    return render(request, 'admin/add_lecturer.html', {'form': form})

@admin_required
def view_lecturer(request, lecturer_id):
    try:
        lecturer = Lecturer.objects.get(id=lecturer_id)
        courses = Course.objects.filter(lecturer=lecturer)
    except Lecturer.DoesNotExist:
        raise Http404("Lecturer not found")

    data = {
        'id': lecturer.id,
        'full_name': f"{lecturer.first_name} {lecturer.last_name}",
        'total_courses': list(courses.values('id', 'name')),  # List of dicts
    }

    return JsonResponse(data)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')

    has_error = False

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
                has_error = True
        else:
            messages.error(request, "Please enter both username and password.")
            has_error = True

    return render(request, 'login.html', {'has_error': has_error})

@login_required
def student_list(request):
    # VULNERABILITY: Any logged-in user (student, lecturer) can view all students.
    students = Student.objects.all()
    return render(request, 'student_list.html', {'students': students})


@login_required
def student_grades(request):
    # VULNERABILITY: This view is intended for students, but there's no check.
    # If a student ID isn't tied to the request.user, they could see other grades.
    # Let's assume the template just gets the student object and works.
    student = get_object_or_404(Student, user=request.user)
    grades = Grade.objects.filter(student=student)
    return render(request, 'student_grades.html', {'grades': grades})



# SECURE: This dashboard now properly redirects users.
@login_required
def dashboard(request):
    if request.user.role == User.Role.ADMIN:
        return redirect('admin_dashboard')
    elif request.user.role == User.Role.LECTURER:
        return redirect('lecturer_dashboard')
    else: # Student
        return redirect('student_dashboard')


# --- Lecturer Views ---
@lecturer_required
def lecturer_dashboard(request):
    # SECURE: A lecturer sees only students in courses they teach.
    lecturer_courses = Course.objects.filter(lecturer=request.user)
    students = Student.objects.filter(courses__in=lecturer_courses).distinct()
    return render(request, 'lecturer/dashboard.html', {'students': students, 'courses': lecturer_courses})

@lecturer_required
def update_grade(request, student_id, course_id):
    student = get_object_or_404(Student, id=student_id)
    course = get_object_or_404(Course, id=course_id)

    # SECURE (Business Logic Check): Verify this lecturer teaches this course.
    if course.lecturer != request.user:
        raise PermissionDenied("You are not assigned to teach this course.")
        
    # SECURE (Business Logic Check): Verify the student is enrolled in this course.
    if not student.courses.filter(id=course.id).exists():
        raise PermissionDenied("This student is not enrolled in this course.")

    grade, created = Grade.objects.get_or_create(student=student, course=course)
    
    if request.method == 'POST':
        # Using a Django Form is even better for validation, but this is a direct fix.
        grade.mark = request.POST.get('mark')
        grade.graded_by = request.user # Set the user who performed the action
        grade.save() # The signal will fire here, creating an AuditLog
        return redirect('lecturer_dashboard')
        
    return render(request, 'lecturer/update_grade.html', {'grade': grade})

# --- Student Views ---

@student_required
def student_dashboard(request):
    student = request.user
    #registered_courses = Course.objects.filter(enrollment__student=student)
    registered_courses = Enrollment.objects.all()
    #completed_courses = Course.objects.filter(enrollment__student=student, enrollment__completed=True)
    completed_courses = Enrollment.objects.all()
    all_courses = Course.objects.all()
    return render(request, 'student/dashboard.html', {
        'registered_courses': registered_courses,
        'completed_courses': completed_courses,
        'all_courses': all_courses,
    })

#@login_required
def enroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('student_dashboard')

@login_required
def unenroll_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
    if enrollment:
        enrollment.delete()
    return redirect('student_dashboard')

@login_required
def student_courses(request):
    # student = request.user
    #enrolled_courses = Course.objects.filter(enrollment__student=request.user)
    enrolled_courses = Enrollment.objects.all()
    return render(request, 'student/courses.html', {'enrolled_courses': enrolled_courses})

