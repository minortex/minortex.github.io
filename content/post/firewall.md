+++
date = '2025-04-25T21:46:16+08:00'
draft = false
title = '那些防火墙的事情--iptables&nftables&firewalld'
description = '折腾防火墙有感'
tags = ['Arch']
+++

## 前言

其实防火墙这玩意，我三年前就有所耳闻。那时候在用iptables来配置路由器的虚拟组网规则，就被弄得头昏脑转。

如今过去了那么久，知识储备多了那么一点点，正好有需求，就重新了解了一下。

## 简单介绍

### iptables

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

1. filter表最简单，也是默认的表。它只有INPUT，OUTPUT，FORWARD链。这几个顾名思义，分别是进入内核

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

#### 啥表啥链？

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
#### 命令

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

### nftables

## 设置一个简单的防火墙！

## 让信任的网络加入区域

## 给tun专门分配一个规则