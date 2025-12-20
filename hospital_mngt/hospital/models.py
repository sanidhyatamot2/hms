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
    title = models.CharField(max_length=200, default="Medical Report")
    file = models.FileField(upload_to='medical_files/%Y/%m/%d/')  # saves to media/medical_files/year/month/day/
    uploaded_at = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} - {self.patient.Name}"