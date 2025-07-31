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
from django.template.loader import get_template, render_to_string
from django.utils.timezone import now
from xhtml2pdf import pisa
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.core.mail import EmailMessage
from io import BytesIO
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
import os
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseForbidden
import json
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
import pandas as pd
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from .models import Invoice, Product, Customer
from .models import Purchase
from .forms import PurchaseForm
from django.db.models import Q

from .models import Purchase,PurchaseLineItem
from .forms import PurchaseForm, PurchaseLineItemForm



# def register(request):
#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             user = form.save()
#             # login(request, user)  # ✅ This is critical — logs in new user
#             return render(request, 'login')
#     else:
#         form = UserCreationForm()
#     return render(request, 'registration/register.html', {'form': form})


# def register(request):
#     if request.user.is_authenticated:
#         return redirect('home')  # Don't let logged-in users re-register

#     if request.method == 'POST':
#         form = UserCreationForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('registration_success')  # or to login page
#     else:
#         form = UserCreationForm()
    
#     return render(request, 'registration/register.html', {'form': form})


def register(request):
    if request.user.is_authenticated:
        return redirect('home')  # Don't let logged-in users register again

    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # 👇 Choose whether to auto-login or not
            # login(request, user)
            return render(request, 'registration/register_success.html')  # ✅ create this template
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})

@permission_required('invoicemgmt.view_invoice', raise_exception=True)
@login_required
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

@login_required
def link_callback(uri, rel):
    """
    Convert HTML URIs to absolute system paths for xhtml2pdf to access local files.
    """
    result = finders.find(uri)
    if result:
        return result
    elif uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
        if os.path.isfile(path):
            return path
    return uri  # Fallback, may cause failure if file doesn't exist

@permission_required('invoicemgmt.view_invoice', raise_exception=True)
@login_required
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

class InvoiceDeleteView(PermissionRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoicemgmt/confirm_delete_invoice.html'
    success_url = reverse_lazy('invoice_list')
    permission_required = 'invoicemgmt.delete_invoice'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        for item in self.object.invoicelineitem_set.all():
            item.product.stock += item.quantity
            item.product.save()
        return super().delete(request, *args, **kwargs)

# from .models import Invoice, Product, Customer  # Make sure your models are imported
@login_required
def home(request):
    if not request.user.is_staff:
        messages.warning(request, "Your account is pending approval.")
        return render(request, 'registration/pending_approval.html')
    
    # Role-based filtering
    if request.user.is_superuser:
        invoice_qs = Invoice.objects.all()
        total_customers = Customer.objects.count()
    else:
        invoice_qs = Invoice.objects.filter(created_by=request.user)
        # Only customers served by this user
        total_customers = Customer.objects.filter(invoice__created_by=request.user).distinct().count()

    # Use invoice_qs for all stats!
    sales_amount = invoice_qs.filter(status="paid").aggregate(total=Sum('total_amount'))['total'] or 0
    total_invoices = invoice_qs.count()
    pending_bills = invoice_qs.filter(status="open").count()
    due_amount = invoice_qs.filter(status="open").aggregate(total=Sum('total_amount'))['total'] or 0
    paid_bills = invoice_qs.filter(status="paid").count()
    recent_invoices = invoice_qs.order_by('-invoice_date')[:5]
    total_products = Product.objects.count()
    low_stock_products = Product.objects.filter(stock__lt=5)

    # --- Chart Data: Last 6 Months Sales ---
    today = datetime.today()
    last_6_months = [today.replace(day=1) - timedelta(days=30*i) for i in reversed(range(6))]
    month_labels = [d.strftime('%b') for d in last_6_months]

    monthly_sales = invoice_qs.filter(status="paid") \
        .annotate(month=TruncMonth('invoice_date')) \
        .values('month') \
        .annotate(total=Sum('total_amount')) \
        .order_by('month')

    sales_dict = {entry['month'].strftime('%b'): entry['total'] for entry in monthly_sales if entry['month']}
    chart_data = [float(sales_dict.get(month, 0)) for month in month_labels]

    # --- Doughnut Chart: Money Breakdown by Status ---
    paid_total = invoice_qs.filter(status='paid').aggregate(total=Sum('total_amount'))['total'] or 0
    unpaid_total = invoice_qs.filter(status='unpaid').aggregate(total=Sum('total_amount'))['total'] or 0
    open_total = invoice_qs.filter(status='open').aggregate(total=Sum('total_amount'))['total'] or 0

    status_labels = ['Paid', 'Unpaid', 'Open']
    status_data = [float(paid_total), float(unpaid_total), float(open_total)]

    context = {
        'sales_amount': sales_amount,
        'total_invoices': total_invoices,
        'pending_bills': pending_bills,
        'due_amount': due_amount,
        'total_products': total_products,
        'total_customers': total_customers,
        'paid_bills': paid_bills,
        'recent_invoices': recent_invoices,
        'low_stock_products': low_stock_products,
        'chart_labels': json.dumps(month_labels),
        'chart_data': json.dumps(chart_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
    }

    return render(request, 'invoicemgmt/home.html', context)

@permission_required('invoicemgmt.change_product', raise_exception=True)
@login_required
def update_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            return redirect('product_list')
    else:
        form = ProductForm(instance=product)
    return render(request, 'invoicemgmt/product_form.html', {'form': form})


@permission_required('invoicemgmt.change_product', raise_exception=True)
@login_required
def restock_product(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if request.method == "POST":
        quantity = int(request.POST.get("quantity", 0))
        if quantity > 0:
            product.stock += quantity
            product.save()
            messages.success(request, f"✅ Restocked {product.name} by {quantity} units.")
        else:
            messages.warning(request, "⚠️ Enter a valid quantity.")

    return redirect('product_list')

@permission_required('invoicemgmt.delete_product', raise_exception=True)
@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    product.delete()
    messages.success(request, f"🗑️ Product '{product.name}' deleted successfully.")
    return redirect('product_list')
@login_required
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

@permission_required('invoicemgmt.view_customer', raise_exception=True)
@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'invoicemgmt/customer_list.html', {'customers': customers})


@permission_required('invoicemgmt.add_customer', raise_exception=True)
@login_required
def create_customer(request):
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('create_invoice')
           
    else:
        form = CustomerForm()
    return render(request, 'invoicemgmt/create_customer.html', {'form': form})

@permission_required('invoicemgmt.delete_customer', raise_exception=True)
@login_required
def delete_customer(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == "POST":
        customer.delete()
        messages.success(request, "Customer deleted successfully.")
        return redirect('customer_list')

    return render(request, 'invoicemgmt/confirm_delete_customer.html', {'customer': customer})

@login_required
def select_document_type(request):
    if request.method == 'POST':
        doc_type = request.POST.get('document_type')
        if doc_type == 'invoice':
            return redirect('create_invoice')
        elif doc_type == 'receipt':
            return redirect('create_receipt')
    return render(request, 'invoicemgmt/select_document_type.html')

@permission_required('invoicemgmt.add_invoice', raise_exception=True)
@login_required
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
            invoice.created_by = request.user  # Assign the invoice to the current user
            formset.instance = invoice

            stock_errors = []

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

            try:
                invoice.save()  # 💡 This will now safely calculate amount_in_words

                total_amount = 0
                line_items = formset.save(commit=False)

                for item_form in line_items:
                    product = item_form.product
                    quantity = item_form.quantity
                    price = product.price
                    item_form.amount = quantity * price
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

            except Exception as e:
                messages.error(request, f"❌ Error saving invoice: {str(e)}")

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


@permission_required('invoicemgmt.view_invoice', raise_exception=True)
@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    return render(request, 'invoicemgmt/invoice_detail.html', {'invoice': invoice})

@permission_required('invoicemgmt.change_invoice', raise_exception=True)
@login_required
def mark_invoice_paid(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.status = 'paid'
    invoice.save()
    return redirect('invoice_list')

@permission_required('invoicemgmt.view_customer', raise_exception=True)
@login_required
def customer_list(request):
    query = request.GET.get('q')
    if query:
        customers = Customer.objects.filter(name__icontains=query)
    else:
        customers = Customer.objects.all()
    return render(request, 'invoicemgmt/customer_list.html', {'customers': customers, 'query': query})

@permission_required('invoicemgmt.view_invoice', raise_exception=True)
@login_required
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


@permission_required('invoicemgmt.view_customer', raise_exception=True)
@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    return render(request, 'invoicemgmt/customer_detail.html', {'customer': customer})

@permission_required('invoicemgmt.change_product', raise_exception=True)
@login_required
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


@permission_required('invoicemgmt.add_product', raise_exception=True)
@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('product_list')  # Optional: or to invoice creation
    else:
        form = ProductForm()
    return render(request, 'invoicemgmt/add_products.html', {'form': form})

@permission_required('invoicemgmt.view_product', raise_exception=True)
@login_required
def product_list(request):
    products = Product.objects.all()
    return render(request, 'invoicemgmt/product_list.html', {'products': products})

@login_required
def delete(self, request, *args, **kwargs):
    self.object = self.get_object()
    for item in self.object.invoicelineitem_set.all():
        item.product.stock += item.quantity
        item.product.save()
    return super().delete(request, *args, **kwargs)

@permission_required('invoicemgmt.view_invoice', raise_exception=True)
@login_required
def email_invoice(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    template = get_template('invoicemgmt/invoice_pdf.html')

    invoice_count = Invoice.objects.count()  # Optional, if used in the template

@csrf_exempt
@login_required
@permission_required('invoicemgmt.add_invoice', raise_exception=True)
def import_invoices_from_excel(request):
    if request.method == "POST" and request.FILES.get("excel_file"):
        file = request.FILES["excel_file"]
        filepath = default_storage.save(file.name, file)
        df = pd.read_excel(default_storage.path(filepath))

        for _, row in df.iterrows():
            try:
                # --- Extract & Clean Values ---
                customer_name = str(row.get("Customer Name", "")).strip()
                customer_country = str(row.get("Country", "")).strip()
                product_name = str(row.get("Product", "")).strip()
                quantity = int(row.get("Quantity", 1))
                unit_price = float(row.get("Unit Price", 0))
                vat_rate = float(row.get("VAT Rate", 5.0))
                po_number = str(row.get("PO Number", "")).strip()
                invoice_date = row.get("Invoice Date")
                status = str(row.get("Status", "open")).strip().lower()

                # --- Handle Invoice Number ---
                invoice_number = row.get("Invoice Number")
                invoice_number = str(int(invoice_number)).strip() if pd.notna(invoice_number) else None

                # --- Check for Duplicate Invoice Number ---
                if invoice_number and Invoice.objects.filter(invoice_number=invoice_number).exists():
                    messages.warning(request, f"⚠️ Skipped duplicate invoice number: {invoice_number}")
                    continue

                # --- Create/Get Customer ---
                customer, _ = Customer.objects.get_or_create(
                    name=customer_name,
                    defaults={"country": customer_country}
                )

                # --- Create/Get Product ---
                product, _ = Product.objects.get_or_create(
                    name=product_name,
                    defaults={"price": unit_price, "vat_rate": vat_rate}
                )

                # --- Create Invoice ---
                invoice = Invoice.objects.create(
                    invoice_number=invoice_number,
                    customer=customer,
                    invoice_date=invoice_date,
                    po_number=po_number,
                    status='paid' if status == 'paid' else 'open',
                )

                # --- Add Line Item ---
                InvoiceLineItem.objects.create(
                    invoice=invoice,
                    product=product,
                    quantity=quantity,
                    unit_price=unit_price,
                    vat_rate=vat_rate,
                    description=product_name
                )

                # --- Final save to recalculate totals & currency-in-words ---
                invoice.save()

            except Exception as e:
                messages.error(request, f"❌ Error on row with Invoice #{row.get('Invoice Number', 'N/A')}: {str(e)}")

        messages.success(request, "✅ Invoices imported successfully.")
        return redirect("invoice_list")

    return render(request, "invoicemgmt/import_invoices.html")


@login_required
def purchase_form(request):
    PurchaseLineItemFormSet = inlineformset_factory(
        Purchase, PurchaseLineItem,
        form=PurchaseLineItemForm,
        extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            purchase = form.save(commit=False)
            purchase.purchased_by = request.user
            purchase.save()
            formset.instance = purchase
            line_items = formset.save(commit=False)

            for item in line_items:
                item.product.stock += item.quantity
                item.product.save()
                item.save()

            formset.save_m2m()
            messages.success(request, 'Purchase created and stock updated!')
            return redirect('purchase_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = PurchaseForm()
        formset = PurchaseLineItemFormSet()

    return render(request, 'invoicemgmt/purchase_form.html', {'form': form, 'formset': formset})

def purchase_summary(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    amount_in_words = num2words(purchase.total_amount, to='currency', lang='en', currency='AED')

    if request.GET.get('format') == 'pdf':
        html_string = render(request, 'purchases/purchase_summary.html', {
            'purchase': purchase,
            'amount_in_words': amount_in_words,
        }).content.decode('utf-8')

        with tempfile.NamedTemporaryFile(delete=True, suffix=".pdf") as output:
            HTML(string=html_string).write_pdf(target=output.name)
            output.seek(0)
            response = HttpResponse(output.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'filename=purchase_{purchase.id}.pdf'
            return response

    return render(request, 'purchases/purchase_summary.html', {
        'purchase': purchase,
        'amount_in_words': amount_in_words,
    })

@login_required
def purchase_pdf(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    html_string = render_to_string('invoicemgmt/purchase_pdf.html', {'purchase': purchase})
    html = HTML(string=html_string)
    pdf_file = html.write_pdf()
    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'filename=purchase_{purchase.pk}.pdf'
    return response

def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    purchase_count = Purchase.objects.count()
    return render(request, 'purchase_detail.html', {
        'purchase': purchase,
        'purchase_count': purchase_count,
    })

@login_required
def purchase_list(request):
    query = request.GET.get("q", "")
    purchases = Purchase.objects.all()

    if query:
        purchases = purchases.filter(
            Q(purchase_number__icontains=query) |
            Q(supplier__name__icontains=query)
        )

    return render(request, "invoicemgmt/purchase_list.html", {
        "purchases": purchases,
        "query": query,
    })

@permission_required('invoicemgmt.add_purchase', raise_exception=True)
@login_required
def purchase_create(request):
    PurchaseLineItemFormSet = inlineformset_factory(
        Purchase, PurchaseLineItem,
        form=PurchaseLineItemForm,
        extra=1, can_delete=True
    )

    if request.method == 'POST':
        form = PurchaseForm(request.POST)
        formset = PurchaseLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            purchase = form.save(commit=False)
            purchase.created_by = request.user
            formset.instance = purchase

            try:
                purchase.save()
                total_amount = 0
                line_items = formset.save(commit=False)

                for item in line_items:
                    product = item.product
                    quantity = item.quantity
                    price = item.price

                    item.amount = quantity * price
                    item.purchase = purchase
                    item.save()

                    total_amount += item.amount

                    # ✅ Increase stock
                    product.stock += quantity
                    product.save()

                purchase.total_amount = total_amount
                purchase.save()

                messages.success(request, '✅ Purchase recorded and stock updated.')
                return redirect('purchase_list')

            except Exception as e:
                messages.error(request, f"❌ Error saving purchase: {str(e)}")

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = PurchaseForm()
        formset = PurchaseLineItemFormSet()

    return render(request, 'invoicemgmt/purchase_form.html', {
        'form': form,
        'formset': formset,
        'document_type': 'purchase'
    })

from django.shortcuts import get_object_or_404, redirect

@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    purchase.delete()
    return redirect('purchase_list')

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required

@permission_required('invoicemgmt.change_purchase', raise_exception=True)
@login_required
def purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        if form.is_valid():
            form.save()
            return redirect('purchase_list')
    else:
        form = PurchaseForm(instance=purchase)
    return render(request, 'invoicemgmt/purchase_form.html', {'form': form, 'purchase': purchase})