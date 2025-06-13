from django.db import models
from django.utils.timezone import now
from num2words import num2words

COUNTRY_CURRENCY = {
    'United States': 'USD',
    'India': 'INR',
    'United Kingdom': 'GBP',
    'Germany': 'EUR',
    'France': 'EUR',
    'Italy': 'EUR',
    'Spain': 'EUR',
    'UAE': 'AED',
    # Add more as needed
}

def number_to_words(n, currency='USD'):
    try:
        return num2words(n, to='currency', lang='en', currency=currency)
    except Exception:
        return str(n)
    
class Customer(models.Model):
    name = models.CharField(max_length=255)
    po_box = models.CharField(max_length=50, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    fax = models.CharField(max_length=50, blank=True, null=True)
    vat_number = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.name
    
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vat_number = models.CharField(max_length=100)
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

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')


    def save(self, *args, **kwargs):
        taxable = 0
        vat = 0
        if self.pk:
            for item in self.line_items.all():
                taxable += item.amount
                vat += item.vat_amount
        self.total_taxable = taxable
        self.total_vat = vat
        self.total_amount = taxable + vat

        # Get currency code based on customer's country
        country = self.customer.country if self.customer and self.customer.country else ''
        currency = COUNTRY_CURRENCY.get(country, 'USD')
        self.amount_in_words = number_to_words(self.total_amount, currency=currency)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Invoice #{self.invoice_number} for {self.customer.name}"
class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=20, decimal_places=2, default=0.00)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        self.vat_amount = (self.vat_rate / 100) * self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description[:30]}"