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
    def get(self,path='{"Cisco-IOS-XR-segment-routing-srv6-oper:srv6": [null] }'):
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
def get_host_name(grpc):
    result = grpc.get('{"Cisco-IOS-XR-shellutil-cfg:host-names": {"host-name": [null] } }')
    print(result['Cisco-IOS-XR-shellutil-cfg:host-names']['host-name'])
    return result['Cisco-IOS-XR-shellutil-cfg:host-names']['host-name']

def get_loopback_ip(grpc):
    result = grpc.get('{"openconfig-interfaces:interfaces": {"interface": [null] } }')
    for interface in result['openconfig-interfaces:interfaces']['interface']:
        if interface['name'] == 'Loopback0':
            for sub in interface['subinterfaces']['subinterface']:
                for address in sub['openconfig-if-ip:ipv4']['addresses']['address']:
                    print(address['ip'])
                    return address['ip']
                # print(sub['openconfig-if-ip:ipv4'])


def main():

    grpc_port = username = password = etcd_ip = etcd_port= device_name= grpc_ip=  None
    opts, args = getopt.getopt(sys.argv[1:], '-h:-g:-u:-p:-i:-e:-z:', ['help', 'grpc-port=', 'username=', 'password=', 'etcd-ip=', 'etcd-port=', 'grpc-ip='])
    for opt_name, opt_value in opts:
        if opt_name in ('-h', '--help'):
            print(
                "[*] Help: Please enter Hostname, gRPC port, username, password, Etcd IP, Etcd Port in parameters. Example: \n python main.py -d RouterA -g 57777 -u cisco -p cisco -i 127.0.0.1 -e 2379 -z 127.0.0.1")
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
            "[*] Help: Please enter Hostname, gRPC port, username, password, Etcd IP, Etcd Port, gRPC IP in parameters. Example: \n python main.py -d RouterA -g 57777 -u cisco -p cisco -i 127.0.0.1 -e 2379 -z 127.0.0.1")
        exit()
    # device_name="RouterA"

    grpc = gRPCFetcher('jp.debug.tech', grpc_port, username, password)
    old_sid_data = old_hostname = old_lb_address=None
    while True:
        data = grpc.get()
        hostname = get_host_name(grpc)
        lb_address = get_loopback_ip(grpc)
        processor = SIDProcessor()
        sid_data= processor.get_sids(data)
        if sid_data!=old_sid_data or hostname!=old_hostname or lb_address!=old_lb_address:
            etcd=EtcdHelper(etcd_ip,etcd_port)
            # ETCD
            etcd.put(hostname,json.dumps(sid_data))
            # Node List
            result =etcd.get('nodes')
            if result:
                node_list =json.loads(result)
                if hostname not in node_list:
                    node_list.append(hostname)
                    etcd.put('nodes', json.dumps(node_list))
            else:
                etcd.put('nodes', json.dumps([hostname]))
            # Node IP List
            result =etcd.get('node_ip')
            if result:
                ip_data =json.loads(result)
                if hostname not in ip_data.keys():
                    ip_data[hostname]=lb_address
                    etcd.put('node_ip', json.dumps(ip_data))
            else:
                etcd.put('node_ip', json.dumps({hostname:ip_data}))

            print("[*] Updating SID Info")
            old_sid_data=sid_data
            old_hostname=hostname
            old_lb_address=lb_address
        time.sleep(30)
    # pprint(sid_data)
if __name__ == '__main__':
    main()
