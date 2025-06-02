from django.contrib import admin
from .models import Invoice, Customer, InvoiceLineItem

admin.site.register(Invoice)
admin.site.register(Customer)
admin.site.register(InvoiceLineItem)
# from django.contrib import admin
# from .models import Customer, Invoice, InvoiceLineItem

# @admin.register(Customer)
# class CustomerAdmin(admin.ModelAdmin):
#     list_display = ('name', 'city', 'country', 'phone', 'vat_number')
#     search_fields = ('name', 'city', 'country', 'vat_number')

# @admin.register(Invoice)
# class InvoiceAdmin(admin.ModelAdmin):
#     list_display = ('invoice_number', 'customer', 'invoice_date', 'total_amount', 'payment_method')
#     search_fields = ('invoice_number', 'customer__name')
#     list_filter = ('invoice_date', 'payment_method', 'customer')

# @admin.register(InvoiceLineItem)
# class InvoiceLineItemAdmin(admin.ModelAdmin):
#     list_display = ('invoice', 'description', 'quantity', 'unit_price', 'amount', 'vat_rate', 'vat_amount')
#     search_fields = ('description', 'invoice__invoice_number')
#     list_filter = ('vat_rate',)

# If you want to register without custom admin:
# admin.site.register(Customer)
# admin.site.register(Invoice)
# admin.site.register(InvoiceLineItem)