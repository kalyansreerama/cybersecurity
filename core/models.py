# core/models.py
from django.db import models
from django.conf import settings
#from django.contrib.auth.models import User # Import the standard User model
from django.db.models.signals import post_save
from django.dispatch import receiver # Import the receiver decorator
#from phonenumber_field.modelfields import PhoneNumberField
from django.contrib.auth.models import AbstractUser, UserManager



class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        LECTURER = "LECTURER", "Lecturer"
        STUDENT = "STUDENT", "Student"
    base_role = Role.ADMIN
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=base_role, 
    )


class AdministratorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.ADMIN)

class Administrator(User):
    objects = AdministratorManager()
    class Meta:
        proxy = True
        verbose_name = "Administrator"
        verbose_name_plural = "Administrators"



class LecturerManager(UserManager):  # <-- Inherit from UserManager
    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.LECTURER)
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.LECTURER)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Lecturer(User):
    objects = LecturerManager()

    class Meta:
        proxy = True
        verbose_name = "Lecturer"
        verbose_name_plural = "Lecturers"




class StudentManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(role=User.Role.STUDENT)

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault("role", User.Role.STUDENT)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Student(User):
    objects = StudentManager()
    
    

    class Meta:
        proxy = True
        verbose_name = "Student"
        verbose_name_plural = "Students"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    #phone_number = PhoneNumberField(blank=True, null=True)  # Add phone number field
    credit_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)  # Add credit score field

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
# Signal to create StudentProfile when a new Student is created
@receiver(post_save, sender=Student)
def create_student_profile(sender, instance, created, **kwargs):
    if created:
        StudentProfile.objects.create(user=instance)
        


class Course(models.Model):
    name = models.CharField(max_length=100)
    lecturer = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class StudentEnrollment(models.Model):
    student_profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrollment_date = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('student_profile', 'course')
    def __str__(self):
        return f"{self.student_profile.user.username} enrolled in {self.course.name}"

class Grade(models.Model):
    enrollment = models.OneToOneField(StudentEnrollment, on_delete=models.CASCADE,null=True, related_name='grade')
    mark = models.PositiveIntegerField(default=0)
    graded_by = models.ForeignKey(Lecturer, on_delete=models.SET_NULL, null=True)
    def __str__(self):
        return f"{self.enrollment.student_profile.user.username} - {self.enrollment.course.name}: {self.mark}"

# =========================================================================
# 3. AUDIT LOG AND SIGNAL LOGIC (WITH NEW SIGNAL)
# =========================================================================

class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.user.username} - {self.action} at {self.timestamp}'

# Signal to create AuditLog when a Grade is saved
@receiver(post_save, sender=Grade)
def create_audit_log(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.enrollment.student_profile.user,
            action=f"Grade {instance.mark} assigned for {instance.enrollment.course.name}"
        )


# =========================================================================

# signal to create AuditLog when a StudentEnrollment is created
@receiver(post_save, sender=StudentEnrollment)
def create_studentEnrollment_audit_log(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.student_profile.user,
            action=f"Student {instance.student_profile.user.username} enrolled in {instance.course.name}"
        )

# signal to create AuditLog when a StudentEnrollment is deleted
@receiver(models.signals.post_delete, sender=StudentEnrollment)
def create_studentEnrollment_delete_audit_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.student_profile.user,
        action=f"Student {instance.student_profile.user.username} unenrolled from {instance.course.name}"
    )
# signal to create AuditLog when a Course is created
@receiver(post_save, sender=Course)
def create_course_audit_log(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance.lecturer.user,
            action=f"Course {instance.name} created"
        )
# signal to create AuditLog when a Course is deleted
@receiver(models.signals.post_delete, sender=Course)
def create_course_delete_audit_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.lecturer.user,
        action=f"Course {instance.name} deleted"
    )
# signal to create AuditLog when a User is created
@receiver(post_save, sender=User)
def create_user_audit_log(sender, instance, created, **kwargs):
    if created:
        AuditLog.objects.create(
            user=instance,
            action=f"User {instance.username} created"
        
        )

# signal to create AuditLog when a Lecturer is deleted
@receiver(models.signals.post_delete, sender=Lecturer)
def create_lecturer_delete_audit_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.user,
        action=f"Lecturer {instance.user.username} deleted"
    )
# signal to create AuditLog when a Student is deleted
@receiver(models.signals.post_delete, sender=Student)
def create_student_delete_audit_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance.lecturer.user,
        action=f"Student {instance.user.username} deleted"
    )
# signal to create AuditLog when a User is deleted
@receiver(models.signals.post_delete, sender=User)  
def create_user_delete_audit_log(sender, instance, **kwargs):
    AuditLog.objects.create(
        user=instance,
        action=f"User {instance.username} deleted"
    )

class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"