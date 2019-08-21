import pika
import sys
import json
import settings


class RabbitMQ(object):

    def __init__(self,):
        self.queue_name = 'urls'
        self.exchange_name = 'info'

        self.host = settings.RABBITMQ_HOST
        self.user = settings.RABBITMQ_USER
        self.password = settings.RABBITMQ_PASS

        self.credentials = pika.PlainCredentials(self.user, self.password)

        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host, port=5672,
                                                                            credentials=self.credentials))

##        self.connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host))

        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange=self.exchange_name,exchange_type='direct')
        self.channel.queue_declare(queue=self.queue_name)
        self.channel.queue_bind(exchange=self.exchange_name,
                           queue=self.queue_name,
                           routing_key='')

    def publish(self,message_dict):
        self.channel.basic_publish(exchange=self.exchange_name, routing_key='', body=json.dumps(message_dict))


