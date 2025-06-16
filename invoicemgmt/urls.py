from django.urls import path
from . import views
from .views import InvoiceDeleteView, add_product, product_list,update_product,delete_product

urlpatterns = [
    path('', views.home, name='home'),

    # Customer-related URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/delete/<int:pk>/', views.delete_customer, name='delete_customer'),

    # Invoice-related URLs
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),  # ✅ Use this
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/mark_paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('invoices/<int:pk>/edit/', views.update_invoice, name='update_invoice'),
    path('invoices/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='delete_invoice'),
    path('invoices/<int:pk>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),

    # Product-related URLs
    path('products/', product_list, name='product_list'),
    path('products/add/', add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.update_product, name='product_update'),
    path('products/<int:pk>/restock/', views.restock_product, name='restock_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='product_delete'),


    # Other
    path('create_document/', views.select_document_type, name='select_document_type'),
    path('create_receipt/', views.create_receipt, name='create_receipt'),
    path('generate-recurring-invoices/', views.generate_recurring_invoices, name='generate_recurring_invoices'),
    path('invoice/<int:pk>/email/', views.email_invoice, name='email_invoice'),
    


]
