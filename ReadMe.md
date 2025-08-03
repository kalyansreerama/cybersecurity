# Architecting a Secure Enterprise Web Application: A Secure Student Management System

This repository contains the source code for a **Secure Student Management System (SMS)**, a web application built using the Django framework. This project demonstrates the practical application of secure software development principles, transforming a functionally complete but vulnerable application into an enterprise-ready, secure platform.

## Abstract

This project documents the design, development, and security hardening of a Student Management System. The primary objective is to demonstrate the practical application of secure software development principles. The initial baseline application, while supporting core CRUD operations and multiple user roles (Admin, Lecturer, Student), was intentionally developed with common security flaws. The methodology involved a systematic security overhaul guided by industry best practices and standards such as the OWASP Top 10.

Key security features implemented include a robust **Role-Based Access Control (RBAC)** system using custom decorators, server-side validation to prevent business logic bypass, inherent **SQL injection protection** via the Django ORM, and the creation of an **immutable audit trail** using Django Signals for non-repudiation. This repository serves as a practical blueprint for integrating security into the software development lifecycle (SDLC) to build resilient and trustworthy web applications.

## Core Security Focus

This project was built from the ground up to identify and remediate common web application vulnerabilities. The security model is based on the following principles and implementations:

#### 1. SR1: Robust Authorization & Principle of Least Privilege
- **Problem:** Broken Access Control (OWASP A01:2021). The insecure baseline allowed any authenticated user to access any URL.
- **Solution:** A multi-layered Role-Based Access Control (RBAC) system was implemented.
    - The `User` model is extended with a `role` field (`ADMIN`, `LECTURER`, `STUDENT`).
    - Custom Python decorators (`@admin_required`, `@lecturer_required`, `@student_required`) are used to protect views, ensuring that only users with the appropriate role can access specific functions.
    - **Business Logic Hardening:** The system goes beyond simple role checks. For example, a `Lecturer` is not only checked for their role but also verified to be the assigned instructor for a course before they can update a grade, preventing unauthorized cross-course data manipulation.

#### 2. SR2: Data Integrity and Confidentiality
- **Problem:** SQL Injection (OWASP A03:2021) and unauthorized data exposure.
- **Solution:**
    - **SQLi Prevention:** The application exclusively uses the Django ORM for all database interactions. The ORM automatically parameterizes queries, effectively eliminating the risk of SQL Injection.
    - **Data Segregation:** All data-fetching views are strictly filtered by the currently logged-in user (`request.user`). A student can only ever query for their own grades, and a lecturer for their own courses. This prevents horizontal privilege escalation where a user could view another user's data.
    - **CSRF Protection:** Django's built-in CSRF middleware is enabled, and all forms use the `{% csrf_token %}` tag to prevent Cross-Site Request Forgery attacks.

#### 3. SR3: Comprehensive Auditing and Non-Repudiation
- **Problem:** Lack of accountability. In the baseline, a grade change was untraceable.
- **Solution:** An `AuditLog` model was created to record security-sensitive events.
    
    - The log immutably records **who** made the change (`user`), **what** was changed (`action` and `details`), and **when** it occurred (`timestamp`), ensuring non-repudiation.

#### 4. SR4: Hardened Application Configuration
- **Problem:** Security Misconfiguration (OWASP A05:2021), such as hardcoded secrets.
- **Solution:**
    - The `python-decouple` library is used to manage sensitive configuration.
    - `SECRET_KEY`, `DEBUG` status, and database credentials are read from an untracked `.env` file, keeping secrets out of source control.
    - The `DEBUG` flag is configured to be `False` by default for production environments.

## Technology Stack

- **Backend:** Django 4.x (Python)
- **Database:** PostgreSQL (recommended for production), SQLite3 (for development)
- **Frontend:** Django Template Language (HTML, CSS)


## Project Architecture

The application follows Django's **Model-View-Template (MVT)** pattern, which provides a clean separation of concerns beneficial for security:
- **Models (`core/models.py`):** Define the data structure, relationships, and constraints. This is the single source of truth for our data schema, including the `User` roles.
- **Views (`core/views.py`):** Contain the business logic. This is where authorization checks (via decorators) and business logic validation are strictly enforced before any action is taken.
- **Templates (`templates/`):** The presentation layer. Django's template engine provides default protection against Cross-Site Scripting (XSS) by automatically escaping variables.

---

## Getting Started on Windows

Follow these instructions to set up and run the project on a Windows machine.

### Prerequisites

- [Python 3.8+](https://www.python.org/downloads/windows/) (Ensure it's added to your PATH during installation)
- [Git for Windows](https://git-scm.com/download/win)

### 1. Clone the Repository
Open Command Prompt or PowerShell and clone the repository.
```powershell
git clone https://github.com/kalyansreerama/cybersecurity.git
cd secure-student-management-system
```
# Set Up the Virtual Environment
Create and activate a virtual environment. This isolates the project's dependencies.

## Create the virtual environment folder named 'venv'
```powershell
python -m venv venv
```
## Activate the virtual environment
```powershell
.\venv\Scripts\activate
pip install -r requirements.txt
```


# Usage and Testing
Log in as Admin: Go to http://127.0.0.1:8000/login and use the superuser credentials you created. You will be redirected to the admin dashboard.
Use the Django Admin Panel (/admin/):
Navigate to http://127.0.0.1:8000/admin/.
Create a Lecturer user (set role to 'LECTURER').

Create a Student user (set role to 'STUDENT').

Create a Course and assign the lecturer to it.

Create Grade objects to enroll the student in the course. You can leave the grade field blank initially.
## Test Roles:
Log out and log in as the Lecturer. You should only see the lecturer dashboard and be able to update grades for students in your assigned course.
Log out and log in as the Student. You should only see the student dashboard with your own grades.
Test Security Controls:
While logged in as a Student, try to manually navigate to /dashboard/admin/ or /dashboard/lecturer/. You should receive a 403 Permission Denied error.
Log back in as the Admin and check the audit log on the dashboard to see a record of the grade change made by the lecturer.
