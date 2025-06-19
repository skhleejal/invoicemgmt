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


CURRENCY_SYMBOL = {
    'USD': '$',
    'INR': '₹',
    'EUR': '€',
    'GBP': '£',
    'AED': 'د.إ',
    # Add more as needed
}


COUNTRY_CHOICES = [
    ('United States', 'United States'),
    ('India', 'India'),
    ('United Kingdom', 'United Kingdom'),
    ('Germany', 'Germany'),
    ('France', 'France'),
    ('Italy', 'Italy'),
    ('Spain', 'Spain'),
    ('UAE', 'UAE'),
    # Add more as needed
]


COUNTRY_PHONE_CODES = {
    'United States': '+1',
    'India': '+91',
    'United Kingdom': '+44',
    'Germany': '+49',
    'France': '+33',
    'Italy': '+39',
    'Spain': '+34',
    'UAE': '+971',
    # Add more as needed
}

def number_to_words(n, currency='USD'):
    try:
        # Only use 'currency' if supported
        if currency in ['USD', 'INR', 'EUR', 'GBP']:
            return num2words(n, to='currency', lang='en', currency=currency)
        else:
            # Fallback: just return the number in words
            return num2words(n, lang='en') + f" {currency}"
    except Exception:
        return str(n)

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
        # Always sync phone_code with selected country
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
    created_at = models.DateTimeField(auto_now_add=True)
    
    reorder_level = models.IntegerField(default=2)

    def __str__(self):
        return f"{self.name} – {self.description[:30]}"  # show both name and short desc
    
    def is_low_stock(self):
        return self.stock <= self.reorder_level

class Invoice(models.Model):
    invoice_number = models.CharField(max_length=100)
    invoice_date = models.DateField()
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    vat_number = models.CharField(max_length=100,blank=True, null=True)
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
    invoice_type_choice=(
        ('Receipt','Receipt'),
        ('Invoice','Invoice'),
      
    )
    invoice_type=models.CharField(max_length=50,default='',blank=True,null=True,choices=invoice_type_choice)

    

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='open')

    def get_currency_symbol(self):
        country = self.customer.country if self.customer and self.customer.country else ''
        currency = COUNTRY_CURRENCY.get(country, 'USD')
        return CURRENCY_SYMBOL.get(currency, '$')
    


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
    
class RecurringInvoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    interval = models.CharField(max_length=10, choices=[('monthly', 'Monthly'), ('weekly', 'Weekly')])
    next_due_date = models.DateField()
    active = models.BooleanField(default=True)


class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.TextField()
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
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
    
    # products

