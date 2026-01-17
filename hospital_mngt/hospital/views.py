from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Doctor, Patient, Appointment
from datetime import date
from datetime import date as dt_date
from .models import Patient, MedicalFile, Appointment  # ← ADD MedicalFile here


# ===================== PUBLIC PAGES =====================
def About(request):
    return render(request, 'about.html')


def Home(request):
    return render(request, 'home.html')


def Contact(request):
    return render(request, 'contact.html')


# ===================== NEW AUTHENTICATION =====================
def main_login(request):
    return render(request, 'login.html')


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid admin username or password")
    return redirect('main_login')


def doctor_login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            doctor = Doctor.objects.get(email=email)
            if getattr(doctor, 'password', None) == password:
                request.session['doctor_id'] = doctor.id
                request.session['user_type'] = 'doctor'
                return redirect('doctor_dashboard')
            else:
                messages.error(request, "Wrong password")
        except Doctor.DoesNotExist:
            messages.error(request, "Doctor not found")
    return redirect('main_login')



def patient_login(request):
    if request.method == "POST":
        identifier = request.POST.get('email_or_mobile')
        password = request.POST.get('password')

        patient = None

        # First try as mobile (exact match)
        if identifier.isdigit():  # if it's numbers only
            try:
                patient = Patient.objects.get(Mobile=identifier)
            except Patient.DoesNotExist:
                pass

        # Then try as email
        if not patient:
            try:
                patient = Patient.objects.get(email=identifier)
            except Patient.DoesNotExist:
                pass

        if patient and getattr(patient, 'password', None) == password:
            request.session['patient_id'] = patient.id
            request.session['user_type'] = 'patient'
            messages.success(request, "Welcome back, patient!")
            return redirect('patient_dashboard')
        elif patient:
            messages.error(request, "Incorrect password.")
        else:
            messages.error(request, "No patient found with that mobile/email.")

    return redirect('main_login')


def Logout_admin(request):
    logout(request)
    request.session.flush()
    return redirect('main_login')


# ===================== ADMIN DASHBOARD & FUNCTIONS =====================
def Index(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')

    d_count = Doctor.objects.count()
    p_count = Patient.objects.count()
    a_count = Appointment.objects.count()

    context = {'d': d_count, 'p': p_count, 'a': a_count}
    return render(request, 'index.html', context)


def View_Doctor(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    doctors = Doctor.objects.all()
    return render(request, 'view_doctor.html', {'doc': doctors})

def Add_Doctor(request):
    error = ""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')

    if request.method == "POST":
        n = request.POST.get('Name')
        m = request.POST.get('Mobile')
        sp = request.POST.get('Special')
        try:
            Doctor.objects.create(Name=n, Mobile=m, Special=sp)
            error = "no"
        except:
            error = "yes"

    return render(request, 'add_doctor.html', {'error': error})


def Delete_Doctor(request, pid):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    doctor = Doctor.objects.get(id=pid)
    doctor.delete()
    return redirect('view_doctor')


def View_Patient(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    doc = Patient.objects.all()
    return render(request, 'view_patient.html', {'doc': doc})


def Add_Patient(request):
    error = ""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')

    if request.method == "POST":
        n = request.POST.get('Name')
        m = request.POST.get('Mobile')
        g = request.POST.get('Gender')
        a = request.POST.get('Address')
        try:
            Patient.objects.create(Name=n, Mobile=m, Gender=g, Address=a)
            error = "no"
        except:
            error = "yes"

    return render(request, 'add_patient.html', {'error': error})


def Delete_Patient(request, pid):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    patient = Patient.objects.get(id=pid)
    patient.delete()
    return redirect('view_patient')


def View_Appointment(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    doc = Appointment.objects.all()
    return render(request, 'view_appointment.html', {'doc': doc})


def Add_Appointment(request):
    error = ""
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')

    doctor1 = Doctor.objects.all()
    patient1 = Patient.objects.all()

    if request.method == "POST":
        d = request.POST.get('doctor')
        p = request.POST.get('patient')
        da = request.POST.get('date')
        t = request.POST.get('time')
        doctor_obj = Doctor.objects.filter(Name=d).first()
        patient_obj = Patient.objects.filter(Name=p).first()
        try:
            Appointment.objects.create(Doctor=doctor_obj, Patient=patient_obj, date=da, time=t)
            error = "no"
        except:
            error = "yes"

    return render(request, 'add_appointment.html', {'doctor': doctor1, 'patient': patient1, 'error': error})


def Delete_Appointment(request, pid):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    appointment = Appointment.objects.get(id=pid)
    appointment.delete()
    return redirect('view_appointment')


def signup(request):
    return render(request, 'signup.html')


def doctor_signup(request):
    if request.method == "POST":
        name = request.POST['name']
        email = request.POST['email']
        mobile = request.POST['mobile']
        special = request.POST['special']
        password = request.POST['password']

        if Doctor.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
        else:
            Doctor.objects.create(Name=name, Mobile=mobile, Special=special, email=email, password=password)
            messages.success(request, "Doctor account created successfully! You can now login.")
            return redirect('main_login')
    return redirect('signup')



def patient_signup(request):
    if request.method == "POST":
        name = request.POST['name']
        mobile = request.POST['mobile']
        gender = request.POST['gender']
        address = request.POST['address']
        email = request.POST.get('email', '')
        password = request.POST['password']

        # Use correct field name: Mobile (capital M)
        if Patient.objects.filter(Mobile=mobile).exists():
            messages.error(request, "Mobile number already registered")
        else:
            Patient.objects.create(
                Name=name,
                Mobile=mobile,
                Gender=gender,
                Address=address,
                email=email,
                password=password  # plain text for now
            )
            messages.success(request, "Patient account created successfully! You can now login.")
            return redirect('main_login')

    return redirect('signup')


def patient_dashboard(request):
    if request.session.get('user_type') != 'patient':
        return redirect('main_login')

    patient_id = request.session.get('patient_id')
    try:
        patient = Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        messages.error(request, "Patient session invalid. Please login again.")
        return redirect('main_login')

    # Handle medical file upload (your existing logic - kept as is)
    if request.method == "POST" and 'file' in request.FILES:
        title = request.POST.get('title', 'Untitled Report')
        description = request.POST.get('description', '')
        file = request.FILES['file']
        MedicalFile.objects.create(
            patient=patient,
            title=title,
            description=description,
            file=file
        )
        messages.success(request, "Medical file uploaded successfully!")
        return redirect('patient_dashboard')

    # Get today's date
    today = date.today()

    # Prepare context data for modals and dashboard
    context = {
        'patient': patient,
        'medical_files': patient.medical_files.all().order_by('-uploaded_at'),  # Real uploaded files
        'today_appointments': Appointment.objects.filter(
            Patient=patient,
            date=today
        ).count(),  # Today's appointments count
        # Prescriptions - placeholder (will be real when you add Prescription model)
        'prescriptions': [],  # Replace with patient.prescriptions.all() later
        # Billing - placeholder (will be real when you add Bill model)
        'bills': [],          # Replace with patient.bills.all() later
        'total_due': 0.00,    # Replace with sum of pending bills later
        'today': today,
    }

    return render(request, 'patient_dashboard.html', context)

def doctor_dashboard(request):
    if request.session.get('user_type') != 'doctor':
        return redirect('main_login')

    doctor_id = request.session.get('doctor_id')
    doctor = Doctor.objects.get(id=doctor_id)

    # Today's appointments
    today = date.today()
    appointments = Appointment.objects.filter(Doctor=doctor, date=today)

    context = {
        'doctor': doctor,
        'today_appointments': appointments.count(),
        'total_patients': Appointment.objects.filter(Doctor=doctor).values('Patient').distinct().count(),
    }
    return render(request, 'doctor_dashboard.html', context)


def doctor_appointments(request):
    if request.session.get('user_type') != 'doctor':
        return redirect('main_login')
    
    doctor_id = request.session.get('doctor_id')
    doctor = Doctor.objects.get(id=doctor_id)
    
    # Get all appointments for this doctor
    appointments = Appointment.objects.filter(Doctor=doctor).order_by('-date', '-time')
    
    # Pre-load uploaded medical files for each patient in appointments
    for apt in appointments:
        apt.patient_files = apt.Patient.medical_files.all().order_by('-uploaded_at')  # Real files
    
    context = {
        'doctor': doctor,
        'appointments': appointments,
        'today': dt_date.today(),
    }
    return render(request, 'doctor_appointments.html', context)

def doctor_my_patients(request):
    if request.session.get('user_type') != 'doctor':
        return redirect('main_login')
    
    doctor_id = request.session.get('doctor_id')
    doctor = Doctor.objects.get(id=doctor_id)
    
    patients = Patient.objects.filter(appointment__Doctor=doctor).distinct()
    
    # Pre-calculate totals and last visit (already good)
    for patient in patients:
        patient.total_appointments = Appointment.objects.filter(Patient=patient, Doctor=doctor).count()
        patient.last_visit = Appointment.objects.filter(Patient=patient, Doctor=doctor).order_by('-date').first()
    
    context = {
        'doctor': doctor,
        'patients': patients,
    }
    return render(request, 'doctor_my_patients.html', context)

def doctor_prescriptions(request):
    if request.session.get('user_type') != 'doctor':
        return redirect('main_login')
    
    doctor_id = request.session.get('doctor_id')
    doctor = Doctor.objects.get(id=doctor_id)
    
    # Placeholder: Later you can add real Prescription model
    prescriptions = []  # Replace with real query when model exists
    
    context = {
        'doctor': doctor,
        'prescriptions': prescriptions,
    }
    return render(request, 'doctor_prescriptions.html', context)

def patient_book_appointment(request):
    if request.session.get('user_type') != 'patient':
        return redirect('main_login')

    patient_id = request.session.get('patient_id')
    patient = Patient.objects.get(id=patient_id)
    doctors = Doctor.objects.all()

    if request.method == "POST":
        doctor_id = request.POST['doctor']
        date = request.POST['date']
        time = request.POST['time']
        doctor = Doctor.objects.get(id=doctor_id)

        Appointment.objects.create(Doctor=doctor, Patient=patient, date=date, time=time)
        messages.success(request, "Appointment booked successfully!")
        return redirect('patient_dashboard')

    context = {'doctors': doctors, 'today': dt_date.today()}
    return render(request, 'patient_book_appointment.html', context)


def patient_appointments(request):
    if request.session.get('user_type') != 'patient':
        return redirect('main_login')
    
    patient_id = request.session.get('patient_id')
    patient = Patient.objects.get(id=patient_id)
    appointments = Appointment.objects.filter(Patient_id=patient_id).order_by('-date', '-time')
    
    context = {
        'patient': patient,  # pass patient for name/mobile
        'appointments': appointments,
        'today': dt_date.today()
    }
    return render(request, 'patient_appointments.html', context)

def cancel_appointment(request, apt_id):
    if request.session.get('user_type') != 'patient':
        return redirect('main_login')

    appointment = Appointment.objects.get(id=apt_id, Patient_id=request.session['patient_id'])
    appointment.delete()
    messages.success(request, "Appointment cancelled successfully.")
    return redirect('patient_appointments')