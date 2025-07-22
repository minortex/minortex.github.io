---
title: "Immortalwrt折腾日记"
date: 2025-07-19T14:15:52+08:00
draft: false
---

## 前言

早年接触过wrt，但是那时候用的还是7621的设备，使用mtk开源驱动后信号会变得非常差，闭源驱动会出现死机的情况。如今入手7981的路由器，终于可以研究一下配置以及日用了。

## IPv6上网

想让路由器下面的设备上网，无非就这么几种方式：

- PD(Prefix Delegation): 上级下发ipv6的/56或者/60的前缀，可以自己划分子网使用。

- NDP Proxy: 上级通过SLAAC分配ipv6地址，只开启了O标志，获得一个/64的地址的时候使用。

- NPTv6: 你有多条宽带，需要做负载均衡。

- NAPTv6: 上级只允许通过DHCPv6获取地址（一般是学校之类需要强管理或者认证的场景），获得一个/128的地址。

> 欸，这时候有人问，/128不是也可以使用ndp代理吗？

理论上确实可行，但是很多DHCPv6服务器并不支持代理获取，下面这个`tcpdump`结果说明了这一点：

```
root@ImmortalWrt:~# tcpdump -i eth1 udp port 546 or udp port 547
tcpdump: verbose output suppressed, use -v[v]... for full protocol decode
listening on eth1, link-type EN10MB (Ethernet), snapshot length 262144 bytes
15:03:40.878466 IP6 fe80::aaaa.546 > ff02::1:2.547: dhcp6 solicit
15:03:40.880132 IP6 fe80::bbbb.547 > fe80::aaaa.546: dhcp6 advertise
15:03:42.905527 IP6 fe80::aaaa.546 > ff02::1:2.547: dhcp6 request
15:03:42.908198 IP6 fe80::bbbb.547 > fe80::aaaa.546: dhcp6 reply
15:04:39.149414 IP6 ImmortalWrt.lan.547 > ff05::1:3.547: dhcp6 relay-fwd
15:04:40.188299 IP6 ImmortalWrt.lan.547 > ff05::1:3.547: dhcp6 relay-fwd
15:04:42.189520 IP6 ImmortalWrt.lan.547 > ff05::1:3.547: dhcp6 relay-fwd
```

使用ff05的广播根本就不回你。

### NDP代理

在路由器上面这样设置：

1. `wan6`

DHCP服务器-IPv6设置：

- 指定的主接口（打勾）
- RA服务：中继模式
- DHCPv6服务：中继模式
- NDP代理：中继模式
- 学习路由（打勾）

2. `br-lan`

DHCP服务器-IPv6设置：

- 指定的主接口（不允许选择了）
- RA服务：中继模式
- DHCPv6服务：中继模式
- NDP代理：中继模式
- 学习路由（打勾）
- NDP代理从属设备（打勾）

这样操作相当于透传了上级路由的RA（路由器通告），上面怎么样p配置，你的局域网设备就是怎么样的，没法更改，当然如果你能获取到/64的前缀，那么下面的设备一般来说也没有问题。

### 前缀下发

这当然是最推荐的方式了。

在现代的类wrt上面，使用`PPPoE`在wan口上拨号，同时在高级设置里面开启获取IPv6地址为自动，如果你的ISP有IPv6支持，会自动产生一个虚拟动态接口`wan_6`。一般这个接口能获取到一个/64的地址和IPv6-PD，这是我们能分配的前提条件。

我的配置是这样的：

- RA服务：服务器模式
- DHCPv6服务： 已禁用
- NDP代理：已禁用

#### 使用简单的路由通告配置

在家用的小型网络中，完全可以做到不架设DHCPv6服务器，只通过RA就可以实现基本的配置了，请看这个包：

```shell
root@t-router:~# tcpdump -nvi br-lan ip6[40] == 134
tcpdump: listening on br-lan, link-type EN10MB (Ethernet), snapshot length 262144 bytes
10:35:28.476086 IP6 (flowlabel 0x4f20d, hlim 255, next-header ICMPv6 (58) payload length: 144) fe80::aaaa > ff02::1: [icmp6 sum ok] ICMP6, router advertisement, length 144
        hop limit 64, Flags [none], pref medium, router lifetime 1800s, reachable time 0ms, retrans timer 0ms
          source link-address option (1), length 8 (1): aa:aa:aa:aa:aa:aa
          mtu option (5), length 8 (1):  1492
          prefix info option (3), length 32 (4): 2409:xxxx:xxxx:13a::/64, Flags [onlink, auto], valid time 5400s, pref. time 2700s
          route info option (24), length 24 (3):  2409:xxxx:xxxx:130::/60, pref=medium, lifetime=1800s
          rdnss option (25), length 24 (3):  lifetime 1800s, addr: 2409:xxxx:xxxx:13a::1
          dnssl option (31), length 24 (3):  lifetime 1800s, domain(s): lan.
          advertisement interval option (7), length 8 (1):  600000ms
```

几个重要的信息全部体现在这个里面了：
1. 地址：

没有配置Flag，说明是Stateless，设备自己生成配置，是否开启RFC4941（隐私地址）由设备自己决定。

不过无状态自动配置要求地址的前缀必须是/64以上的，否则会破坏这一行为。

2. 网关：

规定路由通告必须使用fe80开头的本地地址来发送路由通告，只要路由存活时间不为0，那么下面的设备就可以使用这个地址当做默认路由。

2. DNS

- 使用`rdnss option`来配置DNS。

Windows在大概1709这个版本之后支持`rdnss`了，其他系统应该都支持吧？

- 使用`dnssl option`来配置DNS搜索域。

这个感觉意义不大，因为使用DHCPv6才会解析主机名.lan，这个使用DHCPv4已经足够了。

不过注意不要设置成.local，因为mDNS会使用这个域名导致冲突，而mDNS会自动发现的。

如果你有/60的前缀，可以在高级设置里面填写IPv6分配提示，4位正好可以填一位16进制数，`0-f`，以此类推/56可以填两位，从而划分多个IPv6子网。

像我就是填了`a`。

#### 使用DHCPv6

如果设备比较老，可能还是得开启DHCPv6，办法就是把DHCPv6服务设置成服务器模式。

这时候就可以在RA设置里面的RA标记开启几个选项，让设备使用DHCPv6服务，这里配置项目已经讲解得很明白，我就不多说了，直接贴上来：

```shell
RA 标记

受管配置 (M)
受管地址配置 (M) 标记表明可以通过 DHCPv6 获取 IPv6 地址。
其他配置 (O)
其他配置 (O) 标记表明其他信息，如 DNS 服务器，可以通过 DHCPv6 获得。
移动家乡代理 (H)
移动 IPv6 家乡代理 (H) 标记表明该设备在此链路上还充当移动 IPv6 家乡代理。
```

DHCPv6还可以配置别的一大堆东西，比如NTP之类的，但是v4已经干了这一堆了，我觉得除非v4被完全替代，否则现阶段完全没有理由用。

### NPTv6/NAPTv6

如果有多条宽带并且都有PD，你可以内网分配一个ULA地址，然后在路由的时候进行前缀转换，这也是我们学校社团网络的做法。这种办法对于性能要求的不高，本身也算符合IPv6的实践。

---

但是如果你只能通过DHCPv6配到一个/128的地址，那就没办法了，直接用动态地址伪装（masquerade）吧，一般的路由器都不会有硬件加速，所以网速不太行，但是如果是IPv6刚需也没有别的办法了。

我有点懒得写了，想用的可以参考[南航校园网OpenWRT配置IPv6 NAT6](https://blog.creedowl.com/posts/ipv6_and_nat6_in_nuaa/)，我自己在学校里面配的过程已经忘记了，不过跟这个应该大差不差。

### 邻居协议

IPv6相比v4的b就是不同，就是邻居协议取代ARP，RA实现了DHCP的基本功能。

路由器和客户端使用NS（Neighbour Solicitation）和NA（Neighbour Advertisement）来检测地址冲突，探测别的设备。

一个SLAAC的过程具体是这样：

1. 连接到网络，先生成一个地址，用`::`发送到这个地址，看自己生成的`fe80::/16`有没有冲突，没有就使用。
2. 向`ff02::`发送RS，寻找路由器。
3. 路由器默认会每隔几分钟发送RA，接收到RS后，会尽快回复RA消息。
4. 客户端自己生成一个全球唯一的可路由地址，然后再看有没有冲突，没冲突就开始使用这个地址上网。