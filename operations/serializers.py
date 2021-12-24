from rest_framework import serializers

from .models import Operation, CategoryToUser


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryToUser
        exclude = ['user_id']


class OperationSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = Operation
        fields = '__all__'

    def to_representation(self, instance):
        ret = super(OperationSerializer, self).to_representation(instance=instance)
        bill = instance.to_bill.bill
        ret.update({'bill': {
            'name': bill.name,
            'balance': bill.balance
        }})
        return ret

