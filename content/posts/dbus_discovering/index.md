+++
date = '2025-11-21T17:56:21+08:00'
draft = false
title = 'Dbus 探索'
+++

## 前言

之前想使用 `syfs` 监听电量变化失败，原因是 `sysfs` 不支持 `epoll` 之类的高级特性，所以还得隔几秒轮询，这对于精确度要求高的我来说是没法接受的，所以我不得不望向一个很熟悉但是陌生的东西————`Dbus`。

## 概念

感觉 `Dbus` 是有点点像 `MQTT`，你看 `broker` 都出来了，都有订阅这一说法，但是又有点不同。

- **总线**: 包括系统总线和用户总线。前者可以报告系统状态，硬件上的状态（正是我们需要的）；后者则在 `KDE` 的通知和特效之类上面大量使用，比如录屏的时候静音之类。
- **总线名称**: 一个跟 `Dbus` 有关的服务启动了，这个服务下面提供的各种对象，全都是挂在这个总线名称下的。
- **对象路径**: 服务提供的某些功能/实例，有点像 `unix` 的路径但是完全不一样，组织成面向对象的层次结构。
- **接口名称**: 一个服务可以有多个接口，在不同的接口名称定义对象提供的方法、属性和信号。
    - **方法**: 客户端向服务端发起的同步请求，要求服务执行请求/获取状态然后返回请求。
    - **属性**: 客户端向服务端可以获取到的状态。
    - **信号**: 服务向总线上面发送通知，告知感兴趣的客户端某个事件发生了。
- **订阅**: 客户端告诉总线对服务上面的某个对象的某个信号感兴趣。

`systemd` 和 `Dbus` 集成挺好的，可以监听某个总线上面的连接，如果客户端发出了请求但是服务没有启动，那么就会自动启动服务。这就像普通的服务上面的 `socket` 按需启动一样，也是把这套思路应用到了 `Dbus` 上面。

一般来说约定名字和对象路径中间的 `.` 和 `/` 对应，但是当然可以不遵守。

客户端可以手动向服务查询，对于用户，可以手动通过命令行获取信息；也可以由服务通过信号推送得到信息，这样就避免轮询造成的性能开销。

## 命令行使用

`systemd` 的 `busctl` 比较好理解，以这个工具为例。

`busctl` 无非就那几个参数，总线名称，对象路径，接口名称，然后按需调用/获取对应的对象。

### 自省

```shell
busctl introspect <busName> <path>
```

如果这个路径下的对象允许被自省的话，比如说 `UPower`：

```shell
❯ busctl introspect org.freedesktop.UPower /org/freedesktop/UPower
NAME                                TYPE      SIGNATURE RESULT/VALUE FLAGS       
org.freedesktop.DBus.Introspectable interface -         -            -           
.Introspect                         method    -         s            -           
org.freedesktop.DBus.Peer           interface -         -            -           
.GetMachineId                       method    -         s            -           
.Ping                               method    -         -            -           
org.freedesktop.DBus.Properties     interface -         -            -           
.Get                                method    ss        v            -           
.GetAll                             method    s         a{sv}        -           
.Set                                method    ssv       -            -           
.PropertiesChanged                  signal    sa{sv}as  -            -           
org.freedesktop.UPower              interface -         -            -           
.EnumerateDevices                   method    -         ao           -           
.GetCriticalAction                  method    -         s            -           
.GetDisplayDevice                   method    -         o            -           
.DaemonVersion                      property  s         "1.90.10"    emits-change
.LidIsClosed                        property  b         false        emits-change
.LidIsPresent                       property  b         true         emits-change
.OnBattery                          property  b         false        emits-change
.DeviceAdded                        signal    o         -            -           
.DeviceRemoved                      signal    o         -            -           
```

### 调用方法

那么显而易见了，直接调用：

```shell
busctl call <busName> <path> <interface> <object> [param]
```

得是 `method` 才能被调用，有的方法需要参数才能调用。

### 属性

属性既可以获取，在有权限的情况下可以设置。

```shell
busctl get-property <busName> <path> <interface> <object>
busctl set-property <busName> <path> <interface> <object>
```

### 签名

获取对象或者调用方法传参的时候，要求签名匹配。这里其实是一些数据类型，根据对应的英文简称：

- `s`: 字符串
- `b`: 布尔
- `i`: 整形
- `u`: 无符号整形
- `d`: 双精度
- `(a)o`: （数组式的）对象路径，用于查看其他对象。

传入参数是这样的，先输入类型，然后跟上你的数据，比如：

`s "hello" i 32`

### 简单的电量检测小工具

让 Gemini 用 QT 写了一个简单的电量监测系统，仅用于我这一台 chromebook：

[BatteryService](https://github.com/minortex/BatteryService)