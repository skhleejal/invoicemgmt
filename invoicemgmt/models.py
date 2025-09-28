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
            return num2words(n, lang='en') + f" {currency}"
    except Exception:
        return str(n)

# ----- Models -----


# class Shop(models.Model):
#     name = models.CharField(max_length=100)
#     address = models.TextField(blank=True, null=True)
#     # Add other fields as needed

#     def __str__(self):
#         return self.name

class Customer(models.Model):
    name = models.CharField(max_length=255)
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


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    vat_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    reorder_level = models.IntegerField(default=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_low_stock(self):
        return self.stock <= self.reorder_level
    
    def __str__(self):
        desc = self.description[:30] if self.description else "No description"
        return f"{self.name} – {desc}"



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
    payment_method = models.CharField(max_length=100, blank=True, null=True, default="CDC")
    amount_in_words = models.CharField(max_length=512, blank=True, default="N/A")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')

    invoice_type_choices = (
        ('Receipt', 'Receipt'),
        ('Invoice', 'Invoice'),
    )
    invoice_type = models.CharField(max_length=50, choices=invoice_type_choices, blank=True, null=True, default='')

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def save(self, *args, **kwargs):
        # Auto-generate invoice number only if not already set
        if not self.invoice_number:
            with transaction.atomic():
                # Filter numeric-only invoice numbers
                latest = Invoice.objects.select_for_update().filter(
                    invoice_number__regex=r'^\d+$'
                ).aggregate(
                    max_number=Max('invoice_number')
                )['max_number']

                self.invoice_number = str(int(latest) + 1) if latest else '1000'

        # Calculate totals only if invoice already exists (has line items)
        taxable = 0
        vat = 0
        if self.pk:
            for item in self.line_items.all():
                taxable += item.amount
                vat += item.vat_amount

        self.total_taxable = taxable
        self.total_vat = vat
        self.total_amount = taxable + vat

        # Currency & amount in words
        country = getattr(self.customer, 'country', None)
        currency = COUNTRY_CURRENCY.get(country, 'USD') if country else 'USD'
        self.amount_in_words = number_to_words(self.total_amount, currency=currency)

        super().save(*args, **kwargs)

    def get_currency_symbol(self):
        country = getattr(self.customer, 'country', None)
        currency = COUNTRY_CURRENCY.get(country, 'USD') if country else 'USD'
        return CURRENCY_SYMBOL.get(currency, '$')

    def __str__(self):
        try:
            customer_name = self.customer.name if self.customer else "Unknown Customer"
        except:
            customer_name = "Unknown Customer"
        return f"Invoice #{self.invoice_number or 'N/A'} for {customer_name}"    


class RecurringInvoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(max_length=10, choices=[('monthly', 'Monthly'), ('weekly', 'Weekly')])
    next_due_date = models.DateField()
    active = models.BooleanField(default=True)


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        if self.product and not self.unit_price:
            self.unit_price = self.product.price
        self.amount = self.quantity * self.unit_price
        self.vat_amount = (self.vat_rate / 100) * self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description[:30]}"
    


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
    purchase = models.ForeignKey('Purchase', related_name='line_items', on_delete=models.CASCADE)  # <-- Add this
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)  # Add this
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # Add this

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        self.vat_amount = self.amount * (self.vat_rate / 100)
        super().save(*args, **kwargs)


class Quotation(models.Model):
    quote_number = models.CharField(max_length=50)
    date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    ship_to_name = models.CharField(max_length=100, blank=True)
    ship_to_address = models.CharField(max_length=255, blank=True)
    # subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    terms = models.TextField(blank=True)
    company_name = models.CharField(max_length=100, blank=True)
    email_sent = models.BooleanField(default=False)  # <-- Track email status
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"Quotation {self.quote_number} for {self.customer.name}"

class QuotationLineItem(models.Model):
    quotation = models.ForeignKey(Quotation, on_delete=models.CASCADE, related_name='line_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.price
        vat_rate_decimal = Decimal(str(self.vat_rate)) / Decimal('100')
        self.vat_amount = self.amount * vat_rate_decimal
        super().save(*args, **kwargs)


class DeliveryNote(models.Model):
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    company_email = models.EmailField()
    company_phone = models.CharField(max_length=50)
    delivery_to_name = models.CharField(max_length=255)
    delivery_to_address = models.TextField()
    date = models.DateField()
    due_date = models.DateField(blank=True, null=True)
    # You can use a related model for line items if needed
    terms = models.TextField(blank=True, null=True)
    signature = models.CharField(max_length=255, blank=True, null=True)
    signature_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"Delivery Note to {self.delivery_to_name} on {self.date}"
    


class DeliveryNoteLineItem(models.Model):
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField()
    complete = models.BooleanField(default=False)