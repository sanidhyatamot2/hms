from django.db import models
from django.utils import timezone

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
    name = models.CharField(max_length=200)  # e.g., "General Consultation", "X-Ray"
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
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - NPR {self.price}"

class Bill(models.Model):
    patient = models.ForeignKey('Patient', on_delete=models.CASCADE, related_name='bills')
    appointment = models.ForeignKey('Appointment', on_delete=models.SET_NULL, null=True, blank=True)
    bill_number = models.CharField(max_length=20, unique=True, editable=False)
    issue_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('unpaid', 'Unpaid'),
        ('partial', 'Partially Paid'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
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
    discount = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        if not self.unit_price and self.billing_item:
            self.unit_price = self.billing_item.price
        self.amount = (self.quantity * self.unit_price) - self.discount
        super().save(*args, **kwargs)
        self.bill.save()  # Recalculate total in parent bill