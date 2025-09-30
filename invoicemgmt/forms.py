from django import forms
from .models import  Invoice, InvoiceLineItem, Customer
from .models import Purchase, PurchaseLineItem



class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'po_box', 'city', 'email', 'country', 'phone', 'fax', 'vat_number']

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone and not phone.isdigit():
            raise forms.ValidationError("Phone number must contain only digits.")
        return phone


class InvoiceForm(forms.ModelForm):
    class Meta:
        model = Invoice
        fields = [
            'customer', 'invoice_date', 'vat_number',
            'po_number', 'po_date', 'delivery_note', 'do_date', 'ship_to',
            'total_taxable', 'total_vat', 'total_amount',
            'amount_in_words', 'payment_method', 'invoice_type'
        ]
        widgets = {
            'invoice_date': forms.DateInput(attrs={'type': 'date'}),
            'po_date': forms.DateInput(attrs={'type': 'date'}),
            'do_date': forms.DateInput(attrs={'type': 'date'}),
            'total_taxable': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'total_vat': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'total_amount': forms.NumberInput(attrs={'readonly': 'readonly'}),
            'amount_in_words': forms.TextInput(attrs={'readonly': 'readonly'}),
            'payment_method': forms.TextInput(),
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
            'payment_method': 'Payment Method',
            'invoice_type': 'Document Type',
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
        fields = [ 'product' ,'description', 'quantity', 'unit_price', 'vat_rate']
        widgets = {
            'product': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 2}),
            'quantity': forms.NumberInput(),
            'unit_price': forms.NumberInput(),
            'vat_rate': forms.NumberInput(),
        }
        labels = {
            # 'product': 'Product',
            'description': 'Description',
            'quantity': 'Quantity',
            'unit_price': 'Unit Price',
            'vat_rate': 'VAT Rate (%)',
        }
        help_texts = {
            # 'product': 'Select a product to autofill price/VAT.',
            'description': 'Describe the item briefly.',
            'quantity': 'Quantity of the product.',
            'unit_price': 'Rate per unit.',
            'vat_rate': 'VAT percentage.',
        }

    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['product'].queryset = Product.objects.all()
    #     self.fields['product'].required = True
    #     self.fields['product'].empty_label = "Select a product"


# class ProductForm(forms.ModelForm):
#     class Meta:
#         model = Product
#         fields = ['name', 'description', 'price', 'stock', 'reorder_level']
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 2}),
#             'price': forms.NumberInput(),
#             'stock': forms.NumberInput(),
#             'reorder_level': forms.NumberInput(),
#         }
#         labels = {
#             'name': 'Product Name',
#             'description': 'Description',
#             'price': 'Unit Price',
#             'stock': 'Available Stock',
#             'reorder_level': 'Reorder Threshold',
#         }


# class ProductPurchaseForm(forms.Form):
#     supplier_name = forms.CharField(label="Supplier Name", max_length=100)
#     product_id = forms.ModelChoiceField(queryset=Product.objects.all(), label="Product")
#     quantity = forms.IntegerField(min_value=1, label="Quantity Purchased")
#     unit_price = forms.DecimalField(max_digits=10, decimal_places=2, label="Purchase Price per Unit")


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier_name', 'po_number', 'po_date', 'delivery_note', 'do_date', 'ship_to']
        widgets = {
            'supplier_name': forms.TextInput(attrs={'placeholder': 'Enter supplier name', 'class': 'form-control'}),
            'po_number': forms.TextInput(attrs={'placeholder': 'P.O. Number', 'class': 'form-control'}),
            'po_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'delivery_note': forms.TextInput(attrs={'placeholder': 'Delivery Note', 'class': 'form-control'}),
            'do_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ship_to': forms.TextInput(attrs={'placeholder': 'Ship To Address', 'class': 'form-control'}),
        }
        labels = {
            'supplier_name': 'Supplier Name',
            'po_number': 'P.O. Number',
            'po_date': 'P.O. Date',
            'delivery_note': 'Delivery Note',
            'do_date': 'D.O. Date',
            'ship_to': 'Ship To',
        }

class PurchaseLineItemForm(forms.ModelForm):
    class Meta:
        model = PurchaseLineItem
        fields = ['product', 'quantity', 'price', 'vat_rate']
        widgets = {
            'product': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'vat_rate': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'product': 'Product',
            'quantity': 'Quantity',
            'price': 'Unit Price',
            'vat_rate': 'VAT Rate (%)',
        }
        help_texts = {
            'product': 'Select a product.',
            'quantity': 'Quantity of the product.',
            'price': 'Rate per unit.',
            'vat_rate': 'VAT percentage (e.g., 5).',
        }


# class QuotationForm(forms.ModelForm):
#     class Meta:
#         model = Quotation
#         fields = [
#             'quote_number', 'date', 'customer', 'ship_to_name', 'ship_to_address',
#             'total_amount',  'terms', 'company_name'
#         ]

# class QuotationLineItemForm(forms.ModelForm):
#     class Meta:
#         model = QuotationLineItem
#         fields = ['product', 'quantity', 'price',  'vat_rate']
#         widgets = {
#             'product': forms.Select(attrs={'class': 'form-select'}),
#             # 'unit_price': forms.NumberInput(),
#             'price': forms.NumberInput(),
#             'vat_rate': forms.NumberInput(),
#         }
#         labels = {
#             'product': 'Product',
#             'quantity': 'Quantity',
#             # 'unit_price': 'Unit Price',
#             'price': 'Price',
#             'vat_rate': 'VAT Rate (%)',
#         }
#         help_texts = {
#             'product': 'Select a product to autofill details.',
#             'quantity': 'Quantity of the product.',
#             # 'unit_price': 'Rate per unit.',
#             'price': 'Total price for the quantity.',
#             'vat_rate': 'VAT percentage.',
#         }

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['product'].queryset = Product.objects.all()
#         self.fields['product'].required = True
#         self.fields['product'].empty_label = "Select a product"


# class DeliveryNoteForm(forms.ModelForm):
#     class Meta:
#         model = DeliveryNote
#         fields = [
#             'company_name', 'company_address', 'company_email', 'company_phone',
#             'delivery_to_name', 'delivery_to_address', 'date', 'due_date',
#             'terms', 'signature', 'signature_date'
#         ]


# DeliveryNoteLineItemFormSet = forms.inlineformset_factory(
#     DeliveryNote,
#     DeliveryNoteLineItem,
#     fields=['product', 'description', 'quantity', 'complete'],
#     extra=1,
#     can_delete=True
# )