+++
date = '2025-07-07T21:00:20+08:00'
draft = false
title = '黑群晖与PVE折腾小记'
+++
## 前言

这是一篇记录自己折腾的过程的文章，可能会随着我的折腾过程补充，可能开会补一点动机或者小技巧之类的，所以你看到的不一定是完整版~

## 直通SATA控制器的硬盘SMART修复

使用PVE直通我的SATA控制器进群晖，发现命令行的SMART的功能不正常，表现就是没法显示其中的详细信息，而且温度显示为0°C。

虽然群晖里面显示有温度，但是最新的DSM7.2.2已经没法在桌面端读取SMART信息了，不知道是出于什么考虑。

在shell里面是这样的：

```
texsd@tnas ~ [2]> sudo smartctl -a /dev/sata1
smartctl 6.5 (build date Sep 26 2022) [x86_64-linux-5.10.55+] (local build)
Copyright (C) 2002-16, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF INFORMATION SECTION ===
Vendor:               WDC
Product:              WD40EJRX-89AKWY0
Revision:             0B80
User Capacity:        4,000,787,030,016 bytes [4.00 TB]
Logical block size:   512 bytes
Physical block size:  4096 bytes
LU is fully provisioned
Rotation Rate:        5400 rpm
Form Factor:          3.5 inches
Logical Unit id:      0x50014ee2bed41999
Serial number:        WD-XXXXXXXXXXXX
Device type:          disk
Local Time is:        Thu Jul 10 21:23:30 2025 CST
SMART support is:     Unavailable - device lacks SMART capability.

=== START OF READ SMART DATA SECTION ===
Current Drive Temperature:     0 C
Drive Trip Temperature:        0 C

Error Counter logging not supported


[GLTSD (Global Logging Target Save Disable) set. Enable Save with '-S on']
Device does not support Self Test logging
```

我问了下Gemini，跟我说消费级主板不支持，叫我买LSI卡，我当时想麻烦了，亏我专门找一块4SATA的板子。


### 问题解决

我先是一通操作，把SATA控制器直通进Arch虚拟机，发现是能成功读取的。那说明是DSM出了点问题。在RR里面一通乱改添加`smartctl`，本来以为成了，结果接上三块硬盘，一看，只有其中一块是正常的。

看了网上一些教程，发现要手动指定设备类型，才能正确读出硬盘的smart信息。

群晖手动改了sata盘的名字，不是sd[a-z]了，而是sata[1-9]。所以我得这样获取：

```shell
sudo smartctl -d sat -a /dev/sata1
```

```
smartctl 6.5 (build date Sep 26 2022) [x86_64-linux-5.10.55+] (local build)
Copyright (C) 2002-16, Bruce Allen, Christian Franke, www.smartmontools.org

=== START OF INFORMATION SECTION ===
Device Model:     WDC WD40EJRX-89AKWY0
Serial Number:    WD-XXXXXXXXXXXX
LU WWN Device Id: 5 0014ee 2bed41999
Firmware Version: 80.00B80
User Capacity:    4,000,787,030,016 bytes [4.00 TB]
Sector Sizes:     512 bytes logical, 4096 bytes physical
Rotation Rate:    5400 rpm
Form Factor:      3.5 inches
Device is:        Not in smartctl database [for details use: -P showall]
ATA Version is:   ACS-3 T13/2161-D revision 5
SATA Version is:  SATA 3.1, 6.0 Gb/s (current: 6.0 Gb/s)
Local Time is:    Thu Jul 10 21:33:49 2025 CST
SMART support is: Available - device has SMART capability.
SMART support is: Enabled

=== START OF READ SMART DATA SECTION ===
SMART overall-health self-assessment test result: PASSED

General SMART Values:
Offline data collection status:  (0x00) Offline data collection activity
                                        was never started.
                                        Auto Offline Data Collection: Disabled.
Self-test execution status:      (   0) The previous self-test routine completed
                                        without error or no self-test has ever 
                                        been run.
Total time to complete Offline 
data collection:                (41760) seconds.
Offline data collection
capabilities:                    (0x11) SMART execute Offline immediate.
                                        No Auto Offline data collection support.
                                        Suspend Offline collection upon new
                                        command.
                                        No Offline surface scan supported.
                                        Self-test supported.
                                        No Conveyance Self-test supported.
                                        No Selective Self-test supported.
SMART capabilities:            (0x0003) Saves SMART data before entering
                                        power-saving mode.
                                        Supports SMART auto save timer.
Error logging capability:        (0x01) Error logging supported.
                                        General Purpose Logging supported.
Short self-test routine 
recommended polling time:        (   2) minutes.
Extended self-test routine
recommended polling time:        ( 443) minutes.
SCT capabilities:              (0x303d) SCT Status supported.
                                        SCT Error Recovery Control supported.
                                        SCT Feature Control supported.
                                        SCT Data Table supported.

SMART Attributes Data Structure revision number: 16
Vendor Specific SMART Attributes with Thresholds:
ID# ATTRIBUTE_NAME                                                   FLAG     VALUE WORST THRESH TYPE      UPDATED  WHEN_FAILED RAW_VALUE
  1 Raw_Read_Error_Rate                                              0x002f   200   200   051    Pre-fail  Always       -       0
  3 Spin_Up_Time                                                     0x0027   223   219   021    Pre-fail  Always       -       3850
  4 Start_Stop_Count                                                 0x0032   100   100   000    Old_age   Always       -       303
  5 Reallocated_Sector_Ct                                            0x0033   200   200   140    Pre-fail  Always       -       0
  7 Seek_Error_Rate                                                  0x002e   200   200   000    Old_age   Always       -       0
  9 Power_On_Hours                                                   0x0032   056   056   000    Old_age   Always       -       32405
 10 Spin_Retry_Count                                                 0x0032   100   100   000    Old_age   Always       -       0
 11 Calibration_Retry_Count                                          0x0032   100   100   000    Old_age   Always       -       0
 12 Power_Cycle_Count                                                0x0032   100   100   000    Old_age   Always       -       203
192 Power-Off_Retract_Count                                          0x0032   200   200   000    Old_age   Always       -       79
193 Load_Cycle_Count                                                 0x0032   200   200   000    Old_age   Always       -       233
194 Temperature_Celsius                                              0x0022   110   105   000    Old_age   Always       -       40
196 Reallocated_Event_Count                                          0x0032   200   200   000    Old_age   Always       -       0
197 Current_Pending_Sector                                           0x0032   200   200   000    Old_age   Always       -       0
198 Offline_Uncorrectable                                            0x0030   100   253   000    Old_age   Offline      -       0
199 UDMA_CRC_Error_Count                                             0x0032   200   200   000    Old_age   Always       -       0
200 Multi_Zone_Error_Rate                                            0x0008   100   253   000    Old_age   Offline      -       0

SMART Error Log Version: 1
No Errors Logged

SMART Self-test log structure revision number 1
Num  Test_Description    Status                  Remaining  LifeTime(hours)  LBA_of_first_error
# 1  Short offline       Aborted by host               90%     32358         -
# 2  Short offline       Completed without error       00%     32333         -
# 3  Short offline       Completed without error       00%     25336         -
# 4  Short offline       Completed without error       00%     25093         -
# 5  Short offline       Completed without error       00%     15531         -
# 6  Short offline       Completed without error       00%     15527         -
# 7  Short offline       Completed without error       00%     15527         -
# 8  Short offline       Completed without error       00%      7694         -
# 9  Short offline       Completed without error       00%      6217         -
#10  Short offline       Completed without error       00%      3870         -
#11  Short offline       Completed without error       00%      3869         -
#12  Short offline       Completed without error       00%      3868         -
#13  Short offline       Completed without error       00%      3609         -
#14  Short offline       Completed without error       00%      3598         -
#15  Short offline       Completed without error       00%      3545         -
#16  Short offline       Completed without error       00%      3524         -
#17  Short offline       Completed without error       00%      3335         -
#18  Short offline       Completed without error       00%      3033         -
#19  Short offline       Completed without error       00%         0         -
#20  Short offline       Completed without error       00%         0         -
#21  Short offline       Completed without error       00%         0         -

Selective Self-tests/Logging not supported
```

确实获取到了，但是为什么呢？

### 问题溯源

得懂能行，更得明白为什么可以这样。

我去翻了`smartctl`的manual，里面关于`-d`是这么写的：

```
...

       smartctl guesses the device type if possible.  If necessary, the '-d' option can be used
       to override this guess.

...

       -d TYPE, --device=TYPE
              Specifies the type of the device.  The valid arguments to this option are:

              auto  -  attempt to guess the device type from the device name or from controller
              type info provided by the operating system or from a matching USB ID entry in the
              drive database.  This is the default.

              test - prints the guessed TYPE, then opens the device and  prints  the  (possibly
              changed) TYPE name and then exits without performing any further commands.

              ata  - the device type is ATA.  This prevents smartctl from issuing SCSI commands
              to an ATA device.

              scsi - the device type is SCSI.  This prevents smartctl from issuing ATA commands
              to a SCSI device.

              nvme[,NSID] - the device type is NVM Express (NVMe).  The optional parameter NSID
              specifies the namespace id (in hex) passed to the driver.  Use 0xffffffff for the
              broadcast namespace id.  The default for NSID is the namespace  id  addressed  by
              the device name.

              sat[,auto][,N]  -  the device type is SCSI to ATA Translation (SAT).  This is for
              ATA disks that have a SCSI to ATA Translation Layer (SATL) between the  disk  and
              the  operating  system.   SAT  defines two ATA PASS THROUGH SCSI commands, one 12
              bytes long and the other 16 bytes long.  The default is the 16 byte variant which
              can be overridden with either '-d sat,12' or '-d sat,16'.

              If '-d sat,auto' is specified, device type SAT (for ATA/SATA disks) is only  used
              if  the  SCSI INQUIRY data reports a SATL (VENDOR: "ATA     ").  Otherwise device
              type SCSI (for SCSI/SAS disks) is used.
```

好家伙！原来是给我自动在猜啊😲

康康你猜到了什么~

```shell
texsd@tnas ~> sudo smartctl -d test /dev/sata1
smartctl 6.5 (build date Sep 26 2022) [x86_64-linux-5.10.55+] (local build)
Copyright (C) 2002-16, Bruce Allen, Christian Franke, www.smartmontools.org

/dev/sata1: Device of type 'scsi' [SCSI] detected
/dev/sata1: Device of type 'scsi' [SCSI] opened
texsd@tnas ~ [255]> sudo smartctl -d test /dev/sata2
smartctl 6.5 (build date Sep 26 2022) [x86_64-linux-5.10.55+] (local build)
Copyright (C) 2002-16, Bruce Allen, Christian Franke, www.smartmontools.org

/dev/sata2: Device of type 'scsi' [SCSI] detected
/dev/sata2: Device of type 'scsi' [SCSI] opened
texsd@tnas ~ [255]> sudo smartctl -d test /dev/sata3
smartctl 6.5 (build date Sep 26 2022) [x86_64-linux-5.10.55+] (local build)
Copyright (C) 2002-16, Bruce Allen, Christian Franke, www.smartmontools.org

/dev/sata3: Device of type 'scsi' [SCSI] detected
/dev/sata3 [SAT]: Device open changed type from 'scsi' to 'sat'
/dev/sata3 [SAT]: Device of type 'sat' [ATA] opened
```

所以问题已经很清晰了，PVE在把SATA控制器直通的时候，识别出了一点问题，没有正确的报告需要使用sat(SCSI to ATA Translation)，同时DSM配套的`smartctl`太旧了，猜错了，没有猜到这一个SCSI控制器是需要使用sat来翻译，直接使用SCSI来获取SMART信息，就没法读取到正确的信息。

> 但是为什么是SCSI控制器？我不是把PCIe设备直通吗？

这还是挺奇妙的，因为PVE很懒，只想加载一个VirtIO SCSI驱动，不想再折腾一个SATA驱动，所以虚拟机看到的，是一个SCSI设备，想猜出是 sat ，得靠点想象力。

但是新版的`smartctl`就成功了，~~这就不得不提Arch的滚动更新的优越性了~~

一些知识补充：

> SCSI并不是为了磁盘而生的，而是一个系统的接口，用于连接大量外围设备的。它的成本早期非常高昂，需要一个独立的SCSI控制器，所以只有高端工作站才用得起。八十年代，IBM兼容机崛起，为了降低成本，人们开发了ATA (IDE)，这个控制器的成本低廉，而且控制部分集成在硬盘上，大幅降低了成本。（这就是为什么SAS硬盘没法接在SATA控制器上，但是反过来就可以）

突然想起了*nix和dos的斗争，当年的dos也太简陋了，连用户管理都没有，早年我说这设计那么垃圾的系统，自动补全又没有，用的逆天的反斜杠，怎么当时会抢占那么多市场？

但是人家确实打下了市场，就是因为硬件要求低。

所以说当时降本是当时时代的趋势，就算现在SAS阵列卡已经白菜价了，*nix甚至占用比Windows还低，但是前者估计是不太可能回到消费级电子领域了，后者可能还有点希望，得指望deepin和信创了。

## 群晖的文件权限管理

我们已经早都知道，传统的Linux权限很简单而且很不方便，只能设置所有者、组和其他的权限，随后拓展出来的ACL规则则很灵活。但是群晖上面没有`setfacl`和`getfacl`之类的命令，取而代之的是`synoacltool`，应该是存了数据库以便web也能够正确使用这些权限。

我从旧NAS迁移过来的数据是使用rsync的，旧nas的权限管理比较混乱，导致所有存储的文件都是UID0（root），迁移过来就造成了一些问题。

我不知道群晖是怎么实现网页可以读写的，但是我在shell里面就没法进入这些文件夹，此时就需要修复。

群晖提供的方便的webui来修改，在共享文件夹的子文件夹右键-属性-权限。此时会显示此共享文件夹默认配置的权限，点击下面的“应用到这个文件夹、子文件夹及文件”，保存。此时群晖就把这个文件夹改成ACL模式，使得在shell里面也能访问。

但是我有些疑问：

### 1. 为什么改ACL那么快？

> 当您在 File Station 的图形界面中勾选“应用到子文件夹...”时，您不是在运行一个简单的脚本，而是在向 DSM 的核心服务发出一个高级指令。

> 这个指令更像是：“嘿，DSM 内核/存储服务，请你用最高效的方式，把这个 ACL 策略应用到整个文件夹树”。

> DSM 的底层服务接收到这个“批发订单”后，会直接在内核层面或者以最优化的方式遍历文件系统的元数据 (metadata)。它可以批量处理、减少磁盘 I/O、避免不必要的上下文切换，效率远非 chmod -R 可比。

> （摘抄自Gemini的回答）

### 2. ACL是怎么工作的？

通过ACL管理的权限，我很意外的发现`ls`的显示已经不正常了。先举个例子：

ACL规则是这样的：

```
texsd@tnas /volume1> sudo synoacltool -get 个人数据
ACL version: 1
Archive: has_ACL,is_support_ACL
Owner: [root(user)]

         [0] group:administrators:allow:rwxpdDaARWc--:fd-- (level:0)
         [1] group:custom_user:allow:rwxpdDaARWc--:fd-- (level:0)
         [2] user:ActiveBackup:allow:rwxpdDaARWc--:fd-- (level:0)
```

可以看到，我在`administrators`组，有访问这个目录的权限。

我用`ls`查看权限：

```
texsd@tnas /volume1> ls -lah |grep 个人数据
drwxrwxrwx+  1 root         root           86 Jul  8 11:11  个人数据
```

我看到所有人都是有这个权限的。

guest用`ls`查看权限：

```
guest@tnas:/volume1$ ls -lah | grep 个人数据
d---------+  1 root         root           86 Jul  8 11:11 个人数据
```

他没有任何权限，自然无法进入。

所以说，ACL实际上改变了每个人看到的`ls`信息，在ACL Mode下，`ls`的输出已经不准确了。

### 3. 虽然说权限已经不准确了，那么所有者和组怎么样？

所有者和组仍然是以创建的用户为准的。谁创建的就是谁和启主要用户组（UID显示的组）。

### 4. ACL让我整个终端显示都是一片绿，为什么要在POSIX的rwx中设置为777？

这里有一个小前置知识，如果其他用户可写，那么就会显示为绿色背景，如果文件可执行，就是显示为绿色字体。

因为ACL已经接管了权限管理，所以说POSIX显示的已经不够用了，比如说我上面的例子，有两个组都能访问这个文件夹，这个究竟如何界定？

如果使用770，那么指的是users才有这个权限，实际上并不是。

所以，ACL让每个人看到的东西不一样，这里的777表示有极大的权限，反之没权限的为000，不是传统意义上面的421了。

~~我明白为什么fish不兼容POSIX了，因为确实不符合现代的一些实践了~~


## 参考

1. `smartctl` Manual

2. [小型计算机系统接口 - 维基百科](https://zh.wikipedia.org/wiki/%E5%B0%8F%E5%9E%8B%E8%AE%A1%E7%AE%97%E6%9C%BA%E7%B3%BB%E7%BB%9F%E6%8E%A5%E5%8F%A3)

3. [SATA - 维基百科](https://zh.wikipedia.org/wiki/SATA)

4. [高技术配置 - 维基百科](https://zh.wikipedia.org/wiki/%E9%AB%98%E6%8A%80%E8%A1%93%E9%85%8D%E7%BD%AE)