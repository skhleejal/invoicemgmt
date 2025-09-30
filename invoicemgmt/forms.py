from django import forms
from .models import  Invoice, InvoiceLineItem, Customer
from .models import Purchase, PurchaseLineItem

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'address', 'po_box', 'city', 'email', 'country', 'phone', 'fax', 'vat_number']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Customer name'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full address'}),
            'po_box': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'P.O. Box'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'}),
            'fax': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fax'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VAT Number'}),
        }
        labels = {
            'name': 'Customer Name*',
            'address': 'Address',
            'po_box': 'P.O. Box',
            'city': 'City',
            'email': 'Email',
            'country': 'Country',
            'phone': 'Phone',
            'fax': 'Fax',
            'vat_number': 'VAT Number',
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone

class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer', 'invoice_date', 'vat_number', 'payment_method',
            'po_number', 'po_date', 'delivery_note', 'do_date', 'ship_to',
            'total_taxable', 'total_vat', 'total_amount', 'amount_in_words'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'invoice_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'vat_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'VAT Number'}),
            'payment_method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'CDC'}),
            'po_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'P.O. Number'}),
            'po_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'delivery_note': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Delivery Note'}),
            'do_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ship_to': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ship To'}),
            'total_taxable': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'total_vat': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'total_amount': forms.NumberInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            'amount_in_words': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
            # 'special_discount': forms.NumberInput(attrs={'placeholder': 'Enter discount amount'}),

        }
        labels = {
            'customer': 'Customer*',
            'invoice_date': 'Invoice Date*',
            'vat_number': 'VAT Number',
            'payment_method': 'Payment Method',
            'po_number': 'P.O. Number',
            'po_date': 'P.O. Date',
            'delivery_note': 'Delivery Note',
            'do_date': 'D.O. Date',
            'ship_to': 'Ship To',
            'total_taxable': 'Total Taxable Amount*',
            'total_vat': 'Total VAT Amount*',
            'total_amount': 'Total Amount*',
            'amount_in_words': 'Amount in Words',
        }
        help_texts = {
            'total_taxable': 'Calculated automatically.',
            'total_vat': 'Calculated automatically.',
            'total_amount': 'Sum of taxable and VAT.',
            'payment_method': 'CDC / Cash / Transfer etc.',
        }

    def clean_customer(self):
        customer = self.cleaned_data.get('customer')
        if not customer:
            raise forms.ValidationError("Customer is required.")
        if not customer.country:
            raise forms.ValidationError("Customer country is required for currency detection.")
        return customer

class InvoiceLineItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceLineItem
        fields = ['description', 'product', 'quantity', 'unit_price', 'vat_rate', 'is_discount']
        widgets = {
            'description': forms.TextInput(attrs={'placeholder': 'Enter description'}),
            'unit_price': forms.NumberInput(attrs={'placeholder': 'Enter amount'}),
            'is_discount': forms.CheckboxInput(),
        }
        labels = {
            'product': 'Product*',
            'description': 'Description',
            'quantity': 'Quantity*',
            'unit_price': 'Unit Price*',
            'vat_rate': 'VAT Rate (%)*',
        }
        help_texts = {
            'description': 'Describe the item briefly.',
            'quantity': 'Quantity of the product.',
            'unit_price': 'Rate per unit.',
            'vat_rate': 'VAT percentage (e.g., 5).',
        }

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier_name']
        widgets = {
            'supplier_name': forms.TextInput(attrs={'placeholder': 'Enter supplier name', 'class': 'form-control'}),
        }
        labels = {
            'supplier_name': 'Supplier Name*',
        }

class PurchaseLineItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseLineItem
        fields = ['product', 'quantity', 'price', 'vat_rate']
        widgets = {
            'product': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'value': '5.00'}),
        }
        labels = {
            'product': 'Product*',
            'quantity': 'Quantity*',
            'price': 'Unit Price*',
            'vat_rate': 'VAT Rate (%)*',
        }
        help_texts = {
            'product': 'Enter product name.',
            'quantity': 'Quantity of the product.',
            'price': 'Rate per unit.',
            'vat_rate': 'VAT percentage (e.g., 5).',
        }