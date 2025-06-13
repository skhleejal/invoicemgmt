from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from .models import Customer, Invoice, InvoiceLineItem,Product
from .forms import InvoiceForm, InvoiceLineItemForm, CustomerForm
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404

def home(request):
    sales_amount = Invoice.objects.filter(status="paid").aggregate(total=Sum('total_amount'))['total'] or 0
    total_invoices = Invoice.objects.count()
    pending_bills = Invoice.objects.filter(status="open").count()
    due_amount = Invoice.objects.filter(status="open").aggregate(total=Sum('total_amount'))['total'] or 0
    total_products = Product.objects.count() if 'Product' in globals() else 0
    total_customers = Customer.objects.count()
    paid_bills = Invoice.objects.filter(status="paid").count()

    context = {
        'sales_amount': sales_amount,
        'total_invoices': total_invoices,
        'pending_bills': pending_bills,
        'due_amount': due_amount,
        'total_products': total_products,
        'total_customers': total_customers,
        'paid_bills': paid_bills,
    }
    return render(request, 'invoicemgmt/home.html', context)

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