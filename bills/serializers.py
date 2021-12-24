from rest_framework import serializers

from .models import Bill


class BillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bill
        exclude = ['user_id']


    def update(self, instance, validated_data):
        user_id = validated_data.get('user_id')
        name = validated_data.get('name', instance.name)
        balance = validated_data.get('balance', instance.balance)

        if instance.user_id != user_id:
            raise serializers.ValidationError('Incorrect user id')

        if len(Bill.objects.filter(user_id=user_id, name=name).exclude(uuid=instance.uuid)) >= 1:
            raise serializers.ValidationError('Name must be unique')

        if balance < 0:
            raise serializers.ValidationError('Balance must be positive')

        instance.name = name
        instance.balance = balance
        instance.save()
        return instance


    def create(self, validated_data):
        user_id = validated_data.get('user_id')
        name = validated_data.get('name')
        validated_data.update({'start_balance': validated_data.get('balance')})


        if len(Bill.objects.filter(user_id=user_id, name=name)) >= 1:
            raise serializers.ValidationError('Name must be unique')

        instance = Bill(**validated_data)
        instance.save()
        return instance
