from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from .models import Customer, Invoice, InvoiceLineItem,Product
from .forms import InvoiceForm, InvoiceLineItemForm, CustomerForm
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render

class InvoiceDeleteView(DeleteView):
    model = Invoice
    template_name = 'invoicemgmt/confirm_delete_invoice.html'
    success_url = reverse_lazy('invoice_list')


def home(request):
    sales_amount = Invoice.objects.filter(status="paid").aggregate(total=Sum('total_amount'))['total'] or 0
    total_invoices = Invoice.objects.count()
    pending_bills = Invoice.objects.filter(status="open").count()
    due_amount = Invoice.objects.filter(status="open").aggregate(total=Sum('total_amount'))['total'] or 0
    total_products = Product.objects.count() if 'Product' in globals() else 0
    total_customers = Customer.objects.count()
    paid_bills = Invoice.objects.filter(status="paid").count()
    recent_invoices = Invoice.objects.order_by('-invoice_date')[:5]


    context = {
        'sales_amount': sales_amount,
        'total_invoices': total_invoices,
        'pending_bills': pending_bills,
        'due_amount': due_amount,
        'total_products': total_products,
        'total_customers': total_customers,
        'paid_bills': paid_bills,
        'recent_invoices':recent_invoices
    }
    return render(request, 'invoicemgmt/home.html', context)



def create_receipt(request):
    InvoiceLineItemFormSet = inlineformset_factory(
        Invoice, InvoiceLineItem,
        form=InvoiceLineItemForm,
        extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceLineItemFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.document_type = 'receipt'  # if you have a field for it
            invoice.save()
            formset.instance = invoice
            formset.save()
            return redirect('invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceLineItemFormSet()

    return render(request, 'invoicemgmt/create_invoice.html', {
        'form': form,
        'formset': formset,
        'document_type': 'receipt',
    })


def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'invoicemgmt/customer_list.html', {'customers': customers})

def create_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_invoice')
           
    else:
        form = CustomerForm()
    return render(request, 'invoicemgmt/create_customer.html', {'form': form})


def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted successfully.")
        return redirect('customer_list')

    return render(request, 'invoicemgmt/confirm_delete_customer.html', {'customer': customer})

def select_document_type(request):
    if request.method == 'POST':
        doc_type = request.POST.get('document_type')
        if doc_type == 'invoice':
            return redirect('create_invoice')
        elif doc_type == 'receipt':
            return redirect('create_receipt')
    return render(request, 'invoicemgmt/select_document_type.html')


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
            messages.success(request,'successfully saved')
            invoice.save()  # Recalculate totals after line items are saved
            return redirect('invoice_list')
    else:
        form = InvoiceForm()
        formset = InvoiceLineItemFormSet()

    return render(request, 'invoicemgmt/create_invoice.html', {
        'form': form,
        'formset': formset,
    })
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoicemgmt/invoice_detail.html', {'invoice': invoice})



def mark_invoice_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.status = 'paid'
    invoice.save()
    return redirect('invoice_list')

def customer_list(request):
    query = request.GET.get('q')
    if query:
        customers = Customer.objects.filter(name__icontains=query)
    else:
        customers = Customer.objects.all()
    return render(request, 'invoicemgmt/customer_list.html', {'customers': customers, 'query': query})

def invoice_list(request):
    query = request.GET.get('q')
    if query:
        invoices = Invoice.objects.filter(
            customer__name__icontains=query
        ) | Invoice.objects.filter(
            invoice_number__icontains=query
        )
    else:
        invoices = Invoice.objects.all()
    return render(request, 'invoicemgmt/invoice_list.html', {'invoices': invoices, 'query': query})



def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'invoicemgmt/customer_detail.html', {'customer': customer})



def update_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    InvoiceLineItemFormSet = inlineformset_factory(
        Invoice, InvoiceLineItem,
        form=InvoiceLineItemForm,
        extra=0, can_delete=True
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceLineItemFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            invoice.save()  # Recalculate totals
            return redirect('invoice_detail', pk=invoice.pk)
    else:
        form = InvoiceForm(instance=invoice)
        formset = InvoiceLineItemFormSet(instance=invoice)

    return render(request, 'invoicemgmt/update_invoice.html', {
        'form': form,
        'formset': formset,
        'invoice': invoice
    })