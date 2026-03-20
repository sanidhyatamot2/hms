from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from .models import (
    Doctor, Patient, Appointment, Prescription, PrescriptionItem,
    Staff, BillingItem, Bill, BillItem, MedicalFile,
    DoctorSchedule, AppointmentSlot, DoctorLeave,
)
from datetime import date
from datetime import date as dt_date


# ===================== PUBLIC PAGES =====================

def About(request):
    return render(request, 'about.html')


def Home(request):
    return render(request, 'home.html')


def Contact(request):
    return render(request, 'contact.html')


# ===================== LOGIN =====================

def main_login(request):
    return render(request, 'login.html', {'is_auth_page': True})


def admin_login(request):
    if request.method == "POST":
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "Invalid admin username or password.")
    return redirect('main_login')


def doctor_login(request):
    if request.method == "POST":
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()
        try:
            doctor = Doctor.objects.get(email=email)
            # Password stored as plain text in doctor_signup
            if doctor.password == password:
                request.session['doctor_id'] = doctor.id
                request.session['user_type'] = 'doctor'
                return redirect('doctor_dashboard')
            else:
                messages.error(request, "Wrong password.")
        except Doctor.DoesNotExist:
            messages.error(request, "No doctor found with that email.")
    return redirect('main_login')


def patient_login(request):
    if request.method == "POST":
        identifier = request.POST.get('email_or_mobile', '').strip()
        password   = request.POST.get('password', '').strip()

        patient = None

        # Try mobile first
        try:
            patient = Patient.objects.get(Mobile=identifier)
        except Patient.DoesNotExist:
            pass

        # Try email if mobile didn't match
        if not patient:
            try:
                patient = Patient.objects.get(email=identifier)
            except Patient.DoesNotExist:
                pass

        if patient and patient.password == password:
            request.session['patient_id'] = patient.id
            request.session['user_type']  = 'patient'
            messages.success(request, f"Welcome back, {patient.Name}!")
            return redirect('patient_dashboard')
        elif patient:
            messages.error(request, "Incorrect password.")
        else:
            messages.error(request, "No patient found with that mobile/email.")

    return redirect('main_login')


def staff_login(request):
    if request.method == 'POST':
        email_or_username = request.POST.get('email_or_username', '').strip()
        password          = request.POST.get('password', '').strip()

        # Find the Staff record by username or email
        staff = None
        try:
            staff = Staff.objects.get(user__username=email_or_username)
        except Staff.DoesNotExist:
            try:
                staff = Staff.objects.get(user__email=email_or_username)
            except Staff.DoesNotExist:
                pass

        if not staff:
            messages.error(request, "No staff account found with that username/email.")
            return redirect('main_login')

        # Authenticate through Django's auth system
        user = authenticate(request, username=staff.user.username, password=password)
        if user is not None:
            login(request, user)
            request.session['user_type'] = 'staff'
            request.session['staff_id']  = staff.id
            messages.success(request, f"Welcome, {staff.name}!")
            return redirect('staff_dashboard')
        else:
            messages.error(request, "Incorrect password.")

    return redirect('main_login')


# ===================== LOGOUT =====================

def Logout_admin(request):
    logout(request)
    request.session.flush()
    return redirect('main_login')


# ===================== SIGNUP =====================

def signup(request):
    return render(request, 'signup.html')


def doctor_signup(request):
    if request.method == "POST":
        name     = request.POST.get('name', '').strip()
        email    = request.POST.get('email', '').strip()
        mobile   = request.POST.get('mobile', '').strip()
        special  = request.POST.get('special', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([name, email, mobile, special, password]):
            messages.error(request, "All fields are required.")
            return redirect('signup')

        if Doctor.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup')

        # Mobile stored as IntegerField — validate it fits
        try:
            mobile_int = int(mobile)
        except ValueError:
            messages.error(request, "Mobile must be a number.")
            return redirect('signup')

        Doctor.objects.create(
            Name    = name,
            Mobile  = mobile_int,
            Special = special,
            email   = email,
            password= password,   # plain text (matches doctor_login check)
        )
        messages.success(request, "Doctor account created! Please log in.")
        return redirect('main_login')

    return redirect('signup')


def patient_signup(request):
    if request.method == "POST":
        name     = request.POST.get('name', '').strip()
        mobile   = request.POST.get('mobile', '').strip()
        gender   = request.POST.get('gender', '').strip()
        address  = request.POST.get('address', '').strip()
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '').strip()

        if not all([name, mobile, gender, address, password]):
            messages.error(request, "Please fill in all required fields.")
            return redirect('signup')

        if Patient.objects.filter(Mobile=mobile).exists():
            messages.error(request, "Mobile number already registered.")
            return redirect('signup')

        if email and Patient.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup')

        Patient.objects.create(
            Name    = name,
            Mobile  = mobile,
            Gender  = gender,
            Address = address,
            email   = email or None,
            password= password,   # plain text (matches patient_login check)
        )
        messages.success(request, "Patient account created! Please log in.")
        return redirect('main_login')

    return redirect('signup')


def staff_signup(request):
    if request.method == 'POST':
        name             = request.POST.get('name', '').strip()
        email            = request.POST.get('email', '').strip()
        username         = request.POST.get('username', '').strip()
        phone            = request.POST.get('phone', '').strip()
        password         = request.POST.get('password', '').strip()
        password_confirm = request.POST.get('password_confirm', '').strip()

        # ── Validation ──────────────────────────────────────────
        if not all([name, email, username, password, password_confirm]):
            messages.error(request, "All fields are required.")
            return redirect('signup')

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('signup')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return redirect('signup')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered.")
            return redirect('signup')

        # ── Create Django User + Staff profile ──────────────────
        try:
            user = User.objects.create_user(
                username = username,
                email    = email,
                password = password,
            )
            staff = Staff.objects.create(
                user  = user,
                name  = name,
                role  = "Receptionist",
                phone = phone,
            )

            # Log them in immediately after signup
            login(request, user)
            request.session['user_type'] = 'staff'
            request.session['staff_id']  = staff.id   # use staff.id directly (not user.staff.id)

            messages.success(request, f"Welcome, {name}! Your staff account has been created.")
            return redirect('staff_dashboard')

        except Exception as e:
            messages.error(request, f"Error creating account: {str(e)}")
            return redirect('signup')

    return redirect('signup')


# ===================== ADMIN DASHBOARD & CRUD =====================

def Index(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    return render(request, 'index.html', {
        'd': Doctor.objects.count(),
        'p': Patient.objects.count(),
        'a': Appointment.objects.count(),
    })


def View_Doctor(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    return render(request, 'view_doctor.html', {'doc': Doctor.objects.all()})


def Add_Doctor(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    error = ""
    if request.method == "POST":
        try:
            Doctor.objects.create(
                Name    = request.POST.get('Name', '').strip(),
                Mobile  = int(request.POST.get('Mobile', 0)),
                Special = request.POST.get('Special', '').strip(),
                password= 'doctor123',   # default password for admin-added doctors
            )
            error = "no"
        except Exception:
            error = "yes"
    return render(request, 'add_doctor.html', {'error': error})


def Delete_Doctor(request, pid):
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_staff_user = _require_staff(request) is not None
    if not is_admin and not is_staff_user:
        return redirect('main_login')
    Doctor.objects.filter(id=pid).delete()
    messages.success(request, 'Doctor deleted.')
    return redirect('view_doctor')


def View_Patient(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    return render(request, 'view_patient.html', {'doc': Patient.objects.all()})


def Add_Patient(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    error = ""
    if request.method == "POST":
        try:
            Patient.objects.create(
                Name    = request.POST.get('Name', '').strip(),
                Mobile  = request.POST.get('Mobile', '').strip(),
                Gender  = request.POST.get('Gender', '').strip(),
                Address = request.POST.get('Address', '').strip(),
                password= 'patient123',  # default password for admin-added patients
            )
            error = "no"
        except Exception:
            error = "yes"
    return render(request, 'add_patient.html', {'error': error})


def Delete_Patient(request, pid):
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_staff_user = _require_staff(request) is not None
    if not is_admin and not is_staff_user:
        return redirect('main_login')
    Patient.objects.filter(id=pid).delete()
    messages.success(request, 'Patient deleted.')
    return redirect('view_patient')


def View_Appointment(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    return render(request, 'view_appointment.html', {'doc': Appointment.objects.all()})


def Add_Appointment(request):
    if not request.user.is_authenticated or not request.user.is_staff:
        return redirect('main_login')
    error = ""
    doctors  = Doctor.objects.all()
    patients = Patient.objects.all()
    if request.method == "POST":
        try:
            doctor_obj  = Doctor.objects.filter(Name=request.POST.get('doctor')).first()
            patient_obj = Patient.objects.filter(Name=request.POST.get('patient')).first()
            Appointment.objects.create(
                Doctor  = doctor_obj,
                Patient = patient_obj,
                date    = request.POST.get('date'),
                time    = request.POST.get('time'),
            )
            error = "no"
        except Exception:
            error = "yes"
    return render(request, 'add_appointment.html', {
        'doctor': doctors, 'patient': patients, 'error': error
    })


def Delete_Appointment(request, pid):
    # Allow both Django admin users AND staff session users
    is_admin = request.user.is_authenticated and request.user.is_staff
    is_staff_user = _require_staff(request) is not None
    if not is_admin and not is_staff_user:
        return redirect('main_login')
    Appointment.objects.filter(id=pid).delete()
    messages.success(request, 'Appointment deleted.')
    return redirect('view_appointment')


# ===================== DOCTOR VIEWS =====================

def _require_doctor(request):
    """Returns Doctor object or None if session is invalid."""
    if request.session.get('user_type') != 'doctor':
        return None
    doctor_id = request.session.get('doctor_id')
    if not doctor_id:
        return None
    try:
        return Doctor.objects.get(id=doctor_id)
    except Doctor.DoesNotExist:
        return None


def doctor_dashboard(request):
    doctor = _require_doctor(request)
    if not doctor:
        messages.error(request, "Please log in as a doctor.")
        return redirect('main_login')

    today = date.today()
    return render(request, 'doctor_dashboard.html', {
        'doctor':             doctor,
        'today_appointments': Appointment.objects.filter(Doctor=doctor, date=today).count(),
        'total_patients':     Appointment.objects.filter(Doctor=doctor).values('Patient').distinct().count(),
    })


def doctor_appointments(request):
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    appointments = Appointment.objects.filter(Doctor=doctor).select_related('Patient').order_by('-date', '-time')
    return render(request, 'doctor_appointments.html', {
        'doctor':       doctor,
        'appointments': appointments,
        'today':        date.today(),
    })


def doctor_my_patients(request):
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    # All unique patients who have an appointment with this doctor
    patients = Patient.objects.filter(appointment__Doctor=doctor).distinct()

    for patient in patients:
        apts = Appointment.objects.filter(Patient=patient, Doctor=doctor).order_by('-date')
        patient.total_appointments  = apts.count()
        patient.last_visit          = apts.first()
        patient.appointment_history = apts

    return render(request, 'doctor_my_patients.html', {
        'doctor':   doctor,
        'patients': patients,
        'today':    date.today(),
    })


def doctor_prescriptions(request):
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    prescriptions = Prescription.objects.filter(doctor=doctor).select_related('patient').prefetch_related('items').order_by('-date_issued')
    return render(request, 'doctor_prescriptions.html', {
        'doctor':        doctor,
        'prescriptions': prescriptions,
    })


def prescribe_medicine(request, patient_id):
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    patient = get_object_or_404(Patient, id=patient_id)

    # Safety check — doctor can only prescribe to their own patients
    if not Appointment.objects.filter(Patient=patient, Doctor=doctor).exists():
        messages.error(request, "You can only prescribe to your own patients.")
        return redirect('doctor_my_patients')

    if request.method == 'POST':
        notes         = request.POST.get('notes', '')
        medicine_names= request.POST.getlist('medicine_name[]')
        dosages       = request.POST.getlist('dosage[]')
        durations     = request.POST.getlist('duration_days[]')
        instructions  = request.POST.getlist('instructions[]')

        if not any(n.strip() for n in medicine_names):
            messages.error(request, "Please add at least one medicine.")
            return render(request, 'doctor_prescribe.html', {'patient': patient, 'doctor': doctor})

        prescription = Prescription.objects.create(
            patient = patient,
            doctor  = doctor,
            notes   = notes,
        )
        for i, name in enumerate(medicine_names):
            if name.strip():
                PrescriptionItem.objects.create(
                    prescription  = prescription,
                    medicine_name = name.strip(),
                    dosage        = dosages[i] if i < len(dosages) else '',
                    duration_days = int(durations[i]) if i < len(durations) and durations[i].isdigit() else 1,
                    instructions  = instructions[i] if i < len(instructions) else '',
                )

        messages.success(request, f"Prescription issued to {patient.Name}!")
        return redirect('doctor_my_patients')

    return render(request, 'doctor_prescribe.html', {'patient': patient, 'doctor': doctor})


# ===================== PATIENT VIEWS =====================

def _require_patient(request):
    """Returns Patient object or None if session is invalid."""
    if request.session.get('user_type') != 'patient':
        return None
    patient_id = request.session.get('patient_id')
    if not patient_id:
        return None
    try:
        return Patient.objects.get(id=patient_id)
    except Patient.DoesNotExist:
        return None


def patient_dashboard(request):
    patient = _require_patient(request)
    if not patient:
        messages.error(request, "Please log in as a patient.")
        return redirect('main_login')

    # Handle medical file upload
    if request.method == "POST" and 'file' in request.FILES:
        MedicalFile.objects.create(
            patient     = patient,
            title       = request.POST.get('title', 'Untitled Report'),
            description = request.POST.get('description', ''),
            file        = request.FILES['file'],
        )
        return redirect('patient_dashboard')

    today              = date.today()
    medical_files      = patient.medical_files.all().order_by('-uploaded_at')
    prescriptions      = patient.prescriptions.all().select_related('doctor').prefetch_related('items').order_by('-date_issued')
    today_appointments = Appointment.objects.filter(Patient=patient, date=today).count()

    # Billing — safe even if no bills exist yet
    bills     = patient.bills.all().order_by('-issue_date')
    total_due = sum(b.balance_due for b in bills if b.status != 'paid')

    return render(request, 'patient_dashboard.html', {
        'patient':             patient,
        'today':               today,
        'today_appointments':  today_appointments,
        'medical_files':       medical_files,
        'prescriptions':       prescriptions,
        'bills':               bills,
        'total_due':           total_due,
        'pending_bills_count': bills.filter(status__in=['unpaid', 'partial']).count(),
    })


def patient_book_appointment(request):
    patient = _require_patient(request)
    if not patient:
        return redirect('main_login')

    if request.method == "POST":
        doctor_id = request.POST.get('doctor')
        slot_id   = request.POST.get('slot_id')
        date_str  = request.POST.get('date')
        time_str  = request.POST.get('time')

        try:
            doctor = get_object_or_404(Doctor, id=doctor_id)

            # Slot-based booking
            if slot_id:
                slot = get_object_or_404(AppointmentSlot, id=slot_id, doctor=doctor)
                if not slot.is_available:
                    messages.error(request, 'This slot was just taken. Please choose another.')
                    return redirect('patient_book_appointment')

                # Check patient does not have another appointment same day with same doctor
                if Appointment.objects.filter(Doctor=doctor, Patient=patient, date=slot.date).exists():
                    messages.error(request, 'You already have an appointment with this doctor on that day.')
                    return redirect('patient_book_appointment')

                appt = Appointment.objects.create(
                    Doctor=doctor, Patient=patient,
                    date=slot.date, time=slot.start_time, slot=slot
                )
                slot.status = 'booked'
                slot.save()
                messages.success(request, f'Appointment confirmed with Dr. {doctor.Name} on {slot.date} at {slot.start_time.strftime("%H:%M")}.')
            else:
                # Fallback: no slot system yet for this doctor
                Appointment.objects.create(Doctor=doctor, Patient=patient, date=date_str, time=time_str)
                messages.success(request, "Appointment booked successfully.")

            return redirect('patient_appointments')

        except Exception as e:
            messages.error(request, f"Could not book appointment: {e}")

    # Build availability JSON for JS
    import json
    doctors = Doctor.objects.all()
    availability = {}
    for doc in doctors:
        schedules = DoctorSchedule.objects.filter(doctor=doc, is_active=True)
        leaves    = DoctorLeave.objects.filter(doctor=doc, date__gte=dt_date.today())
        availability[doc.id] = {
            'schedule_days': list(schedules.values_list('day_of_week', flat=True)),
            'leaves':        [str(l.date) for l in leaves],
        }
        # Annotate schedule summary for display
        day_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        doc.schedule_days = ', '.join(day_names[d] for d in availability[doc.id]['schedule_days']) if availability[doc.id]['schedule_days'] else ''

    return render(request, 'patient_book_appointment.html', {
        'doctors':          doctors,
        'today':            dt_date.today(),
        'availability_json': json.dumps(availability),
    })


def patient_appointments(request):
    patient = _require_patient(request)
    if not patient:
        return redirect('main_login')

    appointments = Appointment.objects.filter(Patient=patient).select_related('Doctor').order_by('-date', '-time')
    return render(request, 'patient_appointments.html', {
        'patient':      patient,
        'appointments': appointments,
        'today':        date.today(),
    })


def cancel_appointment(request, apt_id):
    patient = _require_patient(request)
    if not patient:
        return redirect('main_login')

    appointment = get_object_or_404(Appointment, id=apt_id, Patient=patient)
    appointment.delete()
    messages.success(request, "Appointment cancelled.")
    return redirect('patient_appointments')

def _require_staff(request):
    """Returns Staff object or None if session is invalid."""
    if request.session.get('user_type') != 'staff':
        return None
    staff_id = request.session.get('staff_id')
    if not staff_id:
        return None
    try:
        return Staff.objects.get(id=staff_id)
    except Staff.DoesNotExist:
        return None


def staff_dashboard(request):
    staff = _require_staff(request)
    if not staff:
        messages.error(request, "Please log in as staff.")
        return redirect('main_login')

    today        = date.today()
    recent_bills = Bill.objects.select_related('patient').order_by('-issue_date')[:10]
    total_pending = sum(b.balance_due for b in recent_bills if b.status in ['unpaid', 'partial'])

    return render(request, 'staff_dashboard.html', {
        'staff':                    staff,
        'today':                    today,
        'today_appointments_count': Appointment.objects.filter(date=today).count(),
        'total_appointments':       Appointment.objects.count(),
        'recent_bills':             recent_bills,
        'total_pending':            total_pending,
        'message':                  'Welcome to the Staff Dashboard!',
        'doctor_count':             Doctor.objects.count(),
        'staff_count':              Staff.objects.count(),
        'total_patients':           Patient.objects.count(),
        'all_doctors':              Doctor.objects.all().order_by('Name'),
        'all_staff_members':        Staff.objects.all().order_by('name'),
    })


def add_bill(request):
    staff = _require_staff(request)
    if not staff:
        return redirect('main_login')

    if request.method == 'POST':
        patient_id      = request.POST.get('patient')
        notes           = request.POST.get('notes', '')
        billing_item_ids= request.POST.getlist('billing_item[]')
        quantities      = request.POST.getlist('quantity[]')

        try:
            patient = get_object_or_404(Patient, id=patient_id)
            bill    = Bill.objects.create(patient=patient, notes=notes)

            for item_id, qty in zip(billing_item_ids, quantities):
                if item_id and qty.isdigit() and int(qty) > 0:
                    billing_item = get_object_or_404(BillingItem, id=item_id)
                    BillItem.objects.create(
                        bill         = bill,
                        billing_item = billing_item,
                        quantity     = int(qty),
                    )
            messages.success(request, f"Bill {bill.bill_number} created for {patient.Name}.")
        except Exception as e:
            messages.error(request, f"Error creating bill: {str(e)}")

        return redirect('staff_dashboard')

    # GET — show the form
    return render(request, 'add_bill.html', {
        'patients':      Patient.objects.all(),
        'billing_items': BillingItem.objects.filter(is_active=True),
    })


# ===================== STAFF — UPDATED VIEWS =====================

def View_Appointment(request):
    """Staff-styled appointment page with availability-aware booking form."""
    if not request.user.is_authenticated or not request.user.is_staff:
        if _require_staff(request) is None:
            return redirect('main_login')

    import json
    from datetime import date as dt
    appointments = Appointment.objects.select_related('Doctor', 'Patient').order_by('-date', '-time')
    doctors      = Doctor.objects.all()
    patients     = Patient.objects.all()
    today        = dt.today()

    # Build availability JSON for the calendar JS
    availability = {}
    for doc in doctors:
        schedules = DoctorSchedule.objects.filter(doctor=doc, is_active=True)
        leaves    = DoctorLeave.objects.filter(doctor=doc, date__gte=today)
        availability[doc.id] = {
            'schedule_days': list(schedules.values_list('day_of_week', flat=True)),
            'leaves':        [str(l.date) for l in leaves],
        }

    return render(request, 'view_appointment.html', {
        'appointments':    appointments,
        'doctors':         doctors,
        'patients':        patients,
        'today':           today,
        'doc':             appointments,
        'availability_json': json.dumps(availability),
    })


def View_Patient(request):
    """Staff-styled patient page with registration form."""
    if not request.user.is_authenticated or not request.user.is_staff:
        if _require_staff(request) is None:
            return redirect('main_login')

    patients = Patient.objects.all().order_by('Name')

    if request.method == 'POST':
        try:
            Patient.objects.create(
                Name    = request.POST.get('Name', '').strip(),
                Mobile  = request.POST.get('Mobile', '').strip(),
                Gender  = request.POST.get('Gender', '').strip(),
                Address = request.POST.get('Address', '').strip(),
                password= 'patient123',
            )
            messages.success(request, 'Patient registered successfully.')
        except Exception as e:
            messages.error(request, f'Error: {e}')
        return redirect('view_patient')

    return render(request, 'view_patient.html', {
        'patients': patients,
        'doc':      patients,  # backward compat
    })


def add_bill(request):
    """Full billing page — create bills + show all bills."""
    staff = _require_staff(request)
    if not staff:
        return redirect('main_login')

    from datetime import date as dt
    from django.db.models import Sum

    patients      = Patient.objects.all().order_by('Name')
    billing_items = BillingItem.objects.filter(is_active=True).order_by('category', 'name')
    all_bills     = Bill.objects.select_related('patient').order_by('-issue_date')
    pending_count       = all_bills.filter(status__in=['unpaid', 'partial']).count()
    total_outstanding   = sum(b.balance_due for b in all_bills if b.status in ['unpaid', 'partial'])
    selected_patient    = request.GET.get('patient', '')

    if request.method == 'POST':
        patient_id      = request.POST.get('patient')
        notes           = request.POST.get('notes', '')
        billing_ids     = request.POST.getlist('billing_item[]')
        quantities      = request.POST.getlist('quantity[]')

        try:
            patient = get_object_or_404(Patient, id=patient_id)
            bill    = Bill.objects.create(patient=patient, notes=notes)
            added   = 0
            for item_id, qty in zip(billing_ids, quantities):
                if item_id and qty and int(qty) > 0:
                    billing_item = get_object_or_404(BillingItem, id=item_id)
                    BillItem.objects.create(bill=bill, billing_item=billing_item, quantity=int(qty))
                    added += 1
            if added:
                messages.success(request, f'Bill {bill.bill_number} created for {patient.Name} with {added} item(s).')
            else:
                messages.success(request, f'Bill {bill.bill_number} created for {patient.Name} (no items added yet).')
        except Exception as e:
            messages.error(request, f'Error creating bill: {e}')
        return redirect('add_bill')

    return render(request, 'add_bill.html', {
        'staff':             staff,
        'patients':          patients,
        'billing_items':     billing_items,
        'all_bills':         all_bills,
        'pending_count':     pending_count,
        'total_outstanding': total_outstanding,
        'selected_patient':  selected_patient,
    })


def record_payment(request):
    """Record a payment against a bill."""
    staff = _require_staff(request)
    if not staff:
        return redirect('main_login')

    if request.method == 'POST':
        bill_id   = request.POST.get('bill_id')
        amount    = request.POST.get('amount', '0')
        method    = request.POST.get('method', 'cash')
        reference = request.POST.get('reference', '')

        try:
            bill        = get_object_or_404(Bill, id=bill_id)
            pay_amount  = float(amount)

            if pay_amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return redirect('add_bill')

            if pay_amount > float(bill.balance_due):
                messages.error(request, f'Amount exceeds balance due (NPR {bill.balance_due}).')
                return redirect('add_bill')

            bill.paid_amount += type(bill.paid_amount)(pay_amount)

            if bill.balance_due <= 0:
                bill.status = 'paid'
            elif bill.paid_amount > 0:
                bill.status = 'partial'

            bill.save()
            messages.success(request, f'Payment of NPR {pay_amount:.2f} recorded for Bill #{bill.bill_number}.')
        except Exception as e:
            messages.error(request, f'Error recording payment: {e}')

    return redirect('add_bill')



# ===================== STAFF — REGISTER PATIENT WITH CREDENTIALS =====================

def staff_register_patient(request):
    """
    Staff registers a patient.
    Mobile number is automatically used as both login ID and default password.
    After registration, a credential card is shown to staff to hand to the patient.
    """
    staff = _require_staff(request)
    if not staff:
        return redirect('main_login')

    if request.method == 'POST':
        name    = request.POST.get('Name', '').strip()
        mobile  = request.POST.get('Mobile', '').strip()
        gender  = request.POST.get('Gender', '').strip()
        address = request.POST.get('Address', '').strip()
        email   = request.POST.get('email', '').strip()

        # Validation
        if not all([name, mobile, gender, address]):
            messages.error(request, 'All required fields must be filled in.')
            return redirect('view_patient')

        if Patient.objects.filter(Mobile=mobile).exists():
            messages.error(request, f'A patient with mobile number {mobile} is already registered.')
            return redirect('view_patient')

        if email and Patient.objects.filter(email=email).exists():
            messages.error(request, f'A patient with email {email} is already registered.')
            return redirect('view_patient')

        # Mobile number is the default password — patient can use it to log in immediately
        patient = Patient.objects.create(
            Name     = name,
            Mobile   = mobile,
            Gender   = gender,
            Address  = address,
            email    = email or None,
            password = mobile,   # mobile number = default password
        )

        # Re-render the patient list with the credential card visible
        patients = Patient.objects.all().order_by('Name')
        return render(request, 'view_patient.html', {
            'staff':       staff,
            'patients':    patients,
            'doc':         patients,
            'new_patient': patient,   # triggers credential card in template
        })

    return redirect('view_patient')


# ===================== PATIENT BILLING =====================

def patient_billing(request):
    """Patient billing page — view bills created by staff, pay them."""
    patient = _require_patient(request)
    if not patient:
        messages.error(request, 'Please log in as a patient.')
        return redirect('main_login')

    bills      = Bill.objects.filter(patient=patient).prefetch_related('items__billing_item').order_by('-issue_date')
    total_due  = sum(b.balance_due for b in bills if b.status != 'paid')
    paid_count = bills.filter(status='paid').count()

    return render(request, 'patient_billing.html', {
        'patient':    patient,
        'bills':      bills,
        'total_due':  total_due,
        'paid_count': paid_count,
    })


def patient_pay_bill(request):
    """Patient submits a payment for one of their bills."""
    patient = _require_patient(request)
    if not patient:
        return redirect('main_login')

    if request.method == 'POST':
        bill_id   = request.POST.get('bill_id')
        amount    = request.POST.get('amount', '0')
        method    = request.POST.get('method', 'cash')
        reference = request.POST.get('reference', '')

        try:
            from decimal import Decimal
            bill = Bill.objects.get(id=bill_id, patient=patient)

            pay_amount = Decimal(str(amount))

            if pay_amount <= 0:
                messages.error(request, 'Payment amount must be greater than zero.')
                return redirect('patient_billing')

            if pay_amount > bill.balance_due:
                messages.error(request, f'Amount exceeds balance due (NPR {bill.balance_due}).')
                return redirect('patient_billing')

            # Update bill
            bill.paid_amount += pay_amount
            if bill.balance_due <= 0:
                bill.status = 'paid'
            elif bill.paid_amount > 0:
                bill.status = 'partial'
            bill.save()

            # Add note about payment method to bill notes
            from django.utils import timezone as tz
            note_line = f"\nPaid NPR {pay_amount} via {method}"
            if reference:
                note_line += f" (Ref: {reference})"
            note_line += f" on {tz.now().strftime('%Y-%m-%d %H:%M')}"
            bill.notes += note_line
            bill.save()

            messages.success(request, f'Payment of NPR {pay_amount} recorded successfully for Bill #{bill.bill_number}.')

        except Bill.DoesNotExist:
            messages.error(request, 'Bill not found.')
        except Exception as e:
            messages.error(request, f'Payment error: {e}')

    return redirect('patient_billing')



# ===================== STAFF REPORTS =====================

def staff_report(request):
    """Staff reports — shows all uploaded medical files from patients."""
    from django.db.models import Q

    staff = _require_staff(request)
    if not staff:
        messages.error(request, 'Please log in as staff.')
        return redirect('main_login')

    search         = request.GET.get('search', '').strip()
    patient_filter = request.GET.get('patient_id', '').strip()

    # All medical files — start with everything
    files = MedicalFile.objects.select_related('patient').order_by('-uploaded_at')

    # Apply search filter
    if search:
        files = files.filter(
            Q(title__icontains=search) |
            Q(patient__Name__icontains=search) |
            Q(description__icontains=search)
        )

    # Apply patient filter
    if patient_filter:
        files = files.filter(patient_id=patient_filter)

    # Stats (always from full dataset, not filtered)
    total_files         = MedicalFile.objects.count()
    patients_with_files = MedicalFile.objects.values('patient').distinct().count()
    latest_file         = MedicalFile.objects.order_by('-uploaded_at').first()
    latest_upload       = latest_file.uploaded_at if latest_file else None

    return render(request, 'staff_report.html', {
        'staff':               staff,
        'medical_files':       files,
        'all_patients':        Patient.objects.all().order_by('Name'),
        'search':              search,
        'patient_filter':      patient_filter,
        'total_files':         total_files,
        'patients_with_files': patients_with_files,
        'latest_upload':       latest_upload,
    })


# ===================== AVAILABILITY SYSTEM VIEWS =====================

def get_slots(request):
    """AJAX — returns available slots for a doctor on a date as JSON."""
    from django.http import JsonResponse
    from datetime import datetime

    doctor_id = request.GET.get('doctor')
    date_str  = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'slots': []})

    try:
        from datetime import date as dt
        doctor      = get_object_or_404(Doctor, id=doctor_id)
        target_date = dt.fromisoformat(date_str)

        # Check leave
        if DoctorLeave.objects.filter(doctor=doctor, date=target_date).exists():
            return JsonResponse({'slots': [], 'message': 'Doctor is on leave this day.'})

        # Generate slots from schedule if not already generated
        dow      = target_date.weekday()  # Mon=0
        schedule = DoctorSchedule.objects.filter(doctor=doctor, day_of_week=dow, is_active=True).first()
        if schedule:
            schedule.generate_slots_for_date(target_date)

        # Return all slots for this date
        slots = AppointmentSlot.objects.filter(doctor=doctor, date=target_date).order_by('start_time')
        return JsonResponse({
            'slots': [
                {
                    'id':       s.id,
                    'start':    s.start_time.strftime('%H:%M'),
                    'end':      s.end_time.strftime('%H:%M'),
                    'status':   s.status,
                    'duration': schedule.slot_duration_minutes if schedule else 20,
                }
                for s in slots
            ]
        })
    except Exception as e:
        return JsonResponse({'slots': [], 'error': str(e)})


# ── Doctor schedule management ────────────────────────

def doctor_schedule(request):
    """Doctor views and manages their weekly schedule."""
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    schedules = DoctorSchedule.objects.filter(doctor=doctor).order_by('day_of_week')
    leaves    = DoctorLeave.objects.filter(doctor=doctor, date__gte=dt_date.today()).order_by('date')

    from .models import DAYS
    return render(request, 'doctor_schedule.html', {
        'doctor':    doctor,
        'schedules': schedules,
        'leaves':    leaves,
        'days':      DAYS,
        'today':     str(dt_date.today()),
    })


def add_schedule(request):
    """Doctor adds a working day to their schedule."""
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    if request.method == 'POST':
        day      = request.POST.get('day_of_week')
        start    = request.POST.get('start_time')
        end      = request.POST.get('end_time')
        duration = int(request.POST.get('slot_duration_minutes', 20))
        max_p    = int(request.POST.get('max_patients', 15))

        if start >= end:
            messages.error(request, 'End time must be after start time.')
            return redirect('doctor_schedule')

        obj, created = DoctorSchedule.objects.update_or_create(
            doctor=doctor, day_of_week=int(day),
            defaults={
                'start_time':            start,
                'end_time':              end,
                'slot_duration_minutes': duration,
                'max_patients':          max_p,
                'is_active':             True,
            }
        )
        messages.success(request, f'Schedule {"added" if created else "updated"} successfully.')

    return redirect('doctor_schedule')


def toggle_schedule(request, pk):
    """Pause or activate a schedule day."""
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    if request.method == 'POST':
        sched = get_object_or_404(DoctorSchedule, pk=pk, doctor=doctor)
        sched.is_active = not sched.is_active
        sched.save()
        messages.success(request, f'Schedule {"activated" if sched.is_active else "paused"}.')

    return redirect('doctor_schedule')


def delete_schedule(request, pk):
    """Remove a schedule day entirely."""
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    if request.method == 'POST':
        get_object_or_404(DoctorSchedule, pk=pk, doctor=doctor).delete()
        messages.success(request, 'Schedule day removed.')

    return redirect('doctor_schedule')


def add_leave(request):
    """Doctor marks a day as leave/off."""
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    if request.method == 'POST':
        date_str = request.POST.get('date')
        reason   = request.POST.get('reason', '')
        try:
            from datetime import date as dt
            leave_date = dt.fromisoformat(date_str)
            DoctorLeave.objects.get_or_create(
                doctor=doctor, date=leave_date,
                defaults={'reason': reason}
            )
            # Block all existing available slots on this date
            AppointmentSlot.objects.filter(
                doctor=doctor, date=leave_date, status='available'
            ).update(status='blocked')
            messages.success(request, f'{leave_date.strftime("%b %d, %Y")} marked as leave.')
        except Exception as e:
            messages.error(request, f'Error: {e}')

    return redirect('doctor_schedule')


def delete_leave(request, pk):
    """Remove a leave day so slots become available again."""
    doctor = _require_doctor(request)
    if not doctor:
        return redirect('main_login')

    leave = get_object_or_404(DoctorLeave, pk=pk, doctor=doctor)
    # Unblock slots on that date
    AppointmentSlot.objects.filter(
        doctor=doctor, date=leave.date, status='blocked'
    ).update(status='available')
    leave.delete()
    messages.success(request, 'Leave day removed.')
    return redirect('doctor_schedule')


# ===================== STAFF BOOK APPOINTMENT (slot-based) =====================

def staff_book_appointment(request):
    """Staff books an appointment for an offline patient using the slot system."""
    if not request.user.is_authenticated or not request.user.is_staff:
        if _require_staff(request) is None:
            return redirect('main_login')

    if request.method == 'POST':
        doctor_id  = request.POST.get('doctor_id')
        patient_nm = request.POST.get('patient')
        slot_id    = request.POST.get('slot_id')
        date_val   = request.POST.get('date')
        time_val   = request.POST.get('time')

        try:
            doctor  = get_object_or_404(Doctor, id=doctor_id)
            patient = get_object_or_404(Patient, Name=patient_nm)

            if slot_id:
                # Slot-based booking
                slot = get_object_or_404(AppointmentSlot, id=slot_id, doctor=doctor)
                if not slot.is_available:
                    messages.error(request, 'That slot was just taken. Please choose another.')
                    return redirect('view_appointment')
                Appointment.objects.create(
                    Doctor=doctor, Patient=patient,
                    date=slot.date, time=slot.start_time, slot=slot
                )
                slot.status = 'booked'
                slot.save()
                messages.success(request, f'Appointment booked for {patient.Name} with Dr. {doctor.Name} on {slot.date} at {slot.start_time.strftime("%H:%M")}.')
            else:
                # Manual fallback (no schedule set)
                Appointment.objects.create(
                    Doctor=doctor, Patient=patient,
                    date=date_val, time=time_val
                )
                messages.success(request, f'Appointment booked for {patient.Name} with Dr. {doctor.Name}.')

        except Exception as e:
            messages.error(request, f'Booking error: {e}')

    return redirect('view_appointment')
