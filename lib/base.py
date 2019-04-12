# -*- coding: utf-8 -*-

import time
import logging

import pika


class RabbitMQ(object):

    def __init__(self, host, port, username, password, queue):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.queue = queue

        self.connection = self.get_connection()
        self.channel = self.get_channel(self.connection)

    def get_connection(self):
        creds = pika.credentials.PlainCredentials(username=self.username,
                                                  password=self.password)
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=self.host,
                                                                       port=self.port,
                                                                       virtual_host='/',
                                                                       credentials=creds))
        logging.info('connect to rabbitmq at %s:%d' % (self.host, self.port))
        return connection

    def get_reconnection(self):
        self.connection.close()
        connection = self.get_connection()
        return connection

    def get_channel(self, connection):
        channel = connection.channel()
        channel.queue_declare(queue=self.queue, durable=True)
        return channel

    def ensure_channel(self):
        while self.connection.is_closed or self.channel.is_closed:
            logging.info('reconnecting to rabbitmq')
            if self.connection.is_closed:
                self.connection = self.get_reconnection()
            self.channel = self.get_channel(self.connection)
            if not self.channel.is_closed:
                logging.info('reconnected to rabbitmq')
                break
            else:
                time.sleep(1)

    def publish(self, message):
        self.ensure_channel()
        self.channel.basic_publish(exchange='',  # use default exchange
                                   routing_key=self.queue,
                                   body=message,
                                   properties=pika.BasicProperties(
                                       delivery_mode=2,  # make message persistent
                                   ))

    def close(self):
        self.channel.close()
        self.connection.close()


