from django.db import models
from django.utils.timezone import now
from django.db.models import Max
from num2words import num2words
from django.db import transaction
from .utils import number_to_words, COUNTRY_CURRENCY, CURRENCY_SYMBOL
from django.conf import settings
from django.contrib.auth.models import User
from decimal import Decimal
import datetime

# --- NEW: Import Django Signals ---
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


# ----- Currency and Country Config -----
COUNTRY_CURRENCY = {
    'United States': 'USD',
    'India': 'INR',
    'United Kingdom': 'GBP',
    'Germany': 'EUR',
    'France': 'EUR',
    'Italy': 'EUR',
    'Spain': 'EUR',
    'UAE': 'AED',
}

CURRENCY_SYMBOL = {
    'USD': '$',
    'INR': '₹',
    'EUR': '€',
    'GBP': '£',
    'AED': 'د.إ',
}

COUNTRY_PHONE_CODES = {
    'United States': '+1',
    'India': '+91',
    'United Kingdom': '+44',
    'Germany': '+49',
    'France': '+33',
    'Italy': '+39',
    'Spain': '+34',
    'UAE': '+971',
}

COUNTRY_CHOICES = [(c, c) for c in COUNTRY_CURRENCY.keys()]

# ----- Utils -----
def number_to_words(n, currency='USD'):
    try:
        if currency in ['USD', 'INR', 'EUR', 'GBP']:
            return num2words(n, to='currency', lang='en', currency=currency)
        else:
            # Format for AED and other currencies
            integer_part = int(n)
            fractional_part = int((n - integer_part) * 100)
            
            words = num2words(integer_part, lang='en').title()
            
            if fractional_part > 0:
                words += f" {currency} and " + num2words(fractional_part, lang='en') + " fils"
            else:
                words += f" {currency} only"
            return words
            
    except Exception:
        return str(n)

# ----- Models -----

class Customer(models.Model):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    po_box = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, choices=COUNTRY_CHOICES, blank=True, null=True)
    phone_code = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    fax = models.CharField(max_length=50, blank=True, null=True)
    vat_number = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.country:
            self.phone_code = COUNTRY_PHONE_CODES.get(self.country, '')
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100, unique=True, blank=True)
    invoice_date = models.DateField()
    customer = models.ForeignKey('Customer', on_delete=models.CASCADE)
    vat_number = models.CharField(max_length=100, blank=True, null=True)
    po_number = models.CharField(max_length=100, blank=True, null=True)
    po_date = models.DateField(blank=True, null=True)
    delivery_note = models.CharField(max_length=100, blank=True, null=True)
    do_date = models.DateField(blank=True, null=True)
    ship_to = models.CharField(max_length=255, blank=True, null=True)
    total_taxable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_method = models.CharField(max_length=100, blank=True, null=True, default="30 days credit")
    amount_in_words = models.CharField(max_length=512, blank=True, default="N/A")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')

    invoice_type_choices = (('Receipt', 'Receipt'), ('Invoice', 'Invoice'),)
    invoice_type = models.CharField(max_length=50, choices=invoice_type_choices, blank=True, null=True, default='')

    STATUS_CHOICES = [('open', 'Open'), ('paid', 'Paid'),]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')
    
    # --- NEW: Central method to update totals ---
    def update_totals(self):
        taxable = Decimal(0)
        vat = Decimal(0)
        
        for item in self.line_items.all():
            taxable += item.taxable_value
            vat += item.vat_amount

        self.total_taxable = taxable
        self.total_vat = vat
        self.total_amount = taxable + vat

        country = getattr(self.customer, 'country', None)
        currency = COUNTRY_CURRENCY.get(country, 'USD') if country else 'USD'
        self.amount_in_words = number_to_words(self.total_amount, currency=currency)

        # Use update_fields to avoid recursion with signals
        Invoice.objects.filter(pk=self.pk).update(
            total_taxable=self.total_taxable,
            total_vat=self.total_vat,
            total_amount=self.total_amount,
            amount_in_words=self.amount_in_words
        )

    def save(self, *args, **kwargs):
        if not self.invoice_number:
            with transaction.atomic():
                latest = Invoice.objects.select_for_update().filter(
                    invoice_number__regex=r'^\d+$'
                ).aggregate(
                    max_number=Max('invoice_number')
                )['max_number']

                if latest:
                    next_number = int(latest) + 1
                else:
                    next_number = 1025
                
                self.invoice_number = str(next_number)

        # Note: Total calculation logic is removed from here and handled by signals.
        super().save(*args, **kwargs)

    def __str__(self):
        customer_name = self.customer.name if self.customer else "Unknown Customer"
        return f"Invoice #{self.invoice_number or 'N/A'} for {customer_name}"


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.TextField()
    product = models.CharField(max_length=255, blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00) # Changed default to 5%
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    taxable_value = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    is_discount = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.is_discount:
            self.amount = -abs(self.unit_price)
            self.taxable_value = self.amount
            self.vat_amount = 0
            self.vat_rate = 0
        else:
            self.amount = Decimal(self.quantity) * Decimal(self.unit_price)
            self.vat_amount = (Decimal(self.vat_rate) / Decimal(100)) * self.amount
            self.taxable_value = self.amount
            
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description[:30]}"


# --- NEW: Signal to automatically update Invoice totals ---
@receiver([post_save, post_delete], sender=InvoiceLineItem)
def update_invoice_on_line_item_change(sender, instance, **kwargs):
    """
    When an InvoiceLineItem is saved or deleted,
    it triggers the update_totals method on its parent Invoice.
    """
    instance.invoice.update_totals()


# Make sure these models are active in your models.py file

class Purchase(models.Model):
    supplier_name = models.CharField(max_length=255)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date = models.DateField(auto_now_add=True)
    purchased_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    purchase_number = models.CharField(max_length=100, unique=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.purchase_number:
            with transaction.atomic():
                latest = Purchase.objects.select_for_update().filter(
                    purchase_number__regex=r'^\d+$'
                ).aggregate(
                    max_number=Max('purchase_number')
                )['max_number']
                self.purchase_number = str(int(latest) + 1) if latest else '1000'
        # Calculate totals if purchase already exists (has line items)
        total = 0
        vat = 0
        if self.pk:
            for item in self.line_items.all():
                total += item.amount
                vat += item.vat_amount
        self.total_amount = total + vat
        self.vat_amount = vat
        super().save(*args, **kwargs)


class PurchaseLineItem(models.Model):
    purchase = models.ForeignKey('Purchase', related_name='line_items', on_delete=models.CASCADE)
    product = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        self.vat_amount = self.amount * (self.vat_rate / 100)
        super().save(*args, **kwargs)