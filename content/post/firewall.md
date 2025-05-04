+++
date = '2025-04-25T21:46:16+08:00'
draft = false
title = '那些防火墙的事情'
description = 'iptables&nftables&firewalld的世界！'
tags = ['Arch']
+++

## 前言

其实防火墙这玩意，我三年前就有所耳闻。那时候在用iptables来配置路由器的虚拟组网规则，就被弄得头昏脑转。

如今过去了那么久，知识储备多了那么一点点，正好有需求，就重新了解了一下。


## iptables

iptables，这玩意算是个古董了，大概在21世纪初就有了。不过毕竟是老东西，现在大部分旧设备都是用的它，很多软件在修改防火墙规则的时候也只改它。

提起iptables，我们也许会想到五链四表，不过一般来说，知道nat和filter表就已经足够完成80%的工作了（ipv4），我在[archwiki的iptables](https://wiki.archlinuxcn.org/wiki/Iptables)章节翻到这张图，也许能够有助于理解：

```
                               XXXXXXXXXXXXXXXXXX
                             XXX     Network    XXX
                               XXXXXXXXXXXXXXXXXX
                                       +
                                       |
                                       v
 +-------------+              +------------------+
 |table: filter| <---+        | table: nat       |
 |chain: INPUT |     |        | chain: PREROUTING|
 +-----+-------+     |        +--------+---------+
       |             |                 |
       v             |                 v
 [local process]     |           ****************          +--------------+
       |             +---------+ Routing decision +------> |table: filter |
       v                         ****************          |chain: FORWARD|
****************                                           +------+-------+
Routing decision                                                  |
****************                                                  |
       |                                                          |
       v                        ****************                  |
+-------------+       +------>  Routing decision  <---------------+
|table: nat   |       |         ****************
|chain: OUTPUT|       |               +
+-----+-------+       |               |
      |               |               v
      v               |      +-------------------+
+--------------+      |      | table: nat        |
|table: filter | +----+      | chain: POSTROUTING|
|chain: OUTPUT |             +--------+----------+
+--------------+                      |
                                      v
                               XXXXXXXXXXXXXXXXXX
                             XXX    Network     XXX
                               XXXXXXXXXXXXXXXXXX
```

这里的Network，指的就是不同的网卡接口。

接着我来说说自己的理解：

### 啥表啥链？

1. **filter**表 最简单，也是默认的表。它只有OUTPUT，INPUT，FORWARD链。这几个顾名思义，分别是来源本机，目标本机，经过本机的数据包。
    一般来说，
    - **OUTPUT** 的默认规则是ACCEPT，也就是允许所有来源本机的数据包发出。
    - **INPUT** 的默认规则是DROP，也就是不允许外来的数据包访问本机。我们一般监听的端口需要配置例外的规则，否则就无法被访问。
    - **FORWARD* *也是DROP。默认不允许不同网络接口之间的数据包转发。想要转发不仅仅需要手动放行，还得开启内核的IP转发。
        ```shell
        ## 临时启用
        sysctl -w net.ipv4.ip_forward=1
        ## 永久启用
        echo "net.ipv4.ip_forward=1" | sudo tee -a /etc/sysctl.conf
        sysctl -p
        ```
        举个例子：
        ```
        Chain FORWARD (policy DROP 0 packets, 0 bytes)
         pkts bytes target     prot opt in     out     source               destination
            1    52 ACCEPT     all  --  wg0    *       0.0.0.0/0            0.0.0.0/0
        ```

2. **nat**表 这个表有四条链，不过我一般只用其中的两条：PREROUTING和POSTROUTING，分别处理端口映射以及ip伪装。
    - **PREROUTING** 这一个链其实我接触得不多，因为基本都是在ui上面设置的。但是摸过SAST的RouterOS之后，那个ui配置起来就像是手搓iptables一样，我就马上理解了。
        一个例子就像这样：
        ```
        Chain PREROUTING (policy ACCEPT 2885K packets, 212M bytes)
         pkts bytes target     prot opt in     out     source               destination
        16   952 DNAT       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22345 to:192.168.123.2:22
        ## 这里因为涉及到自定义链，我就直接合并了。
        ```
        你会注意到，policy为什么是ACCEPT？我觉得是因为如果不给你规则，路由也不会帮你转发，所以大家都说ipv4的nat安全，原来是这个意思。
    - **POSTROUTING** 你是否想过，nat后的主机，是如何用路由器的ip进行通信的？
        这条链改写了对应目标的源ip地址和端口，然后再发出去。规则SNAT需要指定ip，但是在家庭环境中，ip通常是变化的，这时候神器MASQUERADE出现了，它可以动态的获取出口网卡的ip地址，把ip改写再发出去。至于出口怎么决定，那就是路由表的事情了。
        例子：
        ```
        Chain POSTROUTING (policy ACCEPT 804K packets, 60M bytes)
         pkts bytes target     prot opt in     out     source               destination
            0     0 MASQUERADE  all  --  *      ppp0    0.0.0.0/0            0.0.0.0/0
        ```
### 命令

iptables最被诟病的就是它的命令，那叫一个又臭又长，我永远记不得。

但是简单的查询命令还是很好记的。

```shell
iptables -t nat -nvL #看nat表的规则
iptables -nvL --line-numbers #看filter表的规则，filter默认可以省略；--line-numbers用于显示编号。

# 一些我常用的就一起放在这了
ip6tables -A INPUT -p udp --dport 26741 -j ACCEPT # ip6tables是用于控制ipv6的防火墙，我目前只接触了filter表，NPT还不会...
iptables -A INPUT -i wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o ppp0 -s 10.0.8.0/24 -j MASQUERADE --mode fullcone
```

-A是Append，-I是Insert，-D是Delete，据此可以精确的删除规则。

用行号也可以：`iptables -D INPUT 2`

## nftables + firewalld

nftables是一个新的netfilter工具，通常会和firewalld一起配合使用。对于移动设备来说有更好的可配置性。

这里就不手搓nft规则了，简单讲讲我用到的配置：

### 永久和非永久配置

firewalld在设置防火墙的时候，默认是临时配置立即生效。如果想要配置永久规则，加上`--permanent`参数即可，记得使用`firewall-cmd`重新加载规则生效。

### 启动

一行命令就好：

```shell
sudo systemctl enable --now nftables firewalld
```

这样，系统就为我们配置了一个默认的防火墙，默认所有的网卡会在public区域，现在只有22入站才被允许。

### 区域

你应该发现，新的防护墙工具多了一个新概念叫作区域，不同的网卡可以分配到不同的区域。

先来看看有什么区域？

```shell
sudo firewalld --list-all-zones
```

部分输出：

```
...

home 
  target: default
  ingress-priority: 0
  egress-priority: 0
  icmp-block-inversion: no
  interfaces: 
  sources: 
  services: dhcpv6-client mdns samba-client ssh
  ports: 
  protocols: 
  forward: yes
  masquerade: no
  forward-ports: 
  source-ports: 
  icmp-blocks: 
  rich rules: 

...

public (default, active)
  target: default
  ingress-priority: 0
  egress-priority: 0
  icmp-block-inversion: no
  interfaces: 
  sources: 
  services: dhcpv6-client ssh
  ports: 
  protocols: 
  forward: yes
  masquerade: no
  forward-ports: 
  source-ports: 
  icmp-blocks: 
  rich rules: 

trusted 
  target: ACCEPT
  ingress-priority: 0
  egress-priority: 0
  icmp-block-inversion: no
  interfaces: 
  sources: 
  services: 
  ports: 
  protocols: 
  forward: yes
  masquerade: no
  forward-ports: 
  source-ports: 
  icmp-blocks: 
  rich rules: 

...
```

如果设置了tun模式，你会发现它无法联网了。

### 将网卡分配到区域

#### 分配tun

我们使用firewalld来配置规则。

通过上面的输出可以知道，trusted区域是允许所有流量的，我们把Mihomo加到trusted区域：

```shell
firewall-cmd --zone=trusted --add-interface=Mihomo --permanent
sudo firewall-cmd --reload

## 验证
firewall-cmd --get-zone-of-interface=Mihomo ## 返回trusted
```

这里有个小坑，我加入之后发现还是不行，一看日志发现数据包全被丢弃了。折腾半天发现重启解决了，我：？？？

#### 分配wlan0

如果是便携的设备，我们会连接到不同的热点，有公用的也有家里的，家里可以开放多一点权限，而公用的则不需要。

这一部分由NetworkManager配置：

```shell
nmcli connection modify "SAST" connection.zone "home"

## 验证
sudo nmcli connection show SAST |grep connection.zone

## 返回
connection.zone:                        home
```

这样只有连接到指定的热点名称的时候，才会切换wlan0到home区域，其他都是public区域。

### 开放特定服务和端口

firewalld事先定义了一些服务需要的端口，可以在`/usr/lib/firewalld/services/`找到，这些配置文件以`xml`格式存储。

添加服务和端口的时候，别忘了指定当前区域。如果不指定，那么默认是在public区域添加规则的。

如果你需要的服务恰好在里面，就可以很方便的添加：

```shell
sudo firewall-cmd --zone=home --add-service=kdeconnect --permanent
sudo firewall-cmd --reload
```

如果这个端口是你自己定义的，可以这样子：

```shell
sudo firewall-cmd --add-port=8000/tcp --zone=home --permanent
sudo firewall-cmd --reload
```

然后查看：

```shell
sudo firewall-cmd --zone=home --list-all

## 输出
home (active)
  target: default
  ingress-priority: 0
  egress-priority: 0
  icmp-block-inversion: no
  interfaces: wlan0
  sources: 
  services: dhcpv6-client kdeconnect mdns samba-client ssh
  ports: 8000/tcp
  protocols: 
  forward: yes
  masquerade: no
  forward-ports: 
  source-ports: 
  icmp-blocks: 
  rich rules:
```

### 管理

> 别忘了加上--zone=！

- 删除端口：`--remove-port`
- 删除服务：`--remove-service`
- 列出端口：`--list-ports`
- 列出服务：`--list-services`

## 总结

目前来说个人主机拥抱firewalld + nftables更加合适，因为它们提供了更灵活的规则，也拥有更高效的性能。但是服务器上不建议安装firewalld，因为很多软件是直接通过添加nftables规则的，还有很大一部分老软件会添加iptables规则。当然nftables也做了兼容，`iptables-nft`这个包会把iptables类的指令自动翻译成nftables规则进行加载。此外，`iptables-translate`可以把iptables指令翻译成nftables，便于学习和迁移。

nftables是未来的防火墙！~~但是目前直接使用的真的太少了~~