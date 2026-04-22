+++
date = '2026-04-22T23:00:09+08:00'
draft = false
title = 'UPS 折腾记'
+++

## 前言

最近我突然有了两台 ups 的管理权，一台工作室的 APC Smart-UPS SPRM1K，另一台家里的 APC BACK-UPS BK650。由于手边只有前者，先更新前者的研究成果，后者择日更新。

管理带通信的 UPS 的配套软件其实就两种，这里主要讲解 NUT，而 apcupsd 配置很简单，而且也可以作为 NUT 的驱动，这里不再详述。

## NUT 的配置

要理解 NUT，首先要明白几个概念：driver、monitor(client)、server（可选），三个服务都要单独启用。

### 驱动层

driver 其实就是对接各种奇奇怪怪 ups 的，这里我这两台一个用的是串口（apcsmart）,另一个是 usbhid-ups，这里主要是以前者讲解的。

配置 ups 驱动：
```bash
## /etc/nut/ups.conf 
## 根据需要填写,可用nut-scanner -U获取驱动
[ups] 
    driver = apcsmart 
    port = /dev/ups 
    cable = 940-0024 
    ignorelb # 手动指定阈值
    override.battery.charge.low = 70 
    override.battery.runtime.low = 20
```

启动服务：`upsdrvctl start`。

这里有个小插曲，串口可能提示权限不够：
```bash
root@pve:/etc/nut# upsdrvctl start
Network UPS Tools - UPS driver controller 2.8.1
Network UPS Tools - Generic HID driver 0.52 (2.8.1)
USB communication driver (libusb 1.0) 0.46
libusb1: Could not open any HID devices: insufficient permissions on everything
No matching HID UPS found
upsnotify: notify about state 4 with libsystemd: was requested, but not running as a service unit now, will not spam more about it
upsnotify: failed to notify about state 4: no notification tech defined, will not spam more about it
Driver failed to start (exit status=1)
```

用 udev 规则，给 nut 权限：
```bash
cat << 'EOF' > /etc/udev/rules.d/99-nut-ups.rules
SUBSYSTEM=="usb", ATTR{idVendor}=="051d", ATTR{idProduct}=="0002", MODE="0660", GROUP="nut"
EOF
udevadm control --reload-rules
udevadm trigger
```

再次启动：`upsdrvctl start`

### 服务层

nut 其实 c/s 架构很分明，如果只有一台机子，也得启动一个服务器。但是这也为拓展型带来了便利。

如果你只有一台机子，用 standalone 即可，作为“吹哨人”，用 netserver，接收命令关闭自己的机器，用 netclient。

我这里改成服务器：
```bash
## /etc/nut/nut.conf
# 服务器模式
MODE=netserver

## /etc/nut/upsd.conf
# 加上这一行，给局域网里面的设备提供服务
# 如果你是pve而且路由器不接ups，建议自己建一个
# 自定义交换机
LISTEN 0.0.0.0 3493
```

配置用户，monuser 最好有，因为群晖用这个而且不能更改。
```bash
## /etc/nut/upsd.users
[monuser] 
    password = secret 
    upsmon slave 
[admin] 
    password = <your_password>
    upsmon master 
    actions = SET
    instcmds = ALL
```

启动服务：`systemctl enable --now nut-server`

### 客户端/监视层

配置 nut-monitor 以便自动关机：
```bash
MONITOR ups@localhost 1 monuser secret master # slave也可以，后文（关机过程）讲
```

你可以看到，最下面有个`shutdown`命令，这个只要 monitor 服务启动了，在遇到低电量阈值的时候，就一定会执行的。

启动服务：`systemctl enable --now nut-monitor`


## 关机过程

1. 断开电源，nut 检测到电池供电，其他客户端收到信号。

对于群晖这种设置了 upssched 的机子，他可以在检测到断电之后的一定时间开启安全模式（umount 所有分区，只保留必须的 nut 监听服务和关机逻辑），如果在此期间市电恢复，重新检测到后会进行自动重启。

2. 电池到达所给定的阈值（电量/剩余事件/电池供电时间），发出警告信号。

这时候服务器自己会开始关机（执行 shutdown），其他客户端会收到信号，开始进行关机。

在关机最后一刻，有一个有意思的脚本想和大家分享。

这个脚本是 systemd 在关机的最后时刻执行的，位于`/usr/lib/systemd/system-shutdown/nutshutdown`。我们来看看他的结构：

```bash
#!/bin/sh

# This script requires both nut-server (drivers)
# and nut-client (upsmon) to be present locally
# and on mounted filesystems
[ -x "/sbin/upsmon" ] && [ -x "/sbin/upsdrvctl" ] || exit

if /sbin/upsmon -K >/dev/null 2>&1; then
  # The argument may be anything compatible with sleep
  # (not necessarily a non-negative integer)
  wait_delay="`/bin/sed -ne 's#^ *POWEROFF_WAIT= *\(.*\)$#\1#p' /etc/nut/nut.conf`" || wait_delay=""

  /sbin/upsdrvctl shutdown

  if [ -n "$wait_delay" ] ; then
    /bin/sleep $wait_delay
    # We need to pass --force twice here to bypass systemd and execute the
    # reboot directly ourself.
    /bin/systemctl reboot --force --force
  fi
fi

exit 0
```

可以注意到经过一系列的判断，如果是真的断电（发出警告后）`upsmon -K`会返回 1，那么就会使用`upsdrvctl shutdown`来命令 ups 在一定时间后断电。

但是这时候，系统已经解除了所有的磁盘 rw 的挂载，执行完脚本的下一步其实就是给 acpi 电源发送 S5 信号并断电，速度很快，其实断不断电也无所谓了。

一般的断电延时 20s 绰绰有余。至于断电时间的设置，高级的 ups 可以设置（见后文`upsrw`），普通的不可以。

所以如果这是最后一个“吹哨人”执行的 killpower（让 ups 等会断电），最好关闭的时候要尽量比 slave 关得晚，否则就得尽量延长 ups 的延迟时间。

## 常用命令

### upscmd：执行一些驱动预设的指令

```bash
root@SAST-Docker:~# upscmd -l ups
Instant commands supported on UPS [ups]:

bypass.start - Put the UPS in bypass mode
bypass.stop - Take the UPS out of bypass mode
load.off - Turn off the load immediately
load.on - Turn on the load immediately
shutdown.return - Turn off the load and return when power is back
shutdown.stayoff - Turn off the load and remain off
test.battery.start - Start a battery test
test.battery.stop - Stop the battery test
test.failure.start - Start a simulated power failure
test.panel.start - Start testing the UPS pane
```

### upsrw：用于读写 eeprom 的

使用：
```bash
upsrw -l <upsname>
```

控制响声、复电延迟启动、复电要求电池水平、关电延迟停止 ups。

比如我们工作室的 SPRM1K 可以设置的东西就很多，还贴心的用了 enum 告诉你：
```bash
root@SAST-Docker:/etc/nut# upsrw -l ups
[battery.alarm.threshold]
Battery alarm threshold
Type: ENUM NUMBER
Option: "0" SELECTED
Option: "T"
Option: "L"
Option: "N"

[battery.charge.restart]
Minimum battery level for restart after power off (percent)
Type: ENUM NUMBER
Option: "00"
Option: "15"
Option: "50" SELECTED
Option: "90"

[battery.date]
Battery change date
Type: STRING
Maximum length: 8
Value: 12/30/25

[input.transfer.high]
High voltage transfer point (V)
Type: ENUM NUMBER
Option: "231"
Option: "242"
Option: "253"
Option: "264" SELECTED

[input.transfer.low]
Low voltage transfer point (V)
Type: ENUM NUMBER
Option: "187"
Option: "176" SELECTED
Option: "165"
Option: "154"

[output.voltage.nominal]
Nominal output voltage (V)
Type: ENUM NUMBER
Option: "220" SELECTED
Option: "230"
Option: "240"

[ups.delay.shutdown]
Interval to wait after shutdown with delay command (seconds)
Type: ENUM NUMBER
Option: "020"
Option: "180"
Option: "300" SELECTED
Option: "600"

[ups.delay.start]
Interval to wait before (re)starting the load (seconds)
Type: ENUM NUMBER
Option: "000"
Option: "060" SELECTED
Option: "180"
Option: "300"

[ups.id]
UPS system identifier
Type: STRING
Maximum length: 8
Value: UPS_IDEN

[ups.test.interval]
Interval between self tests (seconds)
Type: ENUM NUMBER
Option: "1209600" SELECTED
Option: "604800"
Option: "0"
```

我在这里改了`ups.delay.shutdown`，原因很尴尬，esxi 只支持客户端模式的 nut，服务端只能用一台虚拟机来实现。那么希望在服务端发出 killpower 后，还能等待 esxi 关闭，这个时间就不可避免的延长。

---

我还改了`ups.delay.start`，这个参数很有意思，他没有注释，根据字面意思理解，应该是断电之后延迟启动吧？

但是不是这个意思。他指的是如果你发出了 killpower 的命令后中途来电，他断电后，应该在多少秒后开机？

我觉得这句话得细品。

对于我这台 SPRM1K 来说，发送 killpower 指令后，首先是等待`ups.delay.shutdown`的时间，然后切断输出，然后过了硬编码的 1 分钟，关闭 ups 自己。

那么就有几种情况：

- 在等待`ups.delay.shutdown`时，市电恢复。
- 在等待硬编码的 1 分钟的时候，市电恢复。
- ups 关机之后，市电恢复。

这三种情况中前两者会等待`ups.delay.start`的时间，最后一种不会等待，初始化之后直接开机。

我想应该是[这篇文章](https://www.chiphell.com/forum.php?mod=viewthread&tid=2605539&extra=page%3D1&mobile=no)里面提到的问题，作者说如果断电的时间太短，那么 After AC Loss 就算设置为 Power On，也不一定能自动开机。所以才有这么一个选项。

> btw: 我并不太赞同链接里面的方案，复杂度太高了很难维护，其实里面很多东西厂家已经做好了。（排除 UPS 不够高端的问题，这个等我回去测试一下我的 BK650 再下定论）

##  奇怪的 bug

根据 `man 8 usbhid-ups` 中的说明，可以直接在 ups.conf 里面配置 `allow_killpower` 来在启动的时候生效，但是[这个 issue](https://github.com/networkupstools/nut/issues/2605) 说 `allow_killpower` 在 2.8.3 之后才修复启动的时候硬编码的 0 会覆盖回去的问题，然而 trixie 是 2.8.1，就很难受。

能用点 hack 的办法，启动的时候修改。

```bash
systemctl edit nut-driver@ups.service
# 写入
[Service]
# 延迟几秒确保驱动已经完全初始化
ExecStartPost=/bin/sh -c "sleep 5 && /usr/bin/upsrw -s driver.flag.allow_killpower=1 -u admin -p <你的密码> ups"
```

但是这台设备不再身边，所以我还是选择了保守的 apcupsd 方案关机+nut 桥接给群晖，这篇文章之后还会更新的。
