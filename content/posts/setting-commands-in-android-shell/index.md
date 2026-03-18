---
title: "Android Shell 中的命令：settings"
date: 2023-04-05
draft: false
description: "为了电视盒子的无障碍这盘醋，包了碟饺子"
tags: ["Android"]
---

## 前言

> 家里的创维盒子需要手机遥控功能，虽说百变遥控可以通过 root 实现，但是毕竟是十年前的老软件了，随着手机系统更新已经落伍了，但是一众新软件都是通过无障碍实现的鼠标和键盘输入，对于没有原生设置的电视，要如何解决呢？
> 小米 6 的 20.1.16 版本 miui 有个大 bug:处于底部的通知栏磁贴怎么都拖不上去，就只能放弃不用了吗？  

但是需要注意的是，修改所有的`secure`命名空间下面的设置项都需要 root 权限。

## 简单上手

### 原理介绍

现代 Android（7+）的设置项本质是修改`/data/system/users/0/`下的  `settings_global.xml``settings_secure.xml``settings_system.xml`
三个 xml，这三个文件保存了你在设置 app 里修改的项目。而旧版的 android 则是在“设置存储（com.android.providers.settings”里的/databases 里存储设置项目，查了下资料，大概说是因为效率原因？  

### 使用方法

我们使用的时候，先列出可以修改的项目及参数： 
`settings list <命名空间>`  
对某一设置项进行查看： 
`settings get <命名空间> <项目>`  
对某一设置项进行修改： 
`settings put <命名空间> <项目> <参数>`  

## 实操

使用 settings list 输出的内容大概可以粗略分为两种：  

1. 只能开启或者禁用的。1 为开启，0 为禁用。
2. 有应用程序特定名字的项目。这些一般反编译 AndroidManifest.xml 会看到应用程序的声明，但由于不会用/和。分开实用性并不大。  
要进行修改，得先知道它们的名字。既然我们要在这台设备上修改，那用另一台设备手动开启后就可以 list 出来，从而知道特定的名称。  
需要注意的一点是，我们一般只是在原有的参数上面添加，所以在使用 settings put 时，别忘了把原有的参数也加上去。  

首先当然是启用无障碍的总开关：  
`settings put secure accessibility_enabled 1`  

以下是我使用的一些常用应用对应的名称：

- **旋转的无障碍“旋转”的无障碍权限**  

```bash
settings put secure enabled_accessibility_services personal.fameit.nl.eg/nl.fameit.rotate.RotateAccessibilityService
```

- **KDE Connect 的鼠标控制**  

```bash
settings put secure enabled_accessibility_services org.kde.kdeconnect_tp/org.kde.kdeconnect.Plugins.MouseReceiverPlugin.MouseReceiverService
```

- **KDE Connect 的通知使用权**:  

```bash
settings put enabled_accessibility_services org.kde.kdeconnect_tp/org.kde.kdeconnect.Plugins.NotificationsPlugin.NotificationReceiver
```

```bash
settings put enabled_accessibility_services org.kde.kdeconnect_tp/org.kde.kdeconnect.Plugins.NotificationsPlugin.NotificationReceiver
```

- **KDE Connect 中启用的键盘**  

```bash
settings put secure enabled_input_methods org.kde.kdeconnect_tp/org.kde.kdeconnect.Plugins.RemoteKeyboardPlugin.RemoteKeyboardService
```
- **通知栏磁贴**  
按需添加，有一个叫做 system_qs_tiles 的项目，修改那个似乎没用。  

```bash
settings put secure sysui_qs_tiles "airplane,cell,wifi,rotation,custom(com.v2ray.ang/.service.QSTileService),batterysaver,hotspot,mute,nfc,custom(net.dinglisch.android.taskerm/.QSTileService0),gps,edit "  
```

---

## 结语

折腾了那么多，不得不感叹命令行的强大之处：正确就是 stout，错误就是 sterr，不会像 gui 控制那样出现卡顿和按了不反应等奇奇怪怪的 bug，当今时代 cli 还是有存在的意义的。
