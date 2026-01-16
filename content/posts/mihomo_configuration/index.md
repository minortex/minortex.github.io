+++
date = '2026-01-06T10:05:49+08:00'
draft = true
title = 'mihomo裸核配置不完全指北'
+++

之前配置了很多，形成了一套自洽的规则，但是回头看根本没看懂自己当时写的什么，所以还是记录一下。

## fake-ip or redir-host

这两者究竟用什么，大家总是争论不休。

- fake-ip 会使得 DNS 缓存全部变成 fake-ip，意味着你每次重启 mihomo 的时候，如果缓存没有清除，那么就没法上网。在我早期使用时，甚至还经常出现睡眠唤醒后无法上网的问题，不知道现在解决了没有。
- fake-ip 使得 `dig/nslookup` 废了，而我使用这些工具频率还挺高。当然也可以打补丁，比如对国内站使用 `fake-ip-filter`，但是国外站还是不可能。

这么听上去，那么 redir-host 似乎不错？非也，这玩意比 fake-ip 历史还早，也曾经出过很多问题，但是现在通过一些手段续上命了。

- redir-host 要求得到域名的时候必须进行解析 DNS，如果你的 DNS 没有配好的话，很容易导致 DNS 泄露，相对而言，fake-ip 的 DNS 配置门槛就小得多，无脑加 `no-resolve` 基本都解决问题。
- redir-host 早期没法实现多个域名指向同一个 IP 的情况，尤其对于 UDP 包。现在 mihomo 强大的 sniffer 缓解了这个问题，但是只是补丁，可能在第一个包上面会剧烈抖动，对于更复杂的包可能也会出现嗅探失败的情况。

两种技术，没有绝对优势，任君选择。看你是要真实的国外 ip，还是更好的兼容性和性能。

## 全局

懒得介绍咯，看看就行：

```yaml
# 设备自定义配置
mode: rule
mixed-port: 7890
allow-lan: false # 如果要开启，强烈建议使用防火墙！
#bind-address: '*'
log-level: warning
ipv6: true
unified-delay: true

secret: '<your-secret>'
external-controller: 127.0.0.1:9099
external-ui: "<your-board-path>"
external-controller-cors:
  allow-private-network: true
  allow-origins:
  - 'localhost:9099'

experimental:
  dialer-ip4p-convert: true # 啊...ip4p没什么用，支持的太少了

profile:
  store-selected: true
  store-fake-ip: true # 存储 fake-ip 一定要开啊，你也不想重启mihomo断网吧？

```

## tun 

对于追求体验的人来说，绝对逃不掉 tun 的，因为系统/socks代理毕竟不是所有东西都走。


```yaml
tun:
  enable: true
  dns-hijack:
  - any:53
  auto-detect-interface: true
  auto-route: true
  device: Mihomo
  mtu: 1500
  stack: system # 出现问题就改 gvisor ，但是 system 的性能最高
  strict-route: true # 开启多宿主的时候，就开这个
  exclude-interface:
    - Tailscale
```

## DNS 和规则

有一句老话：

> “不要玩弄 DNS，否则你就会被 DNS 玩弄。” 

这是真的，我有时候睡不着就在想我的分流规则是怎么匹配的。

### fake-ip 

#### 复杂版本（支持小众国内网站）

为了获取小众域名的 ip 从而通过 ip 正确分流，用远程服务器解析得到 ip，那么 DNS 就只能复杂点了。

- 我希望把所有不是国内的东西全部打到 `MATCH`，就必须让 geosite:!cn 的 DNS 解析用代理服务器打到谷歌，从而避免泄露。
- 由于使用的 `proxy-providers`，在获取订阅的时候会遇到解析走代理 DNS - 代理列表为空的死循环，所以手动加入国内的 DOH。
- 因为遵守规则就得配 `proxy-server-nameserver`，导致又多出了一长串。

```yaml
dns:
  listen: :1053
  enable: true
  ipv6: true
  enhanced-mode: fake-ip
  fake-ip-filter:
    - 'geosite:cn,private,connectivity-check'
  default-nameserver:
    - 119.29.29.29
    - 223.5.5.5
  direct-nameserver: #让走直连的cdn的规则用国内dns
    - https://doh.pub/dns-query#ecs=<your-real-ip-range>
    - https://dns.alidns.com/dns-query#ecs=<your-real-ip-range> 
  respect-rules: true # 遵守规则，把googledns发给远端，远端用googledns来解析，然后返回ip
  nameserver:
    - https://dns.google/dns-query
  nameserver-policy:
    '<your-airport-sub-url>': # 防止死锁，让小众域名走国内dns获取ip（订阅不走proxy-server-nameserver），以便开始。
      - https://doh.pub/dns-query
  proxy-server-nameserver: # 不配不能远程解析dns
      - https://dns.alidns.com/dns-query#ecs=<your-real-ip-range> 
      - https://doh.pub/dns-query#ecs=<your-real-ip-range>  # 用于cdn优化
            

rules:
  - GEOSITE,CN,DIRECT
  - GEOIP,LAN,DIRECT,no-resolve
  - GEOIP,CN,DIRECT # 这一个是为小众网站准备的
  - MATCH,select
```

#### 简单版本

这个版本不支持国内小众网站，好处就是配置清晰明了。

~~不好意思，ns多就可以为所欲为~~

```yaml
dns:
  listen: :1053
  enable: true
  ipv6: true
  enhanced-mode: fake-ip
  default-nameserver:
    - 119.29.29.29
    - 223.5.5.5
  nameserver:
    - tls://8.8.8.8:853
    - tls://8.8.4.4:853
    - tls://dns.alidns.com
    - tls://223.5.5.5
    - tls://223.6.6.6
    - tls://dot.pub
    - tls://1.12.12.12
    - tls://120.53.53.53
    - https://cloudflare-dns.com/dns-query
    - https://dns.google/dns-query
    - https://8.8.8.8/dns-query
    - https://8.8.4.4/dns-query
    - https://dns.alidns.com/dns-query
    - https://223.5.5.5/dns-query
    - https://223.6.6.6/dns-query
    - https://doh.pub/dns-query
    - https://1.12.12.12/dns-query
    - https://120.53.53.53/dns-query

rules:
  - GEOSITE,CN,DIRECT
  - GEOIP,LAN,DIRECT,no-resolve
  - GEOIP,CN,DIRECT,no-resolve
  - MATCH,select
```

### redir-host

redir-host 的思路其实跟 fake-ip 类似，既然都折腾 redir-host，就用复杂那一套吧。

相比 fake-ip，少了 fake-ip-filter，多了 sniffer 。

- 后面研究了下用 `direct-nameserver` 可以直接在 `rules` 里面写更统一，所以 `nameserver-policy` 只留防死锁规则了。

```yaml
dns:
  listen: :1053
  enable: true
  ipv6: true
  use-system-hosts: true
  enhanced-mode: redir-host
  default-nameserver:
    - 119.29.29.29
    - 223.5.5.5
  direct-nameserver: #让走直连的cdn的规则用国内dns
    - https://doh.pub/dns-query#ecs=<your-real-ip-range>
    - https://dns.alidns.com/dns-query#ecs=<your-real-ip-range>
  proxy-server-nameserver:
    - system
    # 如果系统dns污染，才用doh。使用system dns对三网bgp更加友好。
    # - https://doh.pub/dns-query#ecs=<your-real-ip-range>
    # - https://dns.alidns.com/dns-query#ecs=<your-real-ip-range>
  respect-rules: true # dns遵守路由规则，让代理服务器帮我们问谷歌。
  nameserver:
    - https://dns.google/dns-query # 为什么只用google？因为是最全的dns。但是不能直连是一大缺点，也就是导致死锁的产生。
  nameserver-policy:
    '<your-airport-sub-url>': # 防止死锁，让小众域名走国内dns获取ip（订阅不走proxy-server-nameserver），才能有代理服务器的配置文件。
      - https://doh.pub/dns-query

sniffer:
  enable: true
  sniff:
    HTTP:
      ports: [80, 8080-8880]
      override-destination: true
    TLS:
      ports: [443, 8443]
    QUIC:
      ports: [443, 8443]
  skip-domain:
    - "Mijia Cloud"
    - "+.push.apple.com"

rules: # 非常简单，有嗅探器的存在无需GEOSITE,CN
  - GEOSITE,CN,DIRECT
  - GEOIP,LAN,DIRECT
  - GEOIP,CN,DIRECT
  - MATCH,select
```

### 服务器上使用

上面讲完的是你在本地的配置，这时候一般需要外部数据库的支持，如果你是通过包管理器安装的，可以直接引入不需要链接。

```yaml
geodata-loader: standard
geo-auto-update: true
geox-url:
  geoip: "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geoip.dat"
  geosite: "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/geosite.dat"
  mmdb: "https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/country.mmdb"
  asn: "https://github.com/xishang0128/geoip/releases/download/latest/GeoLite2-ASN.mmdb"
```

如果你是想丢两个文件到服务器上面，然后直接 `mihomo -f <file>` 启动的话，就不推荐这么用了，硬编码规则会爽很多。

我搓了一个模板，要用的时候替换 proxies 和 secret 就行。

[gist](https://gist.github.com/minortex/9b2fb8fe6b2a61477558844bcf65fd62)

## 代理分组

按照机场和地区分组，地区自动选择，机场手动选择。

```yaml
proxy-groups:
  - name: "select"
    type: "select"
    proxies:
      - "日本-自动选择"
      - "新加坡-自动选择"
      - "provider_A"
      - "provider_B"

  - name: 日本-自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 80
    use:
      - "provider_A"
    filter: "(?i)日本|JP|Japan" # 自动正则筛选所有机场中的日本节点

  - name: 新加坡-自动选择
    type: url-test
    url: http://www.gstatic.com/generate_204
    interval: 300
    tolerance: 80
    use:
          - "provider_A"
    filter: "(?i)新加坡|SG|Singapore"

# 付费机场

  - name: "A" 
    type: "select"
    use:
      - "provider_A"

  - name: "B"
    type: "select"
    use:
      - "provider_B"

# 免费机场
  - name: "free"
    type: "select"
    lazy: true
    use:
      - "provider_C"
      - "provider_D"
      - "provider_E"
```

然后引入代理提供商：

```yaml
proxy-providers:
  "provider_A":
    type: http
    url: "<your_sub_url>"
    interval: 600
    # proxy: select # 代理更新订阅
    path: ./provide/provider_A.yml
    health-check:
      enable: true
      url: https://cp.cloudflare.com/generate_204
      interval: 300
      
  # ...
```

注意，引入代理提供商的节点，测速是在提供商的 `health-check` 中配置的，`proxy-group` 只是引用了它的结果而已。

如果你是使用的 `proxies:`，那么测速就是在 `proxy-group` 里面配置的，不要搞混了。