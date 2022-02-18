from rest_framework import status
from rest_framework import viewsets
from rest_framework import serializers

from .models import Bill
from .serializers import BillSerializer
from utils import all_methods_get_payload, get_bill, get_user_id_from_payload


@all_methods_get_payload(viewsets.ViewSet)
class BillViewSet:

    @get_user_id_from_payload
    def list(self, request, **kwargs):
        """
        List banks
        """

        user_bills = Bill.objects.filter(user_id=kwargs['user_id']).all()
        serializer = BillSerializer(user_bills, many=True)
        return serializer.data, status.HTTP_200_OK, None

    @get_bill
    def retrieve(self, request, **kwargs):
        """
        Get bank
        """
        serializer = BillSerializer(kwargs['bill'])
        return serializer.data, status.HTTP_200_OK, None

    @get_bill
    def update(self, request, **kwargs):
        """
        Update bank
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
        Delete bank
        """
        bill = kwargs['bill']
        for operation_to_bank in bill.operations.all():
            operation_to_bank.delete()
        bill.delete()
        return {'msg': 'Bank was deleted'}, status.HTTP_202_ACCEPTED, f'Bank - {bill.id} was deleted'

    @get_user_id_from_payload
    def create(self, request, **kwargs):
        """
        Create bank
        """
        bill_data = request.data
        bill_data.update({'user_id': kwargs['user_id'], 'currency': kwargs['decoded_payload']['settings']['currency']})
        serialiser = BillSerializer(data=bill_data)
        serialiser.is_valid(raise_exception=True)
        bill = serialiser.save(user_id=kwargs['user_id'])
        return serialiser.data, status.HTTP_202_ACCEPTED, f'Create bill - {bill.id} User: {kwargs["user_id"]}'



