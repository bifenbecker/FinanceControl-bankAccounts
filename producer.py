import os
import pika

credentials = pika.PlainCredentials('admin', 'admin')

params = pika.ConnectionParameters(os.environ.get('RABBITMQ_HOST', 'localhost'), credentials=credentials)

connection = pika.BlockingConnection(params)

channel = connection.channel()


def logger(body, key='logger'):
    msg = f'Service: Bank Accounts - {body}'
    channel.basic_publish(exchange='',
                          routing_key=key,
                          body=msg)
