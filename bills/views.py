from rest_framework import status
from rest_framework import viewsets
from rest_framework import serializers

from .models import Bill
from .serializers import BillSerializer
from utils import all_methods_get_payload, get_bill, get_user_id_from_payload
from .utils import convert_value


@all_methods_get_payload(viewsets.ViewSet)
class BillViewSet:

    @get_user_id_from_payload
    def list(self, request, **kwargs):
        """
        List bills
        """

        user_bills = Bill.objects.filter(user_id=kwargs['user_id']).all()
        serializer = BillSerializer(user_bills, many=True)
        return serializer.data, status.HTTP_200_OK, None

    @get_bill
    def retrieve(self, request, **kwargs):
        """
        Get bill
        """
        serializer = BillSerializer(kwargs['bill'])
        return serializer.data, status.HTTP_200_OK, None

    @get_bill
    def update(self, request, **kwargs):
        """
        Update bill
        """
        new_bill_data = request.data
        new_bill_data['user_id'] = kwargs['user_id']
        bill = kwargs['bill']
        serializer = BillSerializer(instance=bill)
        try:
            serializer.update(bill, new_bill_data)
        except serializers.ValidationError as e:
            return f'Error. No update bill - ({str(e)})', status.HTTP_400_BAD_REQUEST, f'Bill - {bill.id} was not updated'
        return serializer.data, status.HTTP_202_ACCEPTED, f'Bill - {bill.id} was updated'

    @get_bill
    def destroy(self, request, **kwargs):
        """
        Delete bill
        """
        bill = kwargs['bill']
        for operation_to_bank in bill.operations.all():
            operation_to_bank.delete()
        bill.delete()
        return {'msg': 'Bank was deleted'}, status.HTTP_202_ACCEPTED, f'Bank - {bill.id} was deleted'

    @get_user_id_from_payload
    def create(self, request, **kwargs):
        """
        Create bill
        """
        bill_data = request.data
        bill_data.update({'user_id': kwargs['user_id'], 'currency': kwargs['decoded_payload']['settings']['currency']})
        serialiser = BillSerializer(data=bill_data)
        serialiser.is_valid(raise_exception=True)
        bill = serialiser.save(user_id=kwargs['user_id'])
        return serialiser.data, status.HTTP_202_ACCEPTED, f'Create bill - {bill.id} User: {kwargs["user_id"]}'

    def transfer(self, request, **kwargs):
        decoded_payload = kwargs['decoded_payload']
        user_id = decoded_payload['id']
        if 'from_bill' not in request.data or 'to_bill' not in request.data or 'value' not in request.data:
            return 'Empty data', status.HTTP_400_BAD_REQUEST, None

        from_bill = request.data.pop('from_bill')
        to_bill = request.data.pop('to_bill')
        value = request.data.pop('value')


        from_ = Bill.objects.filter(uuid=from_bill).first()
        to_ = Bill.objects.filter(uuid=to_bill).first()
        if isinstance(value, str) and value.isdigit():
            value = float(value)
        elif isinstance(value, float) or isinstance(value, int):
            pass
        else:
            return 'Value must be a float', status.HTTP_400_BAD_REQUEST, None

        if value < 0:
            return 'Value must be positive', status.HTTP_400_BAD_REQUEST, None

        if from_.user_id == user_id and to_.user_id == user_id:
            if from_ and to_:
                try:
                    converted_value = convert_value(value, decoded_payload['settings']['currency'], from_.currency)
                    from_.transfer(to_, converted_value)
                except TypeError as e:
                    return str(e), status.HTTP_400_BAD_REQUEST, str(e)
                except Exception as e:
                    return str(e), status.HTTP_400_BAD_REQUEST, str(e)

                serializer = BillSerializer([from_, to_], many=True)
                return serializer.data, status.HTTP_200_OK, f'Transfer {value} from {from_.uuid} to {to_.uuid}'
            else:
                return 'No such bills', status.HTTP_400_BAD_REQUEST, None
        else:
            return 'You don not have such bills', status.HTTP_400_BAD_REQUEST, None


