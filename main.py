import getopt
from pprint import pprint

import sys

import time
from grpc.framework.interfaces.face.face import AbortionError
import json
from iosxr_grpc.cisco_grpc_client import CiscoGRPCClient

from etcdhelper import EtcdHelper


class gRPCFetcher(object):
    def __init__(self,ip,port,username,password,timeout=10):
        self.client = CiscoGRPCClient(ip, port, timeout, username, password)
    def get(self):
        path = '{"Cisco-IOS-XR-segment-routing-srv6-oper:srv6": [null] }'
        try:
            err, result = self.client.getoper(path)
            if err:
                pprint(err)
            pprint(json.loads(result))
            return json.loads(result)
        except AbortionError:
            print(
                'Unable to connect to local box, check your gRPC destination.'
                )

class SIDProcessor(object):
    def __init__(self):
        pass

    def get_sids(self,data):
        sid_data=[]
        pprint(data["Cisco-IOS-XR-segment-routing-srv6-oper:srv6"]["active"]["locator-all-active-sids"]["locator-all-active-sid"])
        for sid in data["Cisco-IOS-XR-segment-routing-srv6-oper:srv6"]["active"]["locator-all-active-sids"]["locator-all-active-sid"]:
            print("{} - {}".format(sid["function-type"],sid["sid"]))
            tmp_data={"name":sid["function-type"],"sid":sid["sid"],"sid-context":sid["sid-context"]}
            if sid["function-type"] == "end-x-with-psp":
                tmp_data["interface"] = sid["sid-context"]["key"]["x"]["interface"]
            sid_data.append(tmp_data)
        return sid_data

    # def replace(self):
    #     path = open('snips/bgp_start.json').read()
    #     # try:
    #     response = self.client.replaceconfig(path)
    #     if response.errors:
    #         err = json.loads(response.errors)
    #         print(err)
    #     # except Exception as e:
    #     #     e.print()
    #     #     print(
    #     #         'Unable to connect to local box, check your gRPC destination.'
    #     #         )
    #
    # def merge(self):
    #     path = open('snips/bgp_merge.json').read()
    #     try:
    #         response = self.client.mergeconfig(path)
    #         if response.errors:
    #             err = json.loads(response.errors)
    #             print(err)
    #     except AbortionError:
    #         print(
    #             'Unable to connect to local box, check your gRPC destination.'
    #             )
    #
    # def delete(self):
    #     path = open('snips/bgp_start.json').read()
    #     try:
    #         response = self.client.deleteconfig(path)
    #         if response.errors:
    #             err = json.loads(response.errors)
    #             print(err)
    #     except AbortionError:
    #         print(
    #             'Unable to connect to local box, check your gRPC destination.'
    #             )




def main():
    '''
    This example does not use TLS, if you want to use TLS please refer to the example with tls
    Here is a workflow of the example that uses all the different types.
    '''
    grpc_port = username = password = etcd_ip = etcd_port= device_name= None
    opts, args = getopt.getopt(sys.argv[1:], '-h-d:-g:-u:-p:-i:-e:', ['help','device-name=', 'grpc-port=', 'username=', 'password=', 'etcd-ip=', 'etcd-port='])
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            print(
                "[*] Help: Please enter Hostname, gRPC port, username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -d RouterA -g 57777 -u cisco -p cisco -i 127.0.0.1 -e 2379")
            exit()
        if opt_name in ('-d', '--device-name'):
            device_name= opt_value
            print("[*] Device name is {}".format(device_name))
        if opt_name in ('-g', '--grpc-port'):
            grpc_port= int(opt_value)
            print("[*] gRPC port is {}".format(grpc_port))
        if opt_name in ('-u', '--username'):
            username = opt_value
            print("[*] Username is {}".format(username))
            # do something
        if opt_name in ('-p', '--password'):
            password = opt_value
            print("[*] Password is {}".format(password))
        if opt_name in ('-i', '--etcd-ip'):
            etcd_ip = opt_value
            print("[*] Etcd IP is {}".format(etcd_ip))
        if opt_name in ('-e', '--etcd-port'):
            etcd_port = int(opt_value)
            print("[*] Etcd Port is {}".format(etcd_port))
    if None in [grpc_port, username, password, etcd_ip, etcd_port]:
        print(
            "[*] Help: Please enter Hostname, gRPC port, username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -d RouterA -gp 57777 -u cisco -p cisco -e 127.0.0.1 -ep 2379")
        exit()
    # device_name="RouterA"

    grpc = gRPCFetcher('jp.debug.tech', grpc_port, username, password)
    old_sid_data=None
    while True:
        data = grpc.get()
        processor = SIDProcessor()
        sid_data= processor.get_sids(data)
        if sid_data!=old_sid_data:
            etcd=EtcdHelper(etcd_ip,etcd_port)
            etcd.put(device_name,json.dumps(sid_data))
            print("[*] Updating SID Info")
        time.sleep(60)
    # pprint(sid_data)
if __name__ == '__main__':
    main()
