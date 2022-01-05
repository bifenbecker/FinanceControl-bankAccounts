import pika
from django.conf import settings

credentials = pika.PlainCredentials(settings.RABBITMQ_USER, settings.RABBITMQ_PASSWORD)

params = pika.ConnectionParameters(settings.RABBITMQ_HOST, credentials=credentials)

connection = pika.BlockingConnection(params)

channel = connection.channel()


def logger(body, key='logger'):
    msg = f'Service: Bank Accounts - {body}'
    channel.basic_publish(exchange='',
                          routing_key=key,
                          body=msg)
