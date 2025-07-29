# core/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Grade, AuditLog

@receiver(post_save, sender=Grade)
def log_grade_change(sender, instance, created, **kwargs):
    """Log when a grade is created or updated."""
    action_verb = "created" if created else "updated"
    action = (
        f"Grade for {instance.student.user.username} in {instance.course.name} "
        f"{action_verb} to {instance.mark} by {instance.graded_by.username}."
    )
    AuditLog.objects.create(user=instance.graded_by, action=action)