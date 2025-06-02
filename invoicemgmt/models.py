from django.db import models


def number_to_words(n):
    # Simple implementation for demonstration; use 'num2words' for production
    try:
        from num2words import num2words
        return num2words(n, to='currency', lang='en')
    except ImportError:
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

class Invoice(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    invoice_number = models.IntegerField(unique=True)
    invoice_date = models.DateField()
    vat_number = models.CharField(max_length=100)
    po_number = models.CharField(max_length=100, blank=True, null=True)
    po_date = models.DateField(blank=True, null=True)
    delivery_note = models.CharField(max_length=100, blank=True, null=True)
    do_date = models.DateField(blank=True, null=True)
    ship_to = models.CharField(max_length=255, blank=True, null=True)
    total_taxable = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_vat = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_in_words = models.CharField(max_length=512, blank=True)
    payment_method = models.CharField(max_length=100, blank=True, null=True, default="CDC")
    created_at = models.DateTimeField(auto_now_add=True)

    
    def save(self, *args, **kwargs):
        self.total_amount = self.total_taxable + self.total_vat
        self.amount_in_words = number_to_words(self.total_amount)
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Invoice #{self.invoice_number} for {self.customer.name}"

class InvoiceLineItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='line_items', on_delete=models.CASCADE)
    description = models.TextField()
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    vat_rate = models.DecimalField(max_digits=4, decimal_places=2, default=5.00)
    vat_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.amount = self.quantity * self.unit_price
        self.vat_amount = (self.vat_rate / 100) * self.amount
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.description[:30]}"