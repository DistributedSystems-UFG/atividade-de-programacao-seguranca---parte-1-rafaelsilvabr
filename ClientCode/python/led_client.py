#from __future__ import print_function

import logging
import sys

import grpc
import crypto
import iot_service_pb2
import iot_service_pb2_grpc

from const import *


def run():
    with grpc.insecure_channel(GRPC_SERVER+':'+GRPC_PORT) as channel:
        
        state = crypto.encrypt(sys.argv[1])
        ledname = crypto.encrypt(sys.argv[2])
        login = crypto.encrypt(sys.argv[3])
        password = crypto.encrypt(sys.argv[4])

        stub = iot_service_pb2_grpc.IoTServiceStub (channel)
        response = stub.BlinkLed(iot_service_pb2.LedRequest(state=state,ledname=ledname, login=login, password=password))

    if response.ledstate[ledname] == 1:
        print("Led state is on")
    else:
        print("Led state is off")

if __name__ == '__main__':
    logging.basicConfig()
    run()
