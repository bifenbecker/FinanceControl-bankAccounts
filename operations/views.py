from rest_framework import status
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from utils import all_methods_get_payload, get_operation, get_bill, get_user_id_from_payload
from .models import Operation, CategoryToUser
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

        serializer = CategorySerializer(data={"name": request.data.get("name", ""), "isIncome": isIncome, "user_id": kwargs['user_id']})
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
class FilterOperationsView(APIView):

    # @get_user_id_from_payload
    def post(self, request, *args, **kwargs):
        # user_id = kwargs['user_id']
        user_id = 5
        category = request.data.get('category', None)
        date = request.data.get('date', None)
        isIncome = request.data.get('isIncome', None)
        value = request.data.get('value', None)

        operations = Operation.objects.filter(category__user_id=user_id).all()
        if category:
            operations = operations.filter(category=category)
        if date:
            operations = operations.filter(date=date)
        if isIncome:
            if not isinstance(isIncome, bool):
                return Response({
                    'msg': 'Incorrect value of "isIncome"'
                })
            operations = operations.filter(isIncome=isIncome)
        if value:
            if isinstance(value, str):
                if not value.isdigit():
                    return Response({
                        'msg': 'Incorrect value of "value"'
                    })
                value = float(value)
            operations = operations.filter(value=value)
        serializer = OperationSerializer(operations, many=True)
        return Response(
            serializer.data
        )

