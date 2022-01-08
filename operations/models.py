import uuid as uuid

from typing import Optional

from django.db import models


class CategoryToUser(models.Model):
    user_id = models.PositiveIntegerField(verbose_name="ID User", blank=False)
    isIncome = models.BooleanField(verbose_name="Is income type of category", default=True)
    name = models.CharField(max_length=50, verbose_name="Category name", blank=False)


class Operation(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    category = models.ForeignKey(CategoryToUser, on_delete=models.SET_NULL, related_name='operations',
                                 verbose_name='Category', blank=False, null=True)
    description = models.CharField(blank=True, default=None, null=True, max_length=255,
                                   verbose_name='Description of operation')
    date = models.DateField(auto_now_add=True)
    isIncome = models.BooleanField(default=True)
    value = models.DecimalField(default=0.0, max_digits=9, decimal_places=2, verbose_name="Value of operation",
                                blank=False)
    currency = models.CharField(max_length=3, default='USD')

    def is_search_text(self, text: Optional[str]) -> Optional[bool]:
        pass

class OperationToBill(models.Model):
    operation = models.OneToOneField(Operation, on_delete=models.CASCADE, related_name='to_bill',
                                     verbose_name="Operation",
                                     blank=False)
    bill = models.ForeignKey('bills.Bill', on_delete=models.PROTECT, related_name='operations',
                             verbose_name='Bill of operation',
                             blank=False)
