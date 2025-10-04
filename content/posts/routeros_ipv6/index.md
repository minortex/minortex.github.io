+++
date = '2025-09-23T21:05:32+08:00'
draft = false
title = 'RouterOS的IPv6多网段统一进行NAPT转换'
lastmod = '2025-10-04T16:38:46+08:00'
+++

## 前言

终于决定给社团的网络修一修了~

## 实践

### 内网划分

对于内网的划分是这样的：

使用`ULA`子网：`fd11:4514:5a51::/48`

然后划分四个网段，分别给设施、1-3楼用户。

- `fd11:4514:5a51:0::/64`，尽量使用`EUI64`分配地址，同时分配公网前缀用于`IPv6`访问。
- `fd11:4514:5a51:[1-3]::/64`，仅仅分配`ULA`，不分配公网前缀，使得设备流量分流到三条移动宽带。

### /DNPT规则

相比之前使用的`fc00-fc03`网段来说，可以少写很多规则，直接转换`/60`的前缀即可。

参考如下：

```shell
 3    ;;; PCC-1 Output
      chain=prerouting action=mark-packet new-packet-mark=PCC-1 passthrough=yes src-address=fd11:4514:5a51::/60 dst-address-list=!ULAs per-connection-classifier=src-address:3/0 log=no log-prefix="" 

 4    ;;; PCC-2 Output
      chain=prerouting action=mark-packet new-packet-mark=PCC-2 passthrough=yes src-address=fd11:4514:5a51::/60 dst-address-list=!ULAs per-connection-classifier=src-address:3/1 log=no log-prefix="" 

 5    ;;; PCC-3 Output
      chain=prerouting action=mark-packet new-packet-mark=PCC-3 passthrough=yes src-address=fd11:4514:5a51::/60 dst-address-list=!ULAs per-connection-classifier=src-address:3/2 log=no log-prefix="" 

 6    ;;; PCC-1 Output NPT
      chain=postrouting action=SNPT src-prefix=fd11:4514:5a51::/60 dst-prefix=2409:8a20:ae0:6af0::/60 src-address=fd11:4514:5a51::/60 packet-mark=PCC-1 log=no log-prefix="" 

 7    ;;; PCC-2 Output NPT
      chain=postrouting action=SNPT src-prefix=fd11:4514:5a51::/60 dst-prefix=2409:8a20:ae0:1360::/60 src-address=fd11:4514:5a51::/60 packet-mark=PCC-2 log=no log-prefix="" 

 8    ;;; PCC-3 Output NPT
      chain=postrouting action=SNPT src-prefix=fd11:4514:5a51::/60 dst-prefix=2409:8a20:bc5:c950::/60 src-address=fd11:4514:5a51::/60 packet-mark=PCC-3 log=no log-prefix="" 

9    ;;; PCC-1 Input NPT
      chain=prerouting action=dnpt src-prefix=2409:8a20:ae0:6af0::/60 dst-prefix=fd11:4514:5a51::/60 dst-address=2409:8a20:ae0:6af0::/60 log=no log-prefix="" 

10    ;;; PCC-2 Input NPT
      chain=prerouting action=dnpt src-prefix=2409:8a20:ae0:1360::/60 dst-prefix=fd11:4514:5a51::/60 dst-address=2409:8a20:ae0:1360::/60 log=no log-prefix="" 

11    ;;; PCC-3 Input NPT
      chain=prerouting action=dnpt src-prefix=2409:8a20:bc5:c950::/60 dst-prefix=fd11:4514:5a51::/60 dst-address=2409:8a20:bc5:c950::/60 log=no log-prefix="" 
```

总共9条规则就可以解决，依次是出站PCC规则分流，出站规则，入站DNPT规则。

## 问题

### 脚本自动更新问题

我真的非常不愿意去看RouterOS的脚本，太乱了，沿用了之前的内容，只是修改了其中的网段。

### 入站问题

按照现有的规则，实际上是无法入站的，需要单独添加一条规则，而且似乎只对`EUI64`的地址生效。

```
 2    ;;; PCC-1 LAN_Device
      chain=prerouting action=accept dst-address=2409:8a20:ae0:6af0::/64 log=no log-prefix=""
```

其实，对于隐私地址，防火墙也非常难以匹配规则，因为后缀变，运营商的前缀也跟着变，一般解决方案都是`socat`或者反向匹配(目标地址写`::be24:11ff:fe82:8282/::ffff:ffff:ffff:ffff`这样)。

### 内网访问问题

对于内网v6互访(从0网段到1)是失败的，我怀疑是PCC规则误伤了，但是排查还是挺困难的，因为RouterOS的日志调试我根本不会用，不出日志，你说要是有个`tcpdump`我就会了...

## 补充

### 关于EUI64和RFC4291

使用`NAPT`，对于`EUI64`:

```bash
2: ens192: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:65:43:21 brd ff:ff:ff:ff:ff:ff
    altname enp11s0
    inet 192.168.114.39/24 brd 192.168.114.255 scope global dynamic ens192
       valid_lft 13117sec preferred_lft 13117sec
    inet6 fd11:4514:5a51:0:20c:29ff:fe65:4321/64 scope global dynamic mngtmpaddr 
       valid_lft 6993sec preferred_lft 3393sec
    inet6 2409:8a20:ae0:6af0:20c:29ff:fe65:4321/64 scope global dynamic mngtmpaddr 
       valid_lft 7124sec preferred_lft 3524sec
```

开启了隐私拓展后：

```bash
4: enp0s20f0u3u4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 01:e0:22:65:43:21 brd ff:ff:ff:ff:ff:ff
    altname enx00e04c6809ce
    inet 192.168.101.80/24 brd 192.168.101.255 scope global dynamic noprefixroute enp0s20f0u3u4
       valid_lft 8484sec preferred_lft 8484sec
    inet6 fd11:4514:5a51:1:ff9d:d0eb:c4f3:ad54/64 scope global dynamic noprefixroute 
       valid_lft 7117sec preferred_lft 3517sec
❯ curl 6.ipw.cn
2409:8a20:ae0:1361:cfab:d0eb:c4f3:ad543
```

其中65-80的这一段，若不是真实反应MAC地址，那么好像在`SNPT`的时候不会为你保留。

有人说，变化是因为要符合校验和，但是对于`EUI64`地址好像并不需要啊，这是为什么呢？

查了下，发现`EUI64`并没有强制要求必须保留，所以为了效率和随机性，就找了一个能够唯一标识的地址使用了。

## 总结

感觉调RouterOS完全就是在猜啊，没有wrt类那种我理解的感觉，希望以后能找到个大佬浇浇我。