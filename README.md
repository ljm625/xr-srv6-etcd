# SRv6 SID fetching docker for IOS-XR

This docker is used for fetching the SID from IOS-XR devices from Yang(through gRPC) and store it in etcd (Anothor docker on IOS XR)

Will also provide API for application querying the data.

#### Usage:

On IOS XR Bash, exec
```bash
docker pull ljm625/xr-srv6-etcd:yang
docker run -itd   --cap-add=SYS_ADMIN   --cap-add=NET_ADMIN   -v /var/run/netns:/var/run/netns ljm625/xr-srv6-etcd:yang -g #gRPCPort -u #UserName -p #Password -i #EtcdIP -e #EtcdPort -z #GrpcIP
```

replace # Part with the value in your environment：

For Example：

- gRPC Port: 57777
- Username : Cisco
- Password : Cisco
- Etcd IP : 172.20.100.150
- Etcd Port :2769
- gRPC IP : 127.0.0.1

Then the command is:

```
docker run -itd   --cap-add=SYS_ADMIN   --cap-add=NET_ADMIN \
  -v /var/run/netns:/var/run/netns ljm625/xr-srv6-etcd:yang \
   -g 57777 -u Cisco -p Cisco -i 172.20.100.150 -e 2769 -z 127.0.0.1
```


Check the logs by `docker logs -f {container Name}` to check run status.