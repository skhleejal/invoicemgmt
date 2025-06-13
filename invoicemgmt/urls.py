from django.urls import path
from . import views
from .views import InvoiceDeleteView

urlpatterns = [
    path('', views.home, name='home'),  # e.g., Home page for your app
    path('customers/', views.customer_list, name='customer_list'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('invoices/<int:pk>/mark_paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('invoice/<int:pk>/edit/', views.update_invoice, name='update_invoice'),
    path('customers/delete/<int:pk>/', views.delete_customer, name='delete_customer'),
    path('invoices/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='delete_invoice'),
    path('create_document/', views.select_document_type, name='select_document_type'),
    path('create_invoice/', views.create_invoice, name='create_invoice'),
    path('create_receipt/', views.create_receipt, name='create_receipt'), 

]