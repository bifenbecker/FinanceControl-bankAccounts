import os

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
                  path(f'{os.environ.get("SERVICE_NAME", "bankAccounts")}/admin', admin.site.urls),
                  path(f'{os.environ.get("SERVICE_NAME", "bankAccounts")}/bills/api/', include('bills.urls')),
                  path(f'{os.environ.get("SERVICE_NAME", "bankAccounts")}/operations/api/', include('operations.urls')),

              ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)