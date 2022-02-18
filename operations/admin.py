from django.contrib import admin

from .models import *


# Register your models here.
class CategoryToUserAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'name', 'isIncome')
    search_fields = ('user_id', 'name')


class OperationAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'category', 'description', 'date', 'isIncome', 'value', 'currency')
    search_fields = ('category', 'description', 'date', 'currency')


class OperationToBillAdmin(admin.ModelAdmin):
    list_display = ('operation', 'bill')
    search_fields = ('operation', 'bill')


admin.site.register(CategoryToUser, CategoryToUserAdmin)
admin.site.register(Operation, OperationAdmin)
admin.site.register(OperationToBill, OperationToBillAdmin)
