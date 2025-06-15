from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from .models import Customer, Invoice, InvoiceLineItem,Product
from .forms import InvoiceForm, InvoiceLineItemForm, CustomerForm,ProductForm
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.shortcuts import redirect
from .models import RecurringInvoice, Invoice, InvoiceLineItem
from datetime import date
from django.utils.timezone import now
from django.template.loader import get_template
from django.utils.timezone import now
from xhtml2pdf import pisa
from django.http import HttpResponse
from django.core.mail import EmailMessage

def generate_invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    template = get_template('invoicemgmt/invoice_pdf.html')
    html = template.render({'invoice': invoice, 'now': now()})

    # Generate PDF in memory
    from io import BytesIO
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)

    pdf_file.seek(0)  # Go back to the beginning of the PDF file

    # Send email with PDF as attachment
    customer_email = invoice.customer.email  # make sure this field exists
    if customer_email:
        subject = f"Invoice #{invoice.pk} from Sherook Kalba"
        body = f"Dear {invoice.customer.name},\n\nPlease find attached your invoice #{invoice.pk}.\n\nThank you!"
        email = EmailMessage(subject, body, to=[customer_email])
        email.attach(f"Invoice_{invoice.pk}.pdf", pdf_file.read(), 'application/pdf')
        email.send()

    # Optional: return PDF as browser download
    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Invoice_{invoice.pk}.pdf"'
    return response


def generate_recurring_invoices(request):
    today = now().date()
    recurring_list = RecurringInvoice.objects.filter(active=True, next_due_date__lte=today)

    for recur in recurring_list:
        # Generate new invoice
        invoice = Invoice.objects.create(
            customer=recur.customer,
            invoice_date=today,
            status='unpaid',
            total_amount=recur.amount,
        )
        InvoiceLineItem.objects.create(
            invoice=invoice,
            product=recur.product,
            quantity=1,
            amount=recur.amount
        )
        # Set next due date
        if recur.interval == 'monthly':
            recur.next_due_date = today + timedelta(days=30)
        elif recur.interval == 'weekly':
            recur.next_due_date = today + timedelta(weeks=1)
        recur.save()

    return redirect('home')

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
    low_stock_products = Product.objects.filter(stock__lt=5)


    context = {
        'sales_amount': sales_amount,
        'total_invoices': total_invoices,
        'pending_bills': pending_bills,
        'due_amount': due_amount,
        'total_products': total_products,
        'total_customers': total_customers,
        'paid_bills': paid_bills,
        'recent_invoices':recent_invoices,
        'low_stock_products': low_stock_products
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
            invoice = form.save(commit=False)
            formset.instance = invoice

            stock_errors = []

            # Step 1: Check stock before saving
            for item_form in formset:
                product = item_form.cleaned_data.get('product')
                quantity = item_form.cleaned_data.get('quantity')

                if product and quantity:
                    if product.stock < quantity:
                        stock_errors.append(
                            f"⚠ Not enough stock for {product.name} (Available: {product.stock}, Requested: {quantity})"
                        )

            if stock_errors:
                for err in stock_errors:
                    messages.error(request, err)
                return render(request, 'invoicemgmt/create_invoice.html', {
                    'form': form,
                    'formset': formset,
                    'document_type': 'invoice'
                })

            # Step 2: Save invoice (temporarily)
            invoice.save()

            total_amount = 0
            line_items = formset.save(commit=False)

            for item_form in line_items:
                product = item_form.product
                quantity = item_form.quantity
                price = product.price
                item_form.amount = quantity * price  # set amount
                item_form.invoice = invoice
                item_form.save()

                total_amount += item_form.amount

                # Reduce stock
                product.stock -= quantity
                product.save()

            invoice.total_amount = total_amount
            invoice.save()

            messages.success(request, '✅ Invoice saved and stock updated.')
            return redirect('invoice_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InvoiceForm()
        formset = InvoiceLineItemFormSet()

    return render(request, 'invoicemgmt/create_invoice.html', {
        'form': form,
        'formset': formset,
        'document_type': 'invoice'
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


def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Optional: or to invoice creation
    else:
        form = ProductForm()
    return render(request, 'invoicemgmt/add_products.html', {'form': form})


def product_list(request):
    products = Product.objects.all()
    return render(request, 'invoicemgmt/product_list.html', {'products': products})

def delete(self, request, *args, **kwargs):
    self.object = self.get_object()
    for item in self.object.invoicelineitem_set.all():
        item.product.stock += item.quantity
        item.product.save()
    return super().delete(request, *args, **kwargs)
