from django.db import models

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
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True)
    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    duration_days = models.IntegerField()
    date_issued = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

class Bill(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True)
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('paid', 'Paid'), ('overdue', 'Overdue')])