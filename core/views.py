# core/views.py (SECURE VERSION)
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Student, Course, Grade, User, AuditLog, Lecturer, Enrollment

from django.http import JsonResponse, Http404,HttpResponse


from django.core.exceptions import PermissionDenied

from .decorators import admin_required, lecturer_required, student_required

from django.contrib.auth import authenticate, login
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

#@student_required
# student/views.py


# We assume you have a decorator like this in a `decorators.py` file.
# If not, the role check inside the view will handle security.
# from .decorators import student_required

@student_required
def student_dashboard(request):
    """
    Displays the academic dashboard for a logged-in student.
    
    This view provides context for:
    - Courses the student is currently enrolled in (in-progress).
    - Courses the student has completed, including their grades.
    - A list of all other available courses they can enroll in.
    - A feed of their recent account activity from the AuditLog.
    """
    # 1. Verify that the logged-in user is a student.
    #    Redirects to a homepage if they are not (e.g., a lecturer).
    if not hasattr(request.user, 'role') or request.user.role != 'STUDENT':
        
        return HttpResponse('Access Denied') 

    student = request.user.id
    
    print(student)

    # 2. Fetch all enrollments for the current student.
    #    Using .select_related() is a major performance optimization. It fetches the
    #    related Course and Grade objects in the same database query, preventing
    #    many extra queries when you loop in the template.
    all_enrollments = Enrollment.objects.filter(student=student).select_related('course', 'grade')

    # 3. Filter the enrollments into two separate lists for the template.
    #    This is efficient as it filters the already-fetched queryset.
    registered_enrollments = all_enrollments.filter(completed=False)
    completed_enrollments = all_enrollments.filter(completed=True)
    
    # 4. Find all courses the student has NOT yet enrolled in.
    #    First, get a list of IDs for all courses the student is in.
    enrolled_course_ids = all_enrollments.values_list('course__id', flat=True)
    #    Then, query the Course model, excluding those IDs.
    available_courses = Course.objects.exclude(id__in=enrolled_course_ids)

    # 5. Get the 5 most recent activities for the student's timeline.
    recent_activity = AuditLog.objects.filter(user=student).order_by('-timestamp')[:5]

    # 6. Assemble the context dictionary to pass to the template.
    context = {
        'student': student,
        'registered_enrollments': registered_enrollments,
        'completed_enrollments': completed_enrollments,
        'available_courses': available_courses,
        'recent_activity': recent_activity,
    }
    
    return render(request, 'student/dashboard.html', context)

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

