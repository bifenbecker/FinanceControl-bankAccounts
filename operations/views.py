from typing import Optional

from django.conf import settings
from django.db.models import Q

from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from bills.models import Bill
from exceptions import ValidateException, ConvertDateException
from utils import all_methods_get_payload, get_operation, get_bill, get_user_id_from_payload, convert_date
from .models import Operation, CategoryToUser, OperationToBill
from .serializers import OperationSerializer, CategorySerializer


@all_methods_get_payload(viewsets.ViewSet)
class OperationViewSet:
    @get_user_id_from_payload
    def list(self, request, *args, **kwargs):
        operations = Operation.objects.filter(category__user_id=kwargs['user_id']).all()
        serializer = OperationSerializer(operations, many=True)
        return serializer.data, status.HTTP_200_OK, None

    @get_operation
    def retrieve(self, request, *args, **kwargs):
        serializer = OperationSerializer(instance=kwargs['operation'])
        return serializer.data, status.HTTP_200_OK, None

    @get_operation
    def update(self, request, *args, **kwargs):
        operation = kwargs['operation']
        bill = operation.to_bill.bill
        prev_operation = OperationSerializer(instance=operation)
        new_data = prev_operation.data
        new_data.update(request.data)
        serializer = OperationSerializer(instance=operation, data=new_data)
        if not serializer.is_valid():
            return {
                       'msg': 'Not valid data'
                   }, status.HTTP_400_BAD_REQUEST, f'Update operation error. Not valid data(4)'
        serializer.save()
        bill.update_balance()
        return serializer.data, status.HTTP_200_OK, f'Operation was updated'

    @get_operation
    def destroy(self, request, *args, **kwargs):
        # todo: Bad deleting
        operation = kwargs['operation']
        operation.delete()
        bill = operation.to_bill.bill
        bill.update_balance()

        return {
                   'msg': 'Operation was deleted'
               }, status.HTTP_200_OK, None

    @get_bill
    def create(self, request, *args, **kwargs):
        bill = kwargs['bill']
        print(kwargs['decoded_payload']['settings']['currency'])
        try:
            operation = bill.add_operation(**request.data, currency=kwargs['decoded_payload']['settings']['currency'])
        except Exception as e:
            return str(e), status.HTTP_400_BAD_REQUEST, None
        serializer = OperationSerializer(instance=operation)
        return serializer.data, status.HTTP_200_OK, f'Operation was added - Operation:{operation.id} to Bill: {bill.id}'


@all_methods_get_payload(viewsets.ViewSet)
class CategoryListView:
    @get_user_id_from_payload
    def list(self, request, *args, **kwargs):
        categories = CategoryToUser.objects.filter(user_id=kwargs['user_id'])
        serializer = CategorySerializer(categories, many=True)
        return serializer.data, status.HTTP_200_OK, None


@all_methods_get_payload(viewsets.ViewSet)
class CategoryView:
    @get_user_id_from_payload
    def create(self, request, *args, **kwargs):
        isIncome = request.data.get('isIncome', True)

        serializer = CategorySerializer(
            data={"name": request.data.get("name", ""), "isIncome": isIncome, "user_id": kwargs['user_id']})
        if serializer.is_valid(raise_exception=False):
            category = serializer.save(user_id=kwargs['user_id'])
            return serializer.data, status.HTTP_200_OK, f'Category was added - Name: {category.name} to User: {kwargs["user_id"]}'
        else:
            return "Not valid data", status.HTTP_400_BAD_REQUEST, f'Added category was error. Not valid data(5)'


@all_methods_get_payload(APIView)
class ListOperationsOfBill:
    @get_bill
    def get(self, request, *args, **kwargs):
        bill = kwargs['bill']
        bill.update_balance()
        operations = [operation_to_bill.operation for operation_to_bill in bill.operations.all()]
        serializer = OperationSerializer(operations, many=True)
        return serializer.data, status.HTTP_200_OK, None


# @all_methods_get_payload(APIView)
class SearchView(APIView):
    """
    API view searching operations or bills
    :param text
    """

    def post(self, request, **kwargs):
        # user_id = kwargs['user_id']
        user_id = 1
        try:
            search_text = request.data.get('text')
        except KeyError:
            # return "Must bet a 'text' param", status.HTTP_400_BAD_REQUEST, None
            return Response(
                data={
                    'msg': 'Must bet a "text" param'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        if isinstance(search_text, str):
            bills = Bill.objects.filter(user_id=user_id).all()
            operations_ids = []
            for bill in bills:
                operations_ids += [operation.operation.id for operation in bill.operations.all()]

            operations = Operation.objects.filter(id__in=operations_ids)
            operations = operations.filter(
                Q(category__name__icontains=search_text) | Q(description__icontains=search_text) | Q(
                    value__icontains=search_text) | Q(currency__icontains=search_text) | Q(
                    to_bill__bill__name__icontains=search_text) | Q(to_bill__bill__balance__icontains=search_text) | Q(
                    date__icontains=search_text))
            serializer = OperationSerializer(operations, many=True)
            return Response(
                serializer.data
            )
        else:
            # return "Text must be a string", status.HTTP_400_BAD_REQUEST, None
            return Response(
                {
                    'msg': 'Text must be a strings'
                },
                status=status.HTTP_400_BAD_REQUEST
            )


# @all_methods_get_payload(APIView)
class FilterOperationsView(APIView):
    """
    API view filtering list of operations
    :param {
    categories: [],
    date: str, int, - format DD.MM.YYYY HH:MM:SS
    isIncome: bool, str,
    value: {
            value: str, float, int,
            icc: bool, str,
                },
    bill: str,
    currencies: []
            }
    """

    # @get_user_id_from_payload
    def post(self, request, *args, **kwargs):
        # user_id = kwargs['user_id']
        self.user_id = 5
        self.categories = request.data.get('category', None)
        self.date = request.data.get('date', None)
        self.isIncome = request.data.get('isIncome', None)
        self.value_dict = request.data.get('value', None)
        self.bill = request.data.get('bill', None)  # todo Make filter bill
        self.currencies = request.data.get('currencies', None)
        self.description = request.data.get('description', None)

        try:
            self.validate(raise_exception=True)
        except ValidateException as e:
            msg = str(e)
            value = msg.split("|")[0]
            error = msg.split("|")[-1]
            return Response({
                'msg': f"Incorrect value of {value} - {error}"
            }, status.HTTP_400_BAD_REQUEST)

        operations = Operation.objects.filter(category__user_id=self.user_id).all()
        operations = self.filter_operations(operations)
        serializer = OperationSerializer(operations, many=True)
        return Response(
            serializer.data
        )

    def filter_operations(self, operations):

        if self.isIncome:
            operations = operations.filter(isIncome=self.isIncome)
        if self.categories:
            operations = operations.filter(category__in=self.categories)
        if self.date:
            operations = operations.filter(date__gte=self.date)
        if self.value_dict and self.value:
            operations = operations.filter(value__gte=self.value) if self.icc else operations.filter(
                value__lte=self.value)
        if self.currencies:
            operations = operations.filter(currency__in=self.currencies)

        if self.description:
            operations = operations.filter(description__search=self.description)

        return operations

    def validate(self, raise_exception=False) -> Optional[bool]:

        def _return_result(msg: Optional[str]):
            if raise_exception:
                raise ValidateException(msg)
            else:
                return False

        if not self.categories and not self.date and not self.isIncome and not self.value_dict and not self.currencies \
                and not self.description:
            _return_result("Data|Empty data or incorrect name of params")

        if self.description:
            if not isinstance(self.description, str):
                _return_result("Description|Description must be a string")

        if self.currencies:
            if isinstance(self.currencies, list):
                available_currencies = [cur[0] for cur in settings.CURRENCY_CHOICES]
                for cur in self.currencies:
                    if cur.upper() not in available_currencies:
                        _return_result(f"Currencies|Currency - {cur} is not available")
                    else:
                        self.currencies[self.currencies.index(cur)] = cur.upper()
            else:
                _return_result("Currencies|Currencies must be a list")

        if self.isIncome:
            if isinstance(self.isIncome, str):
                if self.isIncome in ['True', 'true']:
                    self.isIncome = True
                elif self.isIncome in ['False', 'false']:
                    self.isIncome = False
                else:
                    _return_result(f"isIncome|{self.isIncome}")

            if not isinstance(self.isIncome, bool):
                _return_result(f"isIncome|{self.isIncome}")

        if self.categories:
            if isinstance(self.categories, list):

                if self.isIncome:
                    self.categories = CategoryToUser.objects.filter(name__in=self.categories, isIncome=self.isIncome)
                else:
                    self.categories = CategoryToUser.objects.filter(name__in=self.categories)

            else:
                _return_result("Category|Category must be a list")

        if self.date:
            try:
                self.date = convert_date(self.date)
            except ConvertDateException as e:
                _return_result(f"Date|{str(e)}")

        if self.value_dict:
            if not isinstance(self.value_dict, dict):
                _return_result("Value|Value must be a dictionary")
            if 'value' not in self.value_dict and 'icc' not in self.value_dict:
                _return_result("Value|Key 'value' or 'icc' not in dictionary")

            self.icc = self.value_dict['icc']
            self.value = self.value_dict['value']
            if isinstance(self.icc, str):
                if self.icc in ["True", 'true']:
                    self.icc = True
                elif self.icc in ["False", "false"]:
                    self.icc = False
                else:
                    _return_result("Value|Key 'icc' must be a boolean")
            elif not isinstance(self.icc, bool):
                _return_result("Value|Key 'icc' must be a boolean")
            if isinstance(self.value, str) and self.value.isdigit():
                self.value = float(self.value)
            elif isinstance(self.value, float) or isinstance(self.value, int):
                pass
            else:
                _return_result("Value|Incorrect type of value")

        if self.bill:
            if isinstance(self.bill, str):
                name = self.bill
                self.bill = Bill.objects.filter(name=name, user_id=self.user_id).first()
                if not self.bill:
                    _return_result(f"Bill|No such bill name - {name}")
            else:
                _return_result("Bill|Incorrect type of bill")

        return True
