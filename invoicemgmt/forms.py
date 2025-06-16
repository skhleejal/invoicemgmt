from django import forms
from .models import Invoice, InvoiceLineItem, Customer,Product

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'po_box', 'city', 'email' ,'country', 'phone', 'fax', 'vat_number']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer', 'invoice_number', 'invoice_date', 'vat_number',
            'po_number', 'po_date', 'delivery_note', 'do_date', 'ship_to',
            'total_taxable', 'total_vat', 'total_amount', 'amount_in_words', 'payment_method','invoice_type'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'po_date': forms.DateInput(attrs={'type': 'date'}),
            'do_date': forms.DateInput(attrs={'type': 'date'}),
            'total_taxable': forms.NumberInput(attrs={'readonly': 'readonly'}),  # Calculated automatically
            'total_vat': forms.NumberInput(attrs={'readonly': 'readonly'}),      # Calculated automatically
            'total_amount': forms.NumberInput(attrs={'readonly': 'readonly'}),  # Calculated automatically
            'amount_in_words': forms.TextInput(attrs={'readonly': 'readonly'}),
        }
        labels = {
            'customer': 'Customer',
            'invoice_number': 'Invoice Number',
            'invoice_date': 'Invoice Date',
            'vat_number': 'VAT Number',
            'po_number': 'PO Number',
            'po_date': 'PO Date',
            'delivery_note': 'Delivery Note',
            'do_date': 'DO Date',
            'ship_to': 'Ship To',
            'total_taxable': 'Total Taxable Amount',
            'total_vat': 'Total VAT Amount',
            'total_amount': 'Total Amount',
            'amount_in_words': 'Amount in Words',
            'payment_method': 'Payment Method'
        }
        help_texts = {
            'total_taxable': 'Enter the total taxable amount.',
            'total_vat': 'Enter the total VAT amount.',
            'payment_method': 'Select the payment method.'
        }

class InvoiceLineItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceLineItem
        fields = ['product','description', 'quantity', 'unit_price', 'vat_rate']
        widgets = {
            
            'product': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'rows': 2}),
            'unit_price': forms.NumberInput(),
            'vat_rate': forms.NumberInput()
        }
        labels = {
            'product': 'Select Product',
            'description': 'Description',
            'quantity': 'Quantity',
            'unit_price': 'Unit Price',
            'vat_rate': 'VAT Rate'
        }
        help_texts = {
            'product': 'Choose a product to auto-fill price and VAT.',
            'description': 'Enter a brief description of the item.',
            'quantity': 'Enter the quantity of the item.',
            'unit_price': 'Enter the unit price of the item.',
            'vat_rate': 'Enter the VAT rate applicable to this item.'
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].queryset = Product.objects.all()
        self.fields['product'].empty_label = "Select a product"



class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price', 'stock', 'reorder_level']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 2}),
            'price': forms.NumberInput(),
            # 'vat_rate': forms.NumberInput(),
            'quantity_in_stock': forms.NumberInput(),
            'reorder_level': forms.NumberInput(),
        }