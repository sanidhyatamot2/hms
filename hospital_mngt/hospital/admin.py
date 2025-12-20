from django.contrib import admin
from.models import Patient, Doctor, Appointment

from hospital.models import Doctor, Patient, Appointment

# Register your models here.
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Appointment)
