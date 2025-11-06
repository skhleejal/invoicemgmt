from django import forms
from .models import  Invoice, InvoiceLineItem, Customer,Product
from .models import Purchase, PurchaseLineItem,DeliveryNote,DeliveryNoteItem

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

        return customer

class InvoiceLineItemForm(forms.ModelForm):
    class Meta:
        model = InvoiceLineItem
        fields = ['product','description_fk','description', 'quantity', 'unit_price', 'vat_rate', 'is_discount']
        widgets = {
            'description_fk': forms.Select(attrs={'class': 'form-control'}), 
            'description': forms.TextInput(attrs={'placeholder': 'Enter description'}),
            'unit_price': forms.NumberInput(attrs={'placeholder': 'Enter amount'}),
            'is_discount': forms.NumberInput(attrs={'placeholder': 'Enter discount amount', 'class': 'form-control'}),  # Change to numeric input
        }
        labels = {
            'product': 'Product*',
            'description_fk': 'Product Description',
            'description': 'Description',
            'quantity': 'Quantity*',
            'unit_price': 'Unit Price*',
            'vat_rate': 'VAT Rate (%)*',
            'is_discount': 'Discount Amount',  # Update label
        }
        help_texts = {
            'description_fk': 'Select a product from the dropdown.',
            'description': 'Describe the item briefly.',
            'quantity': 'Quantity of the product.',
            'unit_price': 'Rate per unit.',
            'vat_rate': 'VAT percentage (e.g., 5).',
            'is_discount': 'Enter the discount amount (negative value).',
        }

class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier_name', 'date', 'purchase_number']
        widgets = {
            'supplier_name': forms.TextInput(attrs={'placeholder': 'Enter supplier name', 'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Editable date field
            'purchase_number': forms.TextInput(attrs={'placeholder': 'Enter purchase number', 'class': 'form-control'}),
        }
        labels = {
            'supplier_name': 'Supplier Name*',
            'date': 'Date*',
            'purchase_number': 'Purchase Number*',
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



    
# class DeliveryNoteForm(forms.ModelForm):
#     class Meta:
#         model = DeliveryNote
#         fields = [
#             'company_name', 'company_address', 'company_phone',s
#             'delivery_to_name', 'delivery_to_address', 'date', 'due_date',
#             'terms', 'signature', 'signature_date'
#         ]
#         widgets = {
#             'company_name': forms.TextInput(attrs={'class': 'form-control'}),
#             'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'date': forms.DateInput(attrs={'type': 'date'}),
#         }

# DeliveryNoteLineItemFormSet = forms.inlineformset_factory(
#     DeliveryNote,
#     DeliveryNoteLineItem,
#     fields=['product_name', 'description', 'quantity', 'complete'],
#     extra=20,
#     can_delete=True
# )
class DeliveryNoteForm(forms.ModelForm):
    class Meta:
        model = DeliveryNote
        fields = [
            'company_name', 'company_address', 'company_phone',
            'delivery_to_name', 'delivery_to_address', 
            'lpo_number', 'delivery_to_phone', 'delivery_to_fax', 
            'date', 'due_date',
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'company_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'company_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_to_name': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_to_address': forms.TextInput(attrs={'class': 'form-control'}),
            'lpo_number': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_to_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'delivery_to_fax': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'yyyy-mm-dd'}),
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'placeholder': 'yyyy-mm-dd'}),
        }

# CRITICAL: Renamed formset to match the Item model
DeliveryNoteItemFormSet = forms.inlineformset_factory(
    DeliveryNote,
    DeliveryNoteItem,
    fields=['description', 'unit', 'quantity', 'completed_value'], 
    fk_name='note', 
    extra=5, # Reduced from 20 for cleaner UI/testing
    can_delete=True
)
from django import forms
from .models import Product

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'price', 'vat_rate']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control'}),
        }