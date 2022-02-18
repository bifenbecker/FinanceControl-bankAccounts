from django.contrib import admin

from .models import *


# Register your models here.
class BillAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'user_id', 'name', 'balance', 'start_balance', 'currency')
    search_fields = ('user_id', 'uuid', 'name', 'balance', 'currency')


admin.site.register(Bill, BillAdmin)
