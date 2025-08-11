from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView 
from .views import InvoiceDeleteView, add_product, product_list,update_product,delete_product,register 

urlpatterns = [
    path('', views.home, name='home'),

    # Customer-related URLs
    path('customers/', views.customer_list, name='customer_list'),
    path('customers/create/', views.create_customer, name='create_customer'),
    path('customers/<int:pk>/', views.customer_detail, name='customer_detail'),
    path('customers/delete/<int:pk>/', views.delete_customer, name='delete_customer'),

    # Invoice-related URLs
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/create/', views.create_invoice, name='create_invoice'),  
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/mark_paid/', views.mark_invoice_paid, name='mark_invoice_paid'),
    path('invoices/<int:pk>/edit/', views.update_invoice, name='update_invoice'),
    path('invoices/<int:pk>/delete/', InvoiceDeleteView.as_view(), name='delete_invoice'),
    path('invoices/<int:pk>/pdf/', views.generate_invoice_pdf, name='generate_invoice_pdf'),
    path("import-invoices/", views.import_invoices_from_excel, name="import_invoices"),


    # Product-related URLs
    path('products/', product_list, name='product_list'),
    path('products/add/', add_product, name='add_product'),
    path('products/<int:pk>/edit/', views.update_product, name='product_update'),
    path('products/<int:pk>/restock/', views.restock_product, name='restock_product'),
    path('products/<int:pk>/delete/', views.delete_product, name='product_delete'),
    # path('products/purchase/', views.purchase_product, name='purchase_product'),
    path('purchases/create/', views.purchase_create, name='create_purchase'),
    path('purchases/<int:pk>/summary/', views.purchase_summary, name='purchase_summary'),
    path('purchases/', views.purchase_list, name='purchase_list'),
    path('purchases/create/', views.purchase_create, name='create_purchase'),
    path('purchases/<int:pk>/', views.purchase_detail, name='purchase_detail'),
    path('purchases/<int:pk>/delete/', views.purchase_delete, name='delete_purchase'),
    path('purchases/<int:pk>/update/', views.purchase_update, name='update_purchase'),
    path('purchases/<int:pk>/pdf/', views.purchase_pdf, name='purchase_pdf'),
    path('ai-support/', views.ai_support, name='ai_support'),

]


# Other
urlpatterns += [
    path('create_document/', views.select_document_type, name='select_document_type'),
    path('create_receipt/', views.create_receipt, name='create_receipt'),
    path('generate-recurring-invoices/', views.generate_recurring_invoices, name='generate_recurring_invoices'),
    path('invoice/<int:pk>/email/', views.email_invoice, name='email_invoice'),
    path('accounts/register/', register, name='register'),
    path('accounts/register/success/', TemplateView.as_view(
        template_name='registration/register_success.html'), name='registration_success'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('quotations/', views.quotation_list, name='quotation_list'),
    path('quotations/create/', views.create_quotation, name='create_quotation'),
    path('quotations/<int:pk>/send_email/', views.send_quotation_email, name='send_quotation_email'),
]
