from time import sleep

import pika
from vnpy.rabbitmq.config.rabbitmq import RabbitmqCnf


class RabbitMQ(object):

    def __init__(self, config: RabbitmqCnf):
        self._host = config.HOST  # broker IP
        self._port = config.PORT  # broker port
        self._vhost = config.VHOST  # vhost
        self._credentials = pika.PlainCredentials(RabbitmqCnf.USER, RabbitmqCnf.PASS)
        self._connection = None
        self.connect_count = 0
        self.get_count = 0

    def get_connection(self):
        return self._connection

    def connect(self):
        self.connect_count = 0
        # 创建RabbitMQ的连接对象
        # 一定时间内和服务端没有数据来往，服务端会自动断开连接，不会一直保持connection状态。heartbeat=0 不发送心跳，服务端永远不会断开这个连接。
        parameter = pika.ConnectionParameters(self._host, self._port, self._vhost, self._credentials, heartbeat=0)
        while True:
            connect_success = False
            try:
                self._connection = pika.BlockingConnection(parameter)  # 建立连接
                connect_success = True
            except Exception as e:
                sleep(1)  # 睡眠为了连接失败时减少尝试次数。
                # 注意还可以计算重试次数,达到一定次数后,可以放弃重连接。
                self.connect_count += 1
                if self.connect_count >= 10:  # 重新连接次数大于10次时，就不再重新连接。
                    print(f"rabbitmq服务器连接断开,错误信息为:{e},已经自动重连{self.connect_count}次还未连接成功,结束自动重连。")
                    return

            if connect_success:
                break

    def put(self, message_str, exchange='test_exchange', route_key="route_key", exchange_type='topic', delivery_mode=2, durable=True):
        """往队列里面放入消息"""
        if self._connection is None:
            return
        try:
            channel = self._connection.channel()  # 获取channel
            channel.exchange_declare(exchange, exchange_type=exchange_type, durable=durable)  # 声明交换机
            # channel.queue_declare(queue=queue_name)  # 申明使用的queue

            #  调用basic_publish方法向RabbitMQ发送数据， 这个方法应该只支持str类型的数据。
            channel.basic_publish(
                exchange=exchange,  # 指定交换机(频道)
                routing_key=route_key,  # 指定路由(routing_key在使用匿名交换机的时候才需要指定，表示发送到哪个队列)
                body=message_str,  # 具体发送的数据
                properties=pika.BasicProperties(delivery_mode=delivery_mode)
            )
            channel.close()
            self.close()
        except Exception:
            pass

    def get(self, queue_name='test_queue', exchange='test_exchange', route_key='route_key', on_message_callback=None, durable=True):
        """从队列里面取出消息"""
        if self._connection is None:
            return
        if on_message_callback is None:
            return
        try:
            channel = self._connection.channel()
            channel.queue_declare(queue=queue_name, durable=durable)  # 把队列和中间人(channel:交换机)绑定
            channel.queue_bind(queue_name, exchange, route_key)
            channel.basic_qos(prefetch_count=1)  # 防止消息积压,指定1次prefetch_count条消息
            channel.basic_consume(queue=queue_name, on_message_callback=on_message_callback)  # 消费消息
            channel.start_consuming()  # 开始循环取消息,一直等待消息
        except Exception as e:
            self.get_count += 1
            print(f"从rabbitmq服务器中获取数据失败,错误信息为:{e},重新进行第{self.get_count}次请求")
            if self.get_count >= 10:  # 当向rabbitmq请求10次还未反应时,则不再请求,结束程序。
                self.get_count = 0
                return
            self.connect()
            self.get(queue_name, exchange, route_key, on_message_callback, durable=True)

    @staticmethod
    def callback(ch, method, properties, message_str):
        """收到消息后的回调函数"""
        print(f"Received {message_str}")

    def close(self):
        """关闭RabbitMQ的连接"""
        if self._connection is not None:
            self._connection.close()
