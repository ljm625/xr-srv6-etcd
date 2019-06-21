import getopt
from pprint import pprint

import sys

import time

import textfsm
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
            # pprint(json.loads(result))
            return json.loads(result)
        except AbortionError:
            print(
                'Unable to connect to local box, check your gRPC destination.'
                )

    def exec(self,cmd):
        try:
            err, result = self.client.showcmdtextoutput(cmd)
            if err:
                pprint(err)
            return result
        except AbortionError:
            print(
                'Unable to connect to local box, check your gRPC destination.'
            )


class SIDProcessor(object):
    def __init__(self,template="template.fsm"):
        self.template=template
        pass

    def get_sids(self,raw_data):
        # print(raw_data)
        sid_data={}
        with open(self.template) as file:
            re_table = textfsm.TextFSM(file)
            data = re_table.ParseText(raw_data)
            new_data=[]
            tmp_entry=[]
            for row in data:
                if tmp_entry:
                    if tmp_entry[0] == row[0] and tmp_entry[1] == row[1]:
                        tmp_entry[2].extend(row[2])
                    else:
                        new_data.append(tmp_entry)
                        tmp_entry=row
                else:
                    tmp_entry=row
            new_data.append(tmp_entry)
            # Display result as CSV
            # First the column headers
            # print(', '.join(re_table.header))
            # Each row of the table.
            for row in new_data:
                sid_data[row[0]]=[{
                    "name":"end-with-psp",
                    "sid":row[1]
                }]
                for data in row[2]:
                    sid_data[row[0]].append({
                        "name":"end-x-with-psp",
                        "sid":data
                    })
                print('{}, {}, {}, {} '.format(row[0],row[1],json.dumps(row[2]),row[3]))

        return sid_data

    def get_ip(self,raw_data):
        ip_data={}
        with open("template2.fsm") as file:
            re_table = textfsm.TextFSM(file)
            data = re_table.ParseText(raw_data)
            for row in data:
                ip_data[row[0]] = row[1]
                print(', '.join(row))
        return ip_data

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
    grpc_port = username = password = etcd_ip = etcd_port= device_name= grpc_ip=  None
    opts, args = getopt.getopt(sys.argv[1:], '-h:-g:-u:-p:-i:-e:-z:', ['help', 'grpc-port=', 'username=', 'password=', 'etcd-ip=', 'etcd-port=', 'grpc-ip='])
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            print(
                "[*] Help: Please enter Hostname, gRPC port, username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -d RouterA -g 57777 -u cisco -p cisco -i 127.0.0.1 -e 2379")
            exit()
        # if opt_name in ('-d', '--device-name'):
        #     device_name= opt_value
        #     print("[*] Device name is {}".format(device_name))
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
        if opt_name in ('-z', '--grpc-ip'):
            grpc_ip = opt_value
            print("[*] Etcd IP is {}".format(etcd_ip))

    if None in [grpc_ip, grpc_port, username, password, etcd_ip, etcd_port]:
        print(
            "[*] Help: Please enter Hostname, gRPC port, username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -d RouterA -gp 57777 -u cisco -p cisco -e 127.0.0.1 -ep 2379")
        exit()
    # device_name="RouterA"

    grpc = gRPCFetcher(grpc_ip, grpc_port, username, password)
    old_sid_data=None
    old_ip_data = None
    while True:
        data = grpc.exec("show isis database verbose")
        processor = SIDProcessor()
        sid_data= processor.get_sids(data)
        ip_data = processor.get_ip(data)
        if sid_data!=old_sid_data or ip_data!=old_ip_data:
            etcd=EtcdHelper(etcd_ip,etcd_port)
            for k,v in sid_data.items():
                etcd.put(k,json.dumps(v))
            node_list=[]
            for k,v in ip_data.items():
                node_list.append(k)
            etcd.put('nodes',json.dumps(node_list))
            etcd.put('node_ip',json.dumps(ip_data))
            print("[*] Updating SID Info")
            old_ip_data=ip_data
            old_sid_data=sid_data
        time.sleep(60)
    # pprint(sid_data)
if __name__ == '__main__':
    main()
