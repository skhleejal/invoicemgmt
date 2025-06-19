from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from invoicemgmt import views


urlpatterns = [
    path('accounts/', include('registration.backends.default.urls')), 
    path('admin/', admin.site.urls),
    path('', include('invoicemgmt.urls')),  # Include the URLs from your app
   
     

]