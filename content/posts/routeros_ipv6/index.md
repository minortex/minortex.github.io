+++
date = '2025-09-23T21:05:32+08:00'
draft = true
title = 'Routeros_ipv6'
+++

使用napt，对于eui64:
2: ens192: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0c:29:80:e3:fe brd ff:ff:ff:ff:ff:ff
    altname enp11s0
    inet 192.168.114.3/24 brd 192.168.114.255 scope global dynamic ens192
       valid_lft 13117sec preferred_lft 13117sec
    inet6 2409:8a20:ae0:6af0:20c:29ff:fe80:e3fe/64 scope global dynamic mngtmpaddr 
       valid_lft 7124sec preferred_lft 3524sec

出来的ip地址：
curl 6.ipw.cn
2409:8a20:ae0:6af0:20c:29ff:fe80:e3fe

开启了隐私拓展后：

3: enp0s20f0u3u4: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 00:e0:4c:68:09:ce brd ff:ff:ff:ff:ff:ff
    altname enx00e04c6809ce
    inet6 fd11:4514:5a51:0:81e3:4643:cd5c:7b73/64 scope global dynamic noprefixroute 
       valid_lft 7194sec preferred_lft 3594sec

❯ curl 6.ipw.cn
2409:8a20:bc5:c950:9b1b:4643:cd5c:7b73

其中65-80的这一段，若不是真实反应mac地址，那么好像在snpt的时候不会为你保留。

