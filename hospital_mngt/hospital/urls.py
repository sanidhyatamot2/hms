from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (
    # Public pages
    About, Home, Contact,

    # Auth
    main_login, admin_login, doctor_login, patient_login, staff_login,
    Logout_admin,

    # Signup
    signup, doctor_signup, patient_signup, staff_signup,

    # Admin dashboard & CRUD
    Index,
    View_Doctor,  Add_Doctor,  Delete_Doctor,
    View_Patient, Add_Patient, Delete_Patient,
    View_Appointment, Add_Appointment, Delete_Appointment,

    # Doctor portal
    doctor_dashboard, doctor_appointments, doctor_my_patients,
    doctor_prescriptions, prescribe_medicine,

    # Patient portal
    patient_dashboard, patient_book_appointment,
    patient_appointments, cancel_appointment,
    patient_billing, patient_pay_bill,

    # Staff portal
    staff_dashboard, add_bill, record_payment,
    staff_register_patient, staff_report,
)

urlpatterns = [

    # ── Root ─────────────────────────────────────────────────────
    path('', main_login, name='root'),

    # ── Public pages ─────────────────────────────────────────────
    path('home/',    Home,    name='home'),
    path('about/',   About,   name='about'),
    path('contact/', Contact, name='contact'),

    # ── Login ─────────────────────────────────────────────────────
    path('login/',         main_login,    name='main_login'),
    path('admin-login/',   admin_login,   name='admin_login'),
    path('doctor-login/',  doctor_login,  name='doctor_login'),
    path('patient-login/', patient_login, name='patient_login'),
    path('staff-login/',   staff_login,   name='staff_login'),
    path('logout/',        Logout_admin,  name='logout_admin'),

    # ── Signup ────────────────────────────────────────────────────
    path('signup/',         signup,         name='signup'),
    path('doctor-signup/',  doctor_signup,  name='doctor_signup'),
    path('patient-signup/', patient_signup, name='patient_signup'),
    path('staff-signup/',   staff_signup,   name='staff_signup'),

    # ── Admin dashboard ───────────────────────────────────────────
    path('index/', Index, name='dashboard'),

    # ── Admin — Doctor ────────────────────────────────────────────
    path('view_doctor/',             View_Doctor,   name='view_doctor'),
    path('add_doctor/',              Add_Doctor,    name='add_doctor'),
    path('delete_doctor/<int:pid>/', Delete_Doctor, name='delete_doctor'),

    # ── Admin — Patient ───────────────────────────────────────────
    path('view_patient/',             View_Patient,   name='view_patient'),
    path('add_patient/',              Add_Patient,    name='add_patient'),
    path('delete_patient/<int:pid>/', Delete_Patient, name='delete_patient'),

    # ── Admin — Appointment ───────────────────────────────────────
    path('view_appointment/',                View_Appointment,   name='view_appointment'),
    path('add_appointment/',                 Add_Appointment,    name='add_appointment'),
    path('delete_appointment/<int:pid>/',    Delete_Appointment, name='delete_appointment'),

    # ── Doctor portal ─────────────────────────────────────────────
    path('doctor-dashboard/',                  doctor_dashboard,    name='doctor_dashboard'),
    path('doctor-appointments/',               doctor_appointments, name='doctor_appointments'),
    path('doctor-my-patients/',                doctor_my_patients,  name='doctor_my_patients'),
    path('doctor-prescriptions/',              doctor_prescriptions,name='doctor_prescriptions'),
    path('doctor/prescribe/<int:patient_id>/', prescribe_medicine,  name='prescribe_medicine'),

    # ── Patient portal ────────────────────────────────────────────
    path('patient-dashboard/',              patient_dashboard,       name='patient_dashboard'),
    path('patient-book-appointment/',       patient_book_appointment,name='patient_book_appointment'),
    path('patient-appointments/',           patient_appointments,    name='patient_appointments'),
    path('cancel-appointment/<int:apt_id>/',cancel_appointment,      name='cancel_appointment'),
    path('patient-billing/',                patient_billing,         name='patient_billing'),
    path('patient-pay-bill/',               patient_pay_bill,        name='patient_pay_bill'),

    # ── Staff portal ──────────────────────────────────────────────
    path('staff-dashboard/',          staff_dashboard,        name='staff_dashboard'),
    path('staff/add-bill/',           add_bill,               name='add_bill'),
    path('staff/record-payment/',     record_payment,         name='record_payment'),
    path('staff/register-patient/',   staff_register_patient, name='staff_register_patient'),
    path('staff/report/',             staff_report,           name='staff_report'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
