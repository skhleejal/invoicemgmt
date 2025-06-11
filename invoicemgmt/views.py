from django.shortcuts import render, redirect
from django.forms import inlineformset_factory
from .models import Customer, Invoice, InvoiceLineItem
from .forms import InvoiceForm, InvoiceLineItemForm


def home(request):
    return render(request, 'invoicemgmt/home.html')

def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'invoicemgmt/customer_list.html', {'customers': customers})

def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'invoicemgmt/invoice_list.html', {'invoices': invoices})

def create_invoice(request):
    InvoiceLineItemFormSet = inlineformset_factory(
        Invoice, InvoiceLineItem,
        form=InvoiceLineItemForm,
        extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceLineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save()
            formset.instance = invoice
            formset.save()
            return redirect('/add_invoice')
    else:
        form = InvoiceForm()
        formset = InvoiceLineItemFormSet()

    return render(request, 'invoicemgmt/create_invoice.html', {
        'form': form,
        'formset': formset,
    })
from django.shortcuts import get_object_or_404

def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoicemgmt/invoice_detail.html', {'invoice': invoice})
# from django.shortcuts import get_object_or_404
# def invoice_detail(request, pk):
#     invoice = Invoice.objects.get(pk=pk)
#     related_items = invoice.invoicelineitem_set.all()  # Example: Fetch related line items
#     return render(request, 'invoicemgmt/invoice_detail.html', {
#         'invoice': invoice,
#         'related_items': related_items,
#     })
