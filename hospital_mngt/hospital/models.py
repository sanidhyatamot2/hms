from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# Create your models here.
class Doctor(models.Model):
    Name= models.CharField(max_length=100)
    Mobile= models.IntegerField()
    Special = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, blank=True, null=True)        # ADD THIS
    password = models.CharField(max_length=128)

    def __str__(self):
        return self.Name


class Patient(models.Model):
    Name= models.CharField(max_length=100)
    Gender= models.CharField(max_length=100)
    Mobile = models.CharField(max_length=15)
    Address= models.TextField()
    email = models.EmailField(max_length=100, blank=True, null=True)         # optional
    password = models.CharField(max_length=128)   # ADD THIS

    def __str__(self):
        return self.Name

class Appointment(models.Model):
    Doctor= models.ForeignKey(Doctor,on_delete=models.CASCADE)
    Patient= models.ForeignKey(Patient,on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()

class MedicalFile(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_files')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='medical_files/%Y/%m/%d/')
    description = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.patient}"
    
class Prescription(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='prescriptions')
    doctor = models.ForeignKey('Doctor', on_delete=models.SET_NULL, null=True, related_name='prescriptions_issued')
    appointment = models.ForeignKey('Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    date_issued = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Prescription for {self.patient} by {self.doctor} on {self.date_issued.date()}"

class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name='items')
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)  # e.g., "500mg, 1 tablet 3x/day"
    duration_days = models.PositiveIntegerField()
    instructions = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.medicine_name} - {self.dosage}"

class BillingItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=50, choices=[
        ('consultation', 'Consultation'),
        ('lab_test', 'Lab Test'),
        ('medicine', 'Medicine'),
        ('procedure', 'Procedure'),
        ('room', 'Room Charge'),
        ('other', 'Other'),
    ])
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - NPR {self.price}"


class Bill(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='bills')
    bill_number = models.CharField(max_length=20, unique=True, editable=False)
    issue_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
    ], default='unpaid')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        if not self.bill_number:
            last = Bill.objects.order_by('-id').first()
            self.bill_number = f"BILL-{last.id + 1 if last else 1:06d}"
        super().save(*args, **kwargs)

    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount


class BillItem(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='items')
    billing_item = models.ForeignKey(BillingItem, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.unit_price = self.billing_item.price
        self.amount = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update parent bill total
        self.bill.total_amount = sum(item.amount for item in self.bill.items.all())
        self.bill.save()

class Staff(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=50, default="Receptionist")
    phone = models.CharField(max_length=15, blank=True)
    joined_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.role})"