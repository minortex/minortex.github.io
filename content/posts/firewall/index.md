+++
date = '2025-04-25T21:46:16+08:00'
draft = false
title = '那些防火墙的事情'
description = 'iptables&nftables&firewalld的世界！'
tags = ['Arch']
+++

## 前言

其实防火墙这玩意，我三年前就接触过。那时候在用iptables来配置路由器的`ipv6`转发，照着教程抄完了也不知所云。

如今过去了那么久，知识储备多了那么一点点，正好有需求，就重新了解了一下。


## iptables

iptables，这玩意算是个古董了，大概在21世纪初就有了。不过毕竟是老东西，现在大部分旧设备都是用的它，很多软件在修改防火墙规则的时候也只改它。

提起`iptables`，我们也许会想到五链四表，不过一般来说，知道`nat`和`filter`表就已经足够完成80%的工作了（`ipv4`），我在[archwiki的iptables](https://wiki.archlinuxcn.org/wiki/Iptables)章节翻到这张图，也许能够有助于理解：

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

1. **filter**表 最简单，也是默认的表。它只有`OUTPUT`，`INPUT`，`FORWARD`链。这几个顾名思义，分别是来源本机，目标本机，经过本机的数据包。
    一般来说，
    - **OUTPUT** 的默认规则是`ACCEPT`，也就是允许所有来源本机的数据包发出。
    - **INPUT** 的默认规则是`DROP`，也就是不允许外来的数据包访问本机。我们一般监听的端口需要配置例外的规则，否则就无法被访问。
    - **FORWARD* *也是`DROP`。默认不允许不同网络接口之间的数据包转发。想要转发不仅仅需要手动放行，还得开启内核的IP转发。
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

2. **nat**表 这个表有四条链，不过我一般只用其中的两条：`PREROUTING`和`POSTROUTING`，分别处理端口映射以及ip伪装。
    - **PREROUTING** 这一个链其实我接触得不多，因为基本都是在ui上面设置的。但是摸过SAST的RouterOS之后，那个ui配置起来就像是手搓`iptables`一样，我就马上理解了。
        一个例子就像这样：
        ```
        Chain PREROUTING (policy ACCEPT 2885K packets, 212M bytes)
         pkts bytes target     prot opt in     out     source               destination
        16   952 DNAT       tcp  --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:22345 to:192.168.123.2:22
        ## 这里因为涉及到自定义链，我就直接合并了。
        ```
        你会注意到，`policy`为什么是`ACCEPT`？我觉得是因为如果不给你规则，路由也不会帮你转发，所以大家都说`ipv4`的`nat`安全，原来是这个意思。
    - **POSTROUTING** 你是否想过，`nat`后的主机，是如何用路由器的ip进行通信的？
        这条链改写了对应目标的源ip地址和端口，然后再发出去。规则SNAT需要指定ip，但是在家庭环境中，ip通常是变化的，这时候神器`MASQUERADE`出现了，它可以动态的获取出口网卡的ip地址，把ip改写再发出去。至于出口怎么决定，那就是路由表的事情了。
        例子：
        ```
        Chain POSTROUTING (policy ACCEPT 804K packets, 60M bytes)
         pkts bytes target     prot opt in     out     source               destination
            0     0 MASQUERADE  all  --  *      ppp0    0.0.0.0/0            0.0.0.0/0
        ```
### 命令

`iptables`的命令非常的精简，看多了倒还不错，不过现在的风格倒变成自然语言了，像`ip`和`nft`之流。

```shell
iptables -t nat -nvL [CHAIN-NAME] #看nat表的规则,链名是可选的
iptables -nvL --line-numbers #看filter表的规则，filter默认可以省略；--line-numbers用于显示编号。
```

一些我常用的就一起放在这了：
```shell
ip6tables -A INPUT -p udp --dport 26741 -j ACCEPT # ip6tables是用于控制ipv6的防火墙，我目前只接触了filter表，NPT还不会...
iptables -A INPUT -i wg0 -j ACCEPT
iptables -A FORWARD -i wg0 -j ACCEPT
iptables -t nat -A POSTROUTING -o ppp0 -s 10.0.8.0/24 -j MASQUERADE --mode fullcone
```

`-A`是`Append`，`-I`是`Insert`，`-D`是`Delete`，据此可以精确的删除规则。

用行号也可以：`iptables -D INPUT 2`

### 补充

还有子链和其他表等其他内容，等到后面有时间再写吧。

## nftables + firewalld

`nftables`是一个新的`netfilter`工具，`firewalld`是RedHat开发的一个防火墙前端。`firewalld`的默认后端是`nft`，这两者一般来说会配合起来使用。

直接操作底层的`nft`命令对我来说还是有点困难，这里就简单讲讲他们的结合使用吧。

> 为什么选择firewalld而不是选择ufw呢？

`firewalld`对于动态网络（比如笔记本在不同的热点之间切换）有很好的适配，具体体现在与`NetworkManager`之间的配合，使得不同的热点能够应用在不同的区域中，后面会讲讲配置过程。

### 永久和非永久配置

`firewalld`在设置防火墙的时候，默认是临时配置立即生效。如果想要配置永久规则，加上`--permanent`参数即可，记得使用`firewall-cmd`重新加载规则生效。

### 启动

一行命令就好：

```shell
sudo systemctl enable --now nftables firewalld
```

这样，系统就为我们配置了一个默认的防火墙，默认所有的网卡会在`public`区域，现在只有22入站才被允许。

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

如果设置了`tun`模式，你会发现它无法联网了。

### 将网卡分配到区域

#### 分配tun

我们使用`firewalld`来配置规则。

通过上面的输出可以知道，`trusted`区域是允许所有流量的，我们把`Mihomo`加到`trusted`区域：

```shell
firewall-cmd --zone=trusted --add-interface=Mihomo --permanent
sudo firewall-cmd --reload

## 验证
firewall-cmd --get-zone-of-interface=Mihomo ## 返回trusted
```

这里有个小坑，我加入之后发现还是不行，一看日志发现数据包全被丢弃了。~~折腾半天发现重启解决了，我：？？？~~

> 真正的隐藏boss在后面！

[反向路径过滤](#rpfilter)

#### 分配wlan0

如果是便携的设备，我们会连接到不同的热点，有公用的也有家里的，家里可以开放多一点权限，而公用的则不需要。

这一部分由NetworkManager配置：

```shell
nmcli connection modify "SAST" connection.zone "home"

## 验证
sudo nmcli connection show SAST | grep connection.zone

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

### 反向路径过滤 {#rpfilter}

反向路径过滤，简称rpfilter。这一个功能在ipv4时代，是由内核实现的。在[内核文档](https://www.kernel.org/doc/Documentation/networking/ip-sysctl.txt)中是这么写的：

```
/proc/sys/net/ipv4/* Variables:

rp_filter - INTEGER
	0 - No source validation.
	1 - Strict mode as defined in RFC3704 Strict Reverse Path
	    Each incoming packet is tested against the FIB and if the interface
	    is not the best reverse path the packet check will fail.
	    By default failed packets are discarded.
	2 - Loose mode as defined in RFC3704 Loose Reverse Path
	    Each incoming packet's source address is also tested against the FIB
	    and if the source address is not reachable via any interface
	    the packet check will fail.

	Current recommended practice in RFC3704 is to enable strict mode
	to prevent IP spoofing from DDos attacks. If using asymmetric routing
	or other complicated routing, then loose mode is recommended.

	The max value from conf/{all,interface}/rp_filter is used
	when doing source validation on the {interface}.

	Default value is 0. Note that some distributions enable it
	in startup scripts.
```

顺带一提，`ip_forward`也是在这个地方配置的。

这里告诉我们，`0`禁用反向路径过滤，`1`开启严格的反向路径过滤（反向路径必须是最佳路由），`2`开启宽松的反向路径过滤（只要反向路径路由可达即可）。

默认是不开启反向过滤的，但是似乎防火墙会给每个网卡加上一个`2`？由于目前手上没有无防火墙的机器，暂时无法验证...

但是如果你装的是`firewalld`，默认的反向过滤是全部严格的。这时得到`/etc/firewalld/firewalld.conf`改成这样：

```ini
IPv6_rpfilter=loose
```

才能禁用反向路径过滤。由于`firewalld`在nft中配置的表是只读的，只能由它改写，所以去删掉它的规则或者尝试绕过都是没用的。~~别骂了别骂了~~

`Mihomo`会导致出现很多的`drop`数据包，其中一部分就是`rpfilter`引起的，日志类似这样：

```
5月 18 23:18:08 texsd-spin kernel: rpfilter_DROP: IN=Mihomo OUT= MAC= SRC=2a01:04f9:3081:4e4b:0000:0000:0000:0002 DST=fdfe:dcba:9876:0000:0000:0000:0000:0001 LEN=80 TC=0 HOPLIMIT=64 FLOWLBL=1037094 PROTO=TCP SPT=443 DPT=22000 WINDOW=64260 RES=0x00 ACK SYN URGP=0 
```

导致所有的`ipv6`能`ping`通但是无法访问，改成宽松后解决。

### 管理

#### 禁用日志

这是一个标准选项，所以不需要加`--permanent`。

我比较建议把日志调成`unicast`。否则如果你局域网中广播的设备很多的话，`journalctl`会被淹没。

```shell
sudo firewall-cmd --set-log-denied=unicast
```

#### 其他

我觉得`firewalld`的man page写得很清晰，去看它是一个很好的选择。

```shell
man 1 firewall-cmd
```

## 总结

目前来说个人主机拥抱firewalld + nftables更加合适，因为它们提供了更灵活的规则，也拥有更高效的性能。但是服务器上不建议安装firewalld，因为很多软件是直接通过添加nftables规则的，还有很大一部分老软件会添加iptables规则。当然nftables也做了兼容，`iptables-nft`这个包会把iptables类的指令自动翻译成nftables规则进行加载。此外，`iptables-translate`可以把iptables指令翻译成nftables，便于学习和迁移。

nftables是未来的防火墙！~~但是目前直接使用的真的太少了~~