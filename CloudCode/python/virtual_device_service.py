from kafka import KafkaConsumer, KafkaProducer
from const import *
import threading

from concurrent import futures
import logging

import grpc, crypto
import iot_service_pb2
import iot_service_pb2_grpc

# Twin state
current_temperature = 'void'
current_light_level = 'void'
led_state = {'red':0, 'green':0}

# Kafka consumer to run on a separate thread
def consume_temperature():
    global current_temperature
    consumer = KafkaConsumer(bootstrap_servers=[KAFKA_SERVER+':'+KAFKA_PORT],
                             security_protocol='SASL_PLAINTEXT',
                             sasl_mechanism='PLAIN',
                             sasl_plain_username='bob',
                             sasl_plain_password='bob-pass')
    consumer.subscribe(topics=('temperature'))
    for msg in consumer:
        msg_value = crypto.decrypt(msg.value).decode()
        print ('Received Temperature: ', msg_value)
        current_temperature = msg_value

# Kafka consumer to run on a separate thread
def consume_light_level():
    global current_light_level
    consumer = KafkaConsumer(bootstrap_servers=[KAFKA_SERVER+':'+KAFKA_PORT],
                             security_protocol='SASL_PLAINTEXT',
                             sasl_mechanism='PLAIN',
                             sasl_plain_username='bob',
                             sasl_plain_password='bob-pass')
    consumer.subscribe(topics=('lightlevel'))
    for msg in consumer:
        msg_value = crypto.decrypt(msg.value).decode()
        print ('Received Light Level: ', msg_value)
        current_light_level = msg_value

def produce_led_command(state, ledname):
    producer = KafkaProducer(bootstrap_servers=[KAFKA_SERVER+':'+KAFKA_PORT],
                                 security_protocol='SASL_PLAINTEXT',
                                 sasl_mechanism='PLAIN',
                                 sasl_plain_username='bob',
                                 sasl_plain_password='bob-pass')
    key = crypto.encrypt(ledname.encode())
    value = crypto.encrypt(str(state).encode())
    # producer.send('ledcommand', key=ledname.encode(), value=str(state).encode())
    producer.send('ledcommand', key=key, value=value)
    return state

class IoTServer(iot_service_pb2_grpc.IoTServiceServicer):

    def SayTemperature(self, request, context):
        login = crypto.decrypt(request.login.encode()).decode()
        password = crypto.decrypt(request.password.encode()).decode()
        if not crypto.create_or_login(login, password):
            print(f"Failed login attempt for user '{login}'")
            return iot_service_pb2.TemperatureReply(temperature='Wrong password!')
        print(f"User '{login}' consumed current temperature level.")
        return iot_service_pb2.TemperatureReply(temperature=current_temperature)

    def BlinkLed(self, request, context):
        login = crypto.decrypt(request.login.encode()).decode()
        password = crypto.decrypt(request.password.encode()).decode()
        if not crypto.create_or_login(login, password):
            print(f"Failed login attempt for user '{login}'")
            # Update led state of twin
            led_state[request.ledname] = 2
            return iot_service_pb2.LedReply(ledstate=led_state)
        ledname = crypto.decrypt(request.ledname.encode()).decode()
        state = crypto.decrypt(request.state.encode()).decode()

        print ("Blink led ", ledname)
        print ("...with state ", state)
        produce_led_command(state, ledname)
        # Update led state of twin
        led_state[request.ledname] = int(state)
        print(f"User '{login}' blinked led {ledname} to {state}.")
        return iot_service_pb2.LedReply(ledstate=led_state)

    def SayLightLevel(self, request, context):
        login = crypto.decrypt(request.login.encode()).decode()
        password = crypto.decrypt(request.password.encode()).decode()
        if not crypto.create_or_login(login, password):
            print(f"Failed login attempt for user '{login}'")
            return iot_service_pb2.LightLevelReply(lightLevel='Wrong password!')
        print(f"User '{login}' consumed current light level.")
        return iot_service_pb2.LightLevelReply(lightLevel=current_light_level)

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    iot_service_pb2_grpc.add_IoTServiceServicer_to_server(IoTServer(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()


if __name__ == '__main__':
    logging.basicConfig()

    trd1 = threading.Thread(target=consume_temperature)
    trd1.start()

    trd2 = threading.Thread(target=consume_light_level)
    trd2.start()

    # Initialize the state of the leds on the actual device
    for color in led_state.keys():
        produce_led_command (led_state[color], color)
    serve()