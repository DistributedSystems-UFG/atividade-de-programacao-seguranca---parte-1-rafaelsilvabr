import glob
import time
from kafka import KafkaProducer, KafkaConsumer
import math
import threading
import crypto
import RPi.GPIO as GPIO # Import Raspberry Pi GPIO library
from const import *

# For access to the temperature sensor
base_dir = '/sys/bus/w1/devices/'
try:
    device_folder = glob.glob(base_dir + '28*')[0]
    device_file = device_folder + '/w1_slave'
except:
    print("No 1-Wire devices found.")

red_led_pin = 16
green_led_pin = 18
light_sensor_pin = 29


# Initialize GPIO for the LEDs
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BOARD) # Use physical pin numbering
GPIO.setup(red_led_pin, GPIO.OUT, initial=GPIO.LOW) # Set pin 16 to be an output pin and set initial value to low (off)
GPIO.setup(green_led_pin, GPIO.OUT, initial=GPIO.LOW) # Idem for pin 18

producer = KafkaProducer(bootstrap_servers=[KAFKA_SERVER+':'+KAFKA_PORT],
                         security_protocol='SASL_PLAINTEXT',
                         sasl_mechanism='PLAIN',
                         sasl_plain_username='bob',
                         sasl_plain_password='bob-pass')
last_reported_temp = 35
last_reported_light_level = 0

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        temp_f = temp_c * 9.0 / 5.0 + 32.0
        return temp_c, temp_f

def read_light_sensor (pin_to_circuit):
    count = 0

    #Output on the pin for
    GPIO.setup(pin_to_circuit, GPIO.OUT)
    GPIO.output(pin_to_circuit, GPIO.LOW)
    time.sleep(0.1)

    #Change the pin back to input
    GPIO.setup(pin_to_circuit, GPIO.IN)

    #Count until the pin goes high
    while (GPIO.input(pin_to_circuit) == GPIO.LOW):
        count += 1

    return count

def consume_led_command():
    consumer = KafkaConsumer(bootstrap_servers=[KAFKA_SERVER+':'+KAFKA_PORT],
                                 security_protocol='SASL_PLAINTEXT',
                                 sasl_mechanism='PLAIN',
                                 sasl_plain_username='bob',
                                 sasl_plain_password='bob-pass')
    consumer.subscribe(topics=('ledcommand'))
    ledpin = 0
    for msg in consumer:
        msg_key = crypto.decrypt(msg.key).decode()
        msg_value = crypto.decrypt(msg.value).decode()
        print ('Led command received: ', msg_key)
        print ('Led to blink: ', msg_value)
        if msg_key == 'red':
            ledpin = red_led_pin
        else:
            ledpin = green_led_pin
        if msg_value == '1':
            print ('Turning led on')
            GPIO.output(ledpin,GPIO.HIGH)
        elif msg_value == '0':
            print ('Turning led off')
            GPIO.output(ledpin,GPIO.LOW)
        elif msg_value == '2':
            print ('Turning led off')
        else:
            print ('Wrong led state')

trd =threading.Thread(target=consume_led_command)
trd.start()

while True:
    # Read and report temperature to the cloud-based service
    #(temp_c, temp_f) = read_temp()
    #print('Temperature: ', temp_c, temp_f)
    temp_c=35
    if (math.fabs(temp_c - last_reported_temp) >= 0.1):
        last_reported_temp = temp_c
        producer.send('temperature', crypto.encrypt(str(temp_c).encode()))

    # Read and report light lelve to the cloud-based service
    light_level = read_light_sensor(light_sensor_pin)
    print('Light level: ', light_level)
    if (light_level != last_reported_light_level):
        last_reported_light_level = light_level
        producer.send('lightlevel', crypto.encrypt(str(light_level).encode()))
    time.sleep(1)
