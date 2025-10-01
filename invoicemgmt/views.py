from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory
from .models import Customer, Invoice, InvoiceLineItem
from .forms import  InvoiceForm, InvoiceLineItemForm, CustomerForm
from django.db.models import Sum
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.generic import DeleteView
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.shortcuts import redirect
from .models import  Invoice, InvoiceLineItem
from datetime import date
from django.utils.timezone import now
from django.template.loader import get_template
from django.utils.timezone import now
from xhtml2pdf import pisa
from io import BytesIO
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
import os
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse
import json
from django.db.models.functions import TruncMonth
from datetime import datetime, timedelta
import pandas as pd
from django.core.files.storage import default_storage
from django.views.decorators.csrf import csrf_exempt
from .models import Invoice,  Customer
from .models import Purchase
from .forms import PurchaseForm
from django.db.models import Q

from .models import Purchase,PurchaseLineItem
from .forms import PurchaseForm, PurchaseLineItemForm
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .utils import send_mailjet_email


shop_name = "HIGH SPEED"

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
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)

    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)

    pdf_file.seek(0)

    customer_email = invoice.customer.email
    if customer_email:
        email_body = f"Dear {invoice.customer.name},\n\nPlease find attached your invoice #{invoice.pk}.\n\nThank you!"
        pdf_content = pdf_file.read()
        attachment = [{
            "ContentType": "application/pdf",
            "Filename": f"Invoice_{invoice.pk}.pdf",
            "Base64Content": base64.b64encode(pdf_content).decode('utf-8')
        }]
        status, response = send_mailjet_email(
            subject=f"Invoice #{invoice.pk} from Sherook Kalba",
            body=email_body,
            to_email=customer_email,
            attachments=attachment
        )

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

# @permission_required('invoicemgmt.view_invoice', raise_exception=True)
# @login_required
# def generate_recurring_invoices(request):
#     today = now().date()
#     recurring_list = RecurringInvoice.objects.filter(active=True, next_due_date__lte=today)

#     for recur in recurring_list:
#         # Generate new invoice
#         invoice = Invoice.objects.create(
#             customer=recur.customer,
#             invoice_date=today,
#             status='unpaid',
#             total_amount=recur.amount,
#         )
#         InvoiceLineItem.objects.create(
#             invoice=invoice,
#             product=recur.product,
#             quantity=1,
#             amount=recur.amount
#         )
#         # Set next due date
#         if recur.interval == 'monthly':
#             recur.next_due_date = today + timedelta(days=30)
#         elif recur.interval == 'weekly':
#             recur.next_due_date = today + timedelta(weeks=1)
#         recur.save()

#     return redirect('home')

class InvoiceDeleteView(PermissionRequiredMixin, DeleteView):
    model = Invoice
    template_name = 'invoicemgmt/confirm_delete_invoice.html'
    success_url = reverse_lazy('invoice_list')
    permission_required = 'invoicemgmt.delete_invoice'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        # for item in self.object.invoicelineitem_set.all():
        #     item.product.stock += item.quantity
        #     item.product.save()
        return super().delete(request, *args, **kwargs)

# from .models import Invoice, Product, Customer  # Make sure your models are imported
@login_required
def home(request):
    # if not request.user.is_staff:
    #     messages.warning(request, "Your account is pending approval.")
    #     return render(request, 'registration/pending_approval.html')
    
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
    # total_products = Product.objects.count()
    # low_stock_products = Product.objects.filter(stock__lt=5)

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
        # 'total_products': total_products,
        'total_customers': total_customers,
        'paid_bills': paid_bills,
        'recent_invoices': recent_invoices,
        # 'low_stock_products': low_stock_products,
        'chart_labels': json.dumps(month_labels),
        'chart_data': json.dumps(chart_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
    }

    return render(request, 'invoicemgmt/home.html', context)

# @permission_required('invoicemgmt.change_product', raise_exception=True)
# @login_required
# def update_product(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     if request.method == 'POST':
#         form = ProductForm(request.POST, instance=product)
#         if form.is_valid():
#             form.save()
#             return redirect('product_list')
#     else:
#         form = ProductForm(instance=product)
#     return render(request, 'invoicemgmt/product_form.html', {'form': form})


# @permission_required('invoicemgmt.change_product', raise_exception=True)
# @login_required
# def restock_product(request, pk):
#     product = get_object_or_404(Product, pk=pk)

#     if request.method == "POST":
#         quantity = int(request.POST.get("quantity", 0))
#         if quantity > 0:
#             product.stock += quantity
#             product.save()
#             messages.success(request, f"✅ Restocked {product.name} by {quantity} units.")
#         else:
#             messages.warning(request, "⚠️ Enter a valid quantity.")

#     return redirect('product_list')

# @permission_required('invoicemgmt.delete_product', raise_exception=True)
# @login_required
# def delete_product(request, pk):
#     product = get_object_or_404(Product, pk=pk)
#     product.delete()
#     messages.success(request, f"🗑️ Product '{product.name}' deleted successfully.")
#     return redirect('product_list')
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
        extra=6, can_delete=True
    )

    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        formset = InvoiceLineItemFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user  # Assign the invoice to the current user
            formset.instance = invoice

            try:
                invoice.save()  # Save the invoice

                total_amount = 0
                line_items = formset.save(commit=False)

                for item_form in line_items:
                    # Use unit_price directly instead of product.price
                    quantity = item_form.quantity
                    unit_price = item_form.unit_price  # Ensure this is provided
                    item_form.amount = quantity * unit_price
                    item_form.invoice = invoice
                    item_form.save()

                    total_amount += item_form.amount

                invoice.total_amount = total_amount
                invoice.save()

                messages.success(request, '✅ Invoice saved successfully.')
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
    
    if request.user.is_superuser:  
        invoices = Invoice.objects.all()
    else:
    
        invoices = Invoice.objects.filter(created_by=request.user)
    
   
    if query:
        invoices = invoices.filter(
            Q(customer__name__icontains=query) |
            Q(invoice_number__icontains=query)
        )
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


# @permission_required('invoicemgmt.add_product', raise_exception=True)
# @login_required
# def add_product(request):
#     if request.method == 'POST':
#         form = ProductForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return redirect('product_list')  # Optional: or to invoice creation
#     else:
#         form = ProductForm()
#     return render(request, 'invoicemgmt/add_products.html', {'form': form})

# @permission_required('invoicemgmt.view_product', raise_exception=True)
# @login_required
# def product_list(request):
#     products = Product.objects.all()
#     return render(request, 'invoicemgmt/product_list.html', {'products': products})

# @login_required
# def delete(self, request, *args, **kwargs):
#     self.object = self.get_object()
#     for item in self.object.invoicelineitem_set.all():
#         item.product.stock += item.quantity
#         item.product.save()
#     return super().delete(request, *args, **kwargs)

# @permission_required('invoicemgmt.view_invoice', raise_exception=True)
# @login_required
# def email_invoice(request, pk):
#     invoice = get_object_or_404(Invoice, pk=pk)

#     if not (request.user.is_superuser or invoice.created_by == request.user):
#         raise PermissionDenied("You do not have permission to email this invoice.")

#     customer_email = invoice.customer.email
#     if not customer_email:
#         messages.error(request, "Customer does not have an email address.")
#         return redirect('invoice_detail', pk=invoice.pk)

    
#     template = get_template('invoicemgmt/invoice_pdf.html')
#     html = template.render({'invoice': invoice, 'now': now()})
#     pdf_file = BytesIO()
#     pisa_status = pisa.CreatePDF(html, dest=pdf_file)
#     pdf_file.seek(0)

#     if pisa_status.err:
#         messages.error(request, "Error generating PDF.")
#         return redirect('invoice_detail', pk=invoice.pk)

   
#     email_body = render_to_string('invoicemgmt/email_invoice.html', {'invoice': invoice})

   
#     pdf_content = pdf_file.read()
#     attachment = [{
#         "ContentType": "application/pdf",
#         "Filename": f"Invoice_{invoice.pk}.pdf",
#         "Base64Content": base64.b64encode(pdf_content).decode('utf-8')
#     }]

#     status, response = send_mailjet_email(
#         subject=f"Invoice #{invoice.pk} from Sherook Kalba",
#         body=email_body,
#         to_email=customer_email,
#         attachments=attachment
#     )

#     print("Mailjet status:", status)
#     print("Mailjet response:", response)

#     if status == 200:
#         messages.success(request, "Invoice emailed to customer!")
#     else:
#         messages.error(request, f"Error sending email: {response}")

#     return redirect('invoice_detail', pk=invoice.pk)
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
    response['Content-Disposition'] = f'filename=purchase_{purchase.purchase_number}.pdf'
    return response

@login_required
def purchase_list(request):
    query = request.GET.get("q", "")
    purchases = Purchase.objects.all()
    if query:
        purchases = purchases.filter(
            Q(purchase_number__icontains=query) |
            Q(supplier_name__icontains=query)
        )
    return render(request, "invoicemgmt/purchase_list.html", {
        "purchases": purchases,
        "query": query,
    })

@login_required
def purchase_detail(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    purchase_count = Purchase.objects.count()
    return render(request, 'invoicemgmt/purchase_detail.html', {
        'purchase': purchase,
        'purchase_count': purchase_count,
    })

@login_required
def purchase_pdf(request, pk):
    from num2words import num2words
    purchase = get_object_or_404(Purchase, pk=pk)
    amount_in_words = num2words(purchase.total_amount, lang='en') + ' AED' if hasattr(purchase, 'total_amount') else ''
    template = get_template('invoicemgmt/purchase_pdf.html')
    html = template.render({'purchase': purchase, 'amount_in_words': amount_in_words})
    pdf_file = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=pdf_file)
    if pisa_status.err:
        return HttpResponse('PDF generation failed', status=500)
    pdf_file.seek(0)
    response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Purchase_{purchase.pk}.pdf"'
    return response

@permission_required('invoicemgmt.add_purchase', raise_exception=True)
@login_required
def purchase_create(request):
    PurchaseLineItemFormSet = inlineformset_factory(
        Purchase, PurchaseLineItem,
        form=PurchaseLineItemForm,
        extra=1, can_delete=True
    )
    if request.method == 'POST':
        purchase_form = PurchaseForm(request.POST)
        formset = PurchaseLineItemFormSet(request.POST)
        if purchase_form.is_valid() and formset.is_valid():
            purchase = purchase_form.save(commit=False)
            purchase.created_by = request.user
            purchase.save()
            formset.instance = purchase
            formset.save()
            purchase.save()  # <-- Add this line to update totals!
            # Update stock for each product
            # for item in purchase.line_items.all():
            #     item.product.stock += item.quantity
            #     item.product.save()
            messages.success(request, '✅ Purchase recorded and stock updated.')
            return redirect('purchase_list')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        purchase_form = PurchaseForm()
        formset = PurchaseLineItemFormSet()
    return render(request, 'invoicemgmt/purchase_form.html', {
        'purchase_form': purchase_form,
        'formset': formset,
        'document_type': 'purchase'
    })

@login_required
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if request.method == "POST":
        purchase.delete()
        messages.success(request, "Purchase deleted successfully.")
        return redirect('purchase_list')
    return render(request, 'invoicemgmt/confirm_delete_purchase.html', {'purchase': purchase})

@permission_required('invoicemgmt.change_purchase', raise_exception=True)
@login_required
def purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    PurchaseLineItemFormSet = inlineformset_factory(
        Purchase, PurchaseLineItem,
        form=PurchaseLineItemForm,
        extra=0, can_delete=True
    )
    if request.method == 'POST':
        form = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseLineItemFormSet(request.POST, instance=purchase)
        if form.is_valid() and formset.is_valid():
           
            # for old_item in purchase.line_items.all():
            #     old_item.product.stock -= old_item.quantity
            #     old_item.product.save()
            # form.save()
            # formset.save()
            
            # for new_item in purchase.line_items.all():
            #     new_item.product.stock += new_item.quantity
            #     new_item.product.save()
            messages.success(request, "Purchase updated successfully.")
            return redirect('purchase_detail', pk=purchase.pk)
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = PurchaseForm(instance=purchase)
        formset = PurchaseLineItemFormSet(instance=purchase)
    return render(request, 'invoicemgmt/purchase_form.html', {
        'form': form,
        'formset': formset,
        'purchase': purchase,
        'document_type': 'purchase'
    })

from django.forms import inlineformset_factory

# @login_required
# def quotation_list(request):
#     quotations = Quotation.objects.all()
#     return render(request, 'invoicemgmt/quotation_list.html', {'quotations': quotations})

# @login_required
# def create_quotation(request):
#     QuotationLineItemFormSet = inlineformset_factory(
#         Quotation, QuotationLineItem,
#         form=QuotationLineItemForm,
#         extra=1, can_delete=True
#     )
#     if request.method == 'POST':
#         form = QuotationForm(request.POST)
#         formset = QuotationLineItemFormSet(request.POST)
#         if form.is_valid() and formset.is_valid():
#             quotation = form.save()
#             formset.instance = quotation
#             total_amount = 0
#             for item in formset.save(commit=False):
#                 item.amount = item.quantity * item.price
#                 item.save()
#                 total_amount += item.amount
#             quotation.total_amount = total_amount
#             quotation.save()
#             messages.success(request, "Quotation created!")
#             return redirect('quotation_list')
#     else:
#         form = QuotationForm()
#         formset = QuotationLineItemFormSet()
#     return render(request, 'invoicemgmt/quotation_form.html', {'form': form, 'formset': formset})

# @login_required
# def send_quotation_email(request, pk):
#     quotation = get_object_or_404(Quotation, pk=pk)
    
#     html = render_to_string('invoicemgmt/quotation_pdf.html', {'quotation': quotation})
#     pdf_file = BytesIO()
#     pisa.CreatePDF(html, dest=pdf_file)
#     pdf_file.seek(0)

#     email_body = render_to_string('invoicemgmt/quotation_email.html', {'quotation': quotation})

#     email = EmailMessage(
#         subject=f"Quotation from {quotation.company_name}",
#         body=email_body,
#         to=[quotation.customer.email]
#     )
#     email.content_subtype = "html"  # Send as HTML email
#     email.attach('quotation.pdf', pdf_file.read(), 'application/pdf')
#     email.send()
#     quotation.email_sent = True
#     quotation.save()
#     messages.success(request, "Quotation sent to client!")
#     return redirect('quotation_list')

@login_required
def ai_support(request):
    # Define features and their explanations
    features = {
        "invoicing": {
            "title": "Invoicing System",
            "description": "Create, manage and track invoices. Features include:",
            "capabilities": [
                "Create new invoices with multiple line items",
                "Track payment status (paid, unpaid, open)",
                "Generate PDF invoices",
                "Email invoices to customers",
                "View invoice history"
            ]
        },
        "inventory": {
            "title": "Inventory Management",
            "description": "Track and manage your product inventory. Features include:",
            "capabilities": [
                "Add and manage products",
                "Track stock levels",
                "Get low stock alerts",
                "Update product prices",
                "View product history"
            ]
        },
        "customers": {
            "title": "Customer Management",
            "description": "Manage your customer database. Features include:",
            "capabilities": [
                "Add new customers",
                "Track customer purchase history",
                "Manage customer contact information",
                "View customer statements",
                "Customer-specific pricing"
            ]
        },
        "purchases": {
            "title": "Purchase Management",
            "description": "Track purchases and suppliers. Features include:",
            "capabilities": [
                "Create purchase orders",
                "Track supplier deliveries",
                "Manage supplier information",
                "Track purchase history",
                "Automatic stock updates"
            ]
        },
        "quotations": {
            "title": "Quotation System",
            "description": "Create and manage quotations. Features include:",
            "capabilities": [
                "Create professional quotations",
                "Convert quotations to invoices",
                "Email quotations to customers",
                "Track quotation status",
                "Quotation history"
            ]
        }
    }

    # Handle user query
    query = request.GET.get('q', '').lower()
    response = None

    if query:
        # Search through features
        for feature, info in features.items():
            if query in feature.lower() or query in info['description'].lower():
                response = info
                break
        
        if not response:
            response = {
                "title": "Need Help?",
                "description": "I couldn't find an exact match. Here are our main features:",
                "capabilities": [f"- {feature.title()}" for feature in features.keys()]
            }

    return render(request, 'invoicemgmt/ai_support.html', {
        'features': features,
        'response': response,
        'query': query
    })

import pandas as pd
from django.http import HttpResponse

@permission_required('invoicemgmt.view_invoice', raise_exception=True)
@login_required
def export_invoices_to_excel(request):
    # Match invoice_list filtering
    query = request.GET.get('q')
    if request.user.is_superuser:
        invoices = Invoice.objects.all()
    else:
        invoices = Invoice.objects.filter(created_by=request.user)

    if query:
        invoices = invoices.filter(
            Q(customer__name__icontains=query) |
            Q(invoice_number__icontains=query)
        )

    data = []
    for invoice in invoices:
        for item in invoice.line_items.all():
            data.append({
                "Invoice Number": invoice.invoice_number,
                "Customer": invoice.customer.name,
                "Date": invoice.invoice_date.strftime('%Y-%m-%d') if invoice.invoice_date else "",
                "Product": item.product.name if item.product else item.description,
                "Quantity": item.quantity,
                "Unit Price": item.unit_price,
                "Amount": item.amount,
                "Status": invoice.status,
            })

    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="invoices.xlsx"'
    df.to_excel(response, index=False)
    return response

from django.http import HttpResponse
from django.core.mail import EmailMessage

@login_required
def test_email(request):
    try:
        status, response = send_mailjet_email(
            subject='Test Subject',
            body='Test body',
            to_email='your_other_email@gmail.com'  
        )
        if status == 200:
            return HttpResponse("Email sent!")
        else:
            return HttpResponse(f"EMAIL ERROR: {response}")
    except Exception as e:
        return HttpResponse(f"EMAIL ERROR: {e}")

# @login_required
# def quotation_detail(request, pk):
#     quotation = get_object_or_404(Quotation, pk=pk)
#     line_items = quotation.line_items.all()
#     subtotal = sum(item.amount for item in line_items)
#     sales_tax = sum(item.vat_amount for item in line_items)
#     total = subtotal + sales_tax
#     return render(request, 'invoicemgmt/quotation_detail.html', {
#         'quotation': quotation,
#         'subtotal': subtotal,
#         'sales_tax': sales_tax,
#         'total': total,
#     })

# @login_required
# def edit_quotation(request, pk):
#     quotation = get_object_or_404(Quotation, pk=pk)
#     if request.method == 'POST':
#         form = QuotationForm(request.POST, instance=quotation)
#         if form.is_valid():
#             form.save()
#             return redirect('quotation_detail', pk=quotation.pk)
#     else:
#         form = QuotationForm(instance=quotation)
#     return render(request, 'invoicemgmt/quotation_form.html', {'form': form, 'quotation': quotation})

# @login_required
# def create_delivery_note(request):
#     if request.method == 'POST':
#         form = DeliveryNoteForm(request.POST)
#         formset = DeliveryNoteLineItemFormSet(request.POST)
#         if form.is_valid() and formset.is_valid():
#             note = form.save()
#             formset.instance = note
#             formset.save()
#             return redirect('delivery_note_detail', pk=note.pk)
#     else:
#         form = DeliveryNoteForm()
#         formset = DeliveryNoteLineItemFormSet()
#     return render(request, 'invoicemgmt/delivery_note_form.html', {'form': form, 'formset': formset})


# from .models import DeliveryNote
# from .forms import DeliveryNoteForm,DeliveryNoteLineItemFormSet
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import render, get_object_or_404, redirect

# @login_required
# def delivery_note_list(request):
#     notes = DeliveryNote.objects.all()
#     return render(request, 'invoicemgmt/delivery_note_list.html', {'notes': notes})

# @login_required
# def create_delivery_note(request):
#     if request.method == 'POST':
#         form = DeliveryNoteForm(request.POST)
#         formset = DeliveryNoteLineItemFormSet(request.POST)
#         if form.is_valid() and formset.is_valid():
#             note = form.save()
#             formset.instance = note
#             formset.save()
#             return redirect('delivery_note_detail', pk=note.pk)
#     else:
#         form = DeliveryNoteForm()
#         formset = DeliveryNoteLineItemFormSet()
#     return render(request, 'invoicemgmt/delivery_note_form.html', {'form': form, 'formset': formset})

# @login_required
# def delivery_note_detail(request, pk):
#     note = get_object_or_404(DeliveryNote, pk=pk)
#     return render(request, 'invoicemgmt/delivery_note.html', {'note': note})


# from django.http import HttpResponse
# from django.template.loader import get_template


# @login_required
# def delivery_note_pdf(request, pk):
#     note = get_object_or_404(DeliveryNote, pk=pk)
#     template = get_template('invoicemgmt/delivery_note_pdf.html')
#     html = template.render({'note': note})
#     pdf_file = BytesIO()
#     pisa_status = pisa.CreatePDF(html, dest=pdf_file)
#     if pisa_status.err:
#         return HttpResponse('PDF generation failed', status=500)
#     pdf_file.seek(0)
#     response = HttpResponse(pdf_file.getvalue(), content_type='application/pdf')
#     response['Content-Disposition'] = f'attachment; filename="delivery_note_{note.pk}.pdf"'
#     return response