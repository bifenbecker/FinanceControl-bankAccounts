import uuid as uuid
from typing import Optional, Union

from django.db import models

from operations.models import Operation, OperationToBill, CategoryToUser
from operations.serializers import OperationSerializer

from forex_python.converter import CurrencyRates
from forex_python.bitcoin import BtcConverter


class Bill(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user_id = models.PositiveIntegerField(blank=False, verbose_name="ID User")
    name = models.CharField(max_length=64, blank=False, verbose_name="Name of bill")
    balance = models.DecimalField(default=0.0, max_digits=9, decimal_places=2, verbose_name="Current balance")
    start_balance = models.DecimalField(editable=False, default=0.0, max_digits=9, decimal_places=2,
                                        verbose_name="Start balance")

    currency = models.CharField(max_length=3, default='USD')

    def update_balance(self):
        operations = [operation_to_bill.operation for operation_to_bill in self.operations.all()]
        start_balance = self.start_balance
        for operation in operations:
            converter = CurrencyRates()
            converter_btc = BtcConverter()

            if self.currency == operation.currency:
                converted_value = operation.value
            elif self.currency == 'BTC':
                converted_value = converter_btc.convert_to_btc(operation.value, operation.currency)
            elif operation.currency == 'BTC':
                converted_value = converter_btc.convert_to_btc(operation.value, self.currency)
            else:
                converted_value = converter.convert(operation.currency, self.currency, operation.value)

            if operation.isIncome:
                start_balance += converted_value
            else:
                start_balance -= converted_value
        self.balance = start_balance
        self.save()
        return self.balance

    def add_operation(self, category: Union[int, None], description: Optional[str] = "",
                      value: Optional[float] = 0.0, currency: Union[str, None] = None,
                      isIncome: Optional[bool] = True) -> Optional[Operation]:
        """
            Valiadte data and create operation
            :param user_id: ID user
            :param bill_uuid: UUID bill
            :param category: Category of operation
            :param description: Description
            :param value: Value
            :param isIncome:
            :return: Operation
            """
        print("ADD: ", currency)
        if category:
            Category = CategoryToUser.objects.filter(id=category).first()
            if not Category:
                raise Exception("No such category")
        else:
            Category = None

        serializer_operation = OperationSerializer(data={
            'user_id': self.user_id,
            'description': description,
            'isIncome': isIncome,
            'value': value,
            'currency': currency
        })
        serializer_operation.is_valid(raise_exception=True)
        if serializer_operation.is_valid():
            operation = serializer_operation.save(category=Category)
            operation_to_bill = OperationToBill.objects.create(
                operation=operation,
                bill=self
            )
            self.update_balance()
            return operation
        else:
            raise Exception("No valid data")
