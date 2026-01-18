from django.contrib import admin
from .models import Bill, BillItem, BillingItem, Patient, Doctor, Appointment

from hospital.models import Doctor, Patient, Appointment

# Inline for BillItem (so you can add items directly from Bill page)
class BillItemInline(admin.TabularInline):
    model = BillItem
    extra = 1  # number of empty rows shown by default
    fields = ('billing_item', 'quantity', 'unit_price', 'discount', 'amount')
    readonly_fields = ('amount',)  # auto-calculated, so read-only
    can_delete = True

# Admin for BillingItem (simple list)
@admin.register(BillingItem)
class BillingItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name',)

# Admin for Bill (with inline BillItems)
@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'patient', 'issue_date', 'status', 'total_amount', 'balance_due')
    list_filter = ('status', 'issue_date')
    search_fields = ('bill_number', 'patient__Name')
    inlines = [BillItemInline]  # ← THIS ENABLES ADDING ITEMS DIRECTLY!
    readonly_fields = ('bill_number', 'subtotal', 'total_amount', 'balance_due')
    fieldsets = (
        ('Basic Info', {
            'fields': ('bill_number', 'patient', 'appointment', 'issue_date', 'due_date', 'status')
        }),
        ('Financials', {
            'fields': ('subtotal', 'discount', 'tax', 'total_amount', 'paid_amount', 'balance_due')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
    )


# Register your models here.
admin.site.register(Doctor)
admin.site.register(Patient)
admin.site.register(Appointment)
