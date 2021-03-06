import decimal
import uuid as uuid
from typing import Optional

from django.db import models
from django.core.exceptions import ObjectDoesNotExist

from operations.models import Operation, OperationToBill, CategoryToUser, TransferOperation
from operations.serializers import OperationSerializer

from forex_python.converter import CurrencyRates
from forex_python.bitcoin import BtcConverter

from .utils import convert_value


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
        transfers_from = self.transfers_from.all()
        transfers_to = self.transfers_to.all()
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
        for transfer in transfers_from:
            start_balance -= transfer.value_from
        for transfer in transfers_to:
            start_balance += transfer.value_to
        self.balance = start_balance
        self.save()
        return self.balance

    def transfer(self, to_, value: Optional[float]):
        if isinstance(to_, Bill):
            converted_value = convert_value(value, self.currency, to_.currency)
            transfer_operation = TransferOperation.objects.create(
                value_from=value,
                value_to=converted_value,
                from_bill=self,
                to_bill=to_
            )
            self.update_balance()
            to_.update_balance()
        else:
            raise TypeError("Argument must be Bill")

    def add_operation(self, category: Optional[int], description: Optional[str] = "",
                      value: Optional[float] = 0.0, currency: Optional[str] = None,
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

        category_db = None
        if category:
            category_db = CategoryToUser.objects.filter(id=category).first()
            if not category_db:
                raise ObjectDoesNotExist("No such category")

        serializer_operation = OperationSerializer(data={
            'user_id': self.user_id,
            'description': description,
            'isIncome': isIncome,
            'value': value,
            'currency': currency
        })

        if serializer_operation.is_valid():
            operation = serializer_operation.save(category=category_db)
            operation_to_bill = OperationToBill.objects.create(
                operation=operation,
                bill=self
            )
            self.update_balance()
            return operation
        else:
            raise Exception("No valid data")
