+++
date = '2024-12-09T15:42:53+08:00'
draft = false
title = '我的ArchLinux折腾记录'
description = "arch赛高！"
tags = ["Arch", "Chromebook"]
+++

## 前言

暑假的时候在我的掠夺者·擎neo上面第一次纯手动安装了Arch，过程很有意思，但是后面烂到家的NV驱动让我受不了。

我在win下喜欢开独显直连模式，但是在arch下就有很大问题：每次睡眠，内建显示器的亮度都会自动开到最大。

~~我试过很多办法，都很难实现记忆之前的亮度。只有在BIOS里面开启混合模式才会出现intel_backlight，这真是太折磨了。~~

~~最后，我的评价是，别在日用的电脑上面用n卡和linux！~~

其实是有办法的，给睡眠加个钩子保存亮度，然后唤醒的时候读取文件并还原亮度。也是勉强能用的。（果然水平提高了就有新办法

## 物色新机

作为一个穷学生，已经花了大几千实现臭打游戏的目标，无论怎么说都不太好再拿出几千买电脑。开始我把目标锁定在3k左右，然后降到2k，最后1k。

正好这段时间有国补，就在看鸡哥的14x，但是各种说品控差让我望而却步。后面又看火影的6800二手，感觉周边又差一点。

> 怎么，你又开始后悔没有买6800以上的u了？！ 其实只是舍不得出那么多钱罢了！

几番挑选，我决定捡洋垃圾，目光投向了chromebook。这样，就有了这篇文章的主角：Acer Spin713 二代(cp713-2w)。在海鲜市场的js以1050的价格拿下。

配置是i5-10210u，马甲什么的我不是很在意。我在意的是这块屏幕好像是夏老师之前提到的[网格纱窗屏](https://zhuanlan.zhihu.com/p/570757067)，凑近看确实观感不太好，其实，我根本不需要触摸屏的，但是换不得呀！

默念1050...默念1050...默念1050...

## 安装过程

用Arch怎么能不手动安装呢？

但是ArchInstall真的太香了！连好网络分好区，设置好一些东西，直接重启就看到sddm了。

然而，像装黑苹果一样，大家都是装完了然后开系统信息截屏。装完Arch你也可以`fastfetch`，然而，这一切仅仅是个开始...

### 输入法设置

首先得有输入法吧？

我用的是fcitx5 + rime + 雾凇拼音的组合，最终效果还不错。

1. 首先安装fcitx5、rime和雾凇拼音：

```bash
paru -S fcitx5 fcitx5-rime rime-ice-git ## 可以用archlinuxcn源的
```

2. 根据[雾凇拼音的配置方案](https://github.com/iDvel/rime-ice)，把这段配置加入rime输入法：

```yaml
# $HOME/.local/share/fcitx5/rime/
patch:
  # 仅使用「雾凇拼音」的默认配置，配置此行即可
  __include: rime_ice_suggestion:/
  # 以下根据自己所需自行定义，仅做参考。
  # 针对对应处方的定制条目，请使用 <recipe>.custom.yaml 中配置，例如 rime_ice.custom.yaml
  __patch:
    key_binder/bindings/+:
      # 开启逗号句号翻页
      - { when: paging, accept: comma, send: Page_Up }
      - { when: has_menu, accept: period, send: Page_Down }
```


3. 进入设置里面，输入与输出-键盘-虚拟键盘把fcitx5打开，这时候才会在语言和时间下面出现输入法。如果因为kde的bug出不来的话，重启或者重装吧。

4. 输入法-添加输入法，选择中州韵。这里建议点击中州韵的配置，然后把“切换输入法的行为”修改成“提交原始字符串”。

5. 基本完成了。不过如果没有配置字体，会导致emoji显示空白。可以参考我的[字体方案](https://blog.texsd.eu.org/p/%E5%AD%97%E5%BD%A2%E5%AD%97%E4%BD%93%E4%BB%A5%E5%8F%8A%E6%88%91%E7%9A%84%E9%85%8D%E7%BD%AE/#%E7%B3%BB%E7%BB%9F%E5%AD%97%E4%BD%93%E8%B0%83%E4%BC%98)来解决问题。

6. 如果想要让fcitx5符合breeze的外观，可以安装这个包：`fcitx5-breeze`，然后在输入法-配置附加组件-经典用户界面-主题里面修改成KDE Plasma来实现。

### Locale设置

默认在安装的时候大家都会选择`en_US.UTF-8`，这是为了避免tty不支持中文显示。不过在安装完毕后，一般都会重新编译`zh_CN.UTF-8`的语言支持。

这里我选用了一些特殊的设置方式，而不是直接设置`LC_ALL`。原因是让各种工具提示的信息和显示的日志为英文，同时让单位之类的显示符合国内的习惯。

配置像这样：

```shell
# /etc/locale.conf
LANG=zh_CN.UTF-8           # 默认界面语言为中文
LC_MESSAGES=en_US.UTF-8    # 强制日志和错误信息用英文
LC_PAPER=en_SG.UTF-8       # 纸张尺寸 A4
LC_MEASUREMENT=en_SG.UTF-8 # 公制单位（米、升、℃）
LC_TIME=en_SG.UTF-8        # 24 小时制时间
```

参考[archwikicn-安装教程](https://wiki.archlinuxcn.org/wiki/%E5%AE%89%E8%A3%85%E6%8C%87%E5%8D%97#%E5%8C%BA%E5%9F%9F%E5%92%8C%E6%9C%AC%E5%9C%B0%E5%8C%96%E8%AE%BE%E7%BD%AE)

## 对chromebook的折腾过程

### 声音驱动

众所周知，Chromebook很多型号的声音驱动一直是个大问题，windows上面甚至得付费才有驱动，而我装好一进来也是没有声音的。


很幸运的，在Chrultrabook上面提示Linux是完全支持的。然后我就找到了这个项目：

{{<github repo="WeirdTreeThing/chromebook-linux-audio">}}

直接一键部署，太舒服了！不过似乎不支持Ubuntu。

后来，在alsa的一次更新后，我的喇叭不出声了，翻了下issue，[这里](https://github.com/WeirdTreeThing/chromebook-linux-audio/issues/185)提到重新安装加上这个参数就可以了：

```shell
./setup-audio --branch syntax-7
```

### 按键映射

Chromebook的键盘比较特殊，没有<kbd>Del</kbd>，没有<kbd>Ins</kbd>。原来<kbd>Capslock</kbd>的位置现在变成了<kbd>Meta</kbd>(<kbd>Win</kbd>)键。而左<kbd>Alt</kbd>和<kbd>Ctrl</kbd>就变得非常大。

写声音脚本的这位兄弟顺手写了个按键映射：

{{<github repo="WeirdTreeThing/cros-keyboard-map">}}

这个工具映射了上面的功能按键，让<kbd>Meta</kbd>+功能键可以实现原来的功能，然后单独按下功能键就是<kbd>F1</kbd>-<kbd>F10</kbd>。调节键盘背光，则是按下<kbd>leftAlt</kbd>+亮度按键。

我手动对这台笔记本的按键进行定制：

- 让锁屏按键变成<kbd>Del</kbd>

- <kbd>rightAlt</kbd>加上锁屏按键变成<kbd>F11</kbd>，加上<kbd>Backspace</kbd>变成<kbd>F12</kbd>

- 删除了一些冗余的配置，避免了之前为了通用一刀切导致的物理音量键变成<kbd>F8</kbd>/<kbd>F9</kbd>的bug

```ini
[ids]
k:0001:0001

[main]
f13=delete
rightalt = layer(rightalt)

[meta]
f1 = back
f2 = forward
f3 = refresh
f4 = f11
f5 = scale
f6 = brightnessdown
f7 = brightnessup
f8 = mute
f9 = volumedown
f10 = volumeup
backspace = f12

[alt]
f6 = kbdillumdown
f7 = kbdillumup

[rightalt]
f6 = kbdillumdown
f7 = kbdillumup
backspace = f12
f13 = f11

[control]
f5 = sysrq

[control+alt]
f13 = C-A-delete
```

另外值得一提的就是，键盘上面所有的英文全部都是小写的。


### 充电

#### 充电限制

首先需要安装ectool，这一个工具可以在aur的`fw-ectool-git`下载，fw代表的是framework book，这个笔记本使用的是开源的ec，正好chromebook也是这个，所以可以通用。

ectool可以控制系统的充电情况。不过可惜我这一台是10代的，不支持sustainer，也就是说ec不能实现在某个区间自动断电。所以只能写一个脚本来控制系统的充电情况。尽管这样还是有一些限制，比如说关机充电可能就会充到满。

接下来我会对我使用的[一些脚本](https://gist.github.com/minortex/0fe6c1098ec8a4f879fa9315d216a957) 进行解释。

- **charge_control.sh**：这是主要进行控制的脚本，里面有两个功能，一个是`--check-battery`，这个参数会检测电池电量，如果超过了78，就会自动设置成idle模式，同时关闭计时器，避免进行无谓的计时；另一个是`--connect-charger`，这个用于udev的控制。
- **check-battery.service(timer)**：尝试一下systemd-timer，为后续的启动和停用计时器做准备。
- **control_systemd_battery_timer.sh**：这是一个用于设置上述服务的脚本。主要是用于给udev触发使用。(在rules里面写这么多太不优雅了)
- **99-battery.rules**：这就是udev触发的规则了。在插上电源的时候检测一次电池电量，大于78就idle，小于就开始充电。同时开启计时器，每三分钟检测一次电池。如果拔掉电源，那么就停止计时器。

值得小心的是，需要把service设置成enabled，这样当电量达到78，同时插着电源并开启idle模式的时候重启电脑，才会保持这个电量，因为重启会重置限制充电的状态；同时也把timer设置成enabled，这样在电池没到78，同时冲着电的时候重启电脑，才能在到达78的时候检测到从而开启idle模式。

写了那么多，看起来还是有点臃肿的感觉！不过功能总算是实现了。

#### 缓解kde的电量显示的bug

我到手没几天，就发现kde报告的电池状态有bug。当拔下充电器后，显示已连接充电器，但仍在放电。短暂插入充电器然后拔出，会有概率避免这个问题；睡眠再唤醒也能避免这个问题。

经过一系列的排查，发现问题出现在`upower`上，upower报告了错误的电池状态。`power_supply`总共有三个对象：

- AC
- CROS_USBPD_CHARGER0
- CROS_USBPD_CHARGER1

虽然在sysfs里面报告的`online`状态是正确的，来到`upower`就不对了。`AC online`的状态和充电器的状态是相反的。重启`upower`服务可以让状态正确，但是已经被`powerdevil`接收了，所以无济于事。我寻找了很多办法，最终在`upower`的gitlab上面的[issue](https://gitlab.freedesktop.org/upower/upower/-/issues/232)看到了解决方案：

覆写`upower`的systemd服务，把它访问AC的sysfs禁用：
```ini
### Editing /etc/systemd/system/upower.service.d/override.conf
### Anything between here and the comment below will become the contents of the drop-in file
 
[Service]
InaccessiblePaths=/sys/class/power_supply/AC /sys/devices/pci0000:00/0000:00:1f.0/PNP0C09:00/ACPI0003:00/power_supply/AC
 
### Edits below this comment will be discarded
```

虽然方法很暴力，但是它有效啊！

### 风扇控制

理论上，其他的chromebook可以直接通过aur安装`fw-fanctrl`来安装一个用python写的脚本来控制。

不过我这台spin713比较特殊，使用`ectool`来查看温度是这样的：

```shell
$ sudo ectool temps all
--sensor name -------- temperature -------- ratio (fan_off and fan_max) --
Temp1                 318 K (= 45 C)          66% (298 K and 328 K)
Temp2                 324 K (= 51 C)          86% (298 K and 328 K)
Temp3                 314 K (= 41 C)        N/A (fan_off=0 K, fan_max=0 K)
```

而`lm-sensors`的输出：

```shell
$ sensors |sed -n "/coretemp-/,/Temp3/p"

coretemp-isa-0000
Adapter: ISA adapter
Package id 0:  +76.0°C  (high = +100.0°C, crit = +100.0°C)
Core 0:        +59.0°C  (high = +100.0°C, crit = +100.0°C)
Core 1:        +76.0°C  (high = +100.0°C, crit = +100.0°C)
Core 2:        +57.0°C  (high = +100.0°C, crit = +100.0°C)
Core 3:        +61.0°C  (high = +100.0°C, crit = +100.0°C)

cros_ec-isa-0000
Adapter: ISA adapter
fan1:        1641 RPM
Temp1:        +42.9°C  
Temp2:        +43.9°C  
Temp3:        +39.9°C
```

可以发现，ectool并没有读取到cpu的温度，而是其他部分的温度，这个温度会比cpu负载高的时候的温度低很多，当cpu温度降下来后，又会比cpu温度高。而`fw-fanctrl`默认是取`ectool`里面最高的温度，这就会导致风扇控制不灵敏，~~目前办法还在想...~~

已经找到解决办法了：安装旧版的`fw-fanctrl`。在24年5月之后，这个工具读取温度的数据源从`lm-sensors`切换到了`ectool`，原因是他们认为这样更加准确。但是我的本子ectool无法读取到cpu的温度，用着旧版就可以了。

## 小结..

Arch确实不算是一个能让人省心的系统，但是折腾的过程还是回味无穷的，paru和aur配合在一起的包管理也非常好用。另外折腾的东西，等到以后再补充吧。
