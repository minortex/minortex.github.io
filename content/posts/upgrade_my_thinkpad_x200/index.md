+++
date = '2025-08-30T12:33:31+08:00'
draft = false
title = '给老机x200刷开源BIOS--Coreboot！'
lastmod = '2025-09-12T21:02:10+08:00'
+++

这篇文本来是想写一下升级过程的，因为我在家里面翻出了这台x200，也算是我早期用得比较久的本子了（B站就是在这上面注册的）。

出于情怀，给它换了无线网卡，换了风扇，内存4G->8G，换了原来坏了的键盘，总共没超过200元。

不过暂时没带来学校，所以图片的话，以后再补充吧。

## 刷入Coreboot注意事项

这里记载了折腾过程中遇到的坑。

### 请不要购买CH341A！

为什么我会在这里得出跟libreboot一样的结论呢？

CH341A无法设置spispeed，而是默认2M，这就造成一个问题，如果你的连接质量不好的话，这已经是一个相当高的速率了。可能会使得你根本没法看到你的芯片读取到。这里还是推荐买正版的pico吧，这玩意用的buck-boost电路，相比国产的pico来说，发热肯定会小不少，这可能对稳定刷写有一定的帮助。

### 刷写

在[libreboot的教程](https://libreboot.org/docs/install/spi.html)中，告诉你`1, 9`脚分别是WP/HOLD，据说主板自带上拉电阻，所以不用连接。

经过测试，发现夹子连接正确的话，这两个脚会有3.1v左右的电压，稍微低了一点但是不影响。

如果原始的固件你可能根本刷不进去，写入没一会就提示擦除失败，我试了连接这两个脚是无关事项，所以后来者可以不用连接。

请看过程：

```shell
❯ flashprog -p serprog:dev=/dev/ttyACM0,spispeed=16M -c "MX25L6436E/MX25L6445E/MX25L6465E/MX25L6473E/MX25L6473F" -w x200_bios.rom

Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
serprog: Programmer name is "pico-serprog"
Found Macronix flash chip "MX25L6436E/MX25L6445E/MX25L6465E/MX25L6473E/MX25L6473F" (8192 kB, SPI) on serprog.
Reading old flash chip contents... done.
Erasing and writing flash chip... FAILED at 0x00130000! Expected=0xff, Found=0x2f, failed byte count from 0x00130000-0x00137fff: 0x44aa
ERASE FAILED!
FAILED!
Uh oh. Erase/write failed. Checking if anything has changed.
Reading current flash chip contents... done.
Apparently at least some data has changed.
Your flash chip is in an unknown state.
```

那这个问题如何解决呢？答案是**先擦除，再写入**。

像这样：

```shell
❯ flashprog -p serprog:dev=/dev/ttyACM0,spispeed=16M -c "MX25L6436E/MX25L6445E/MX25L6465E/MX25L6473E/MX25L6473F" -E

...
Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
serprog: Programmer name is "pico-serprog"
Found Macronix flash chip "MX25L6436E/MX25L6445E/MX25L6465E/MX25L6473E/MX25L6473F" (8192 kB, SPI) on serprog.
Erasing flash chip... Erase done.
```

然后就可以完美写入了：

```shell
❯ flashprog -p serprog:dev=/dev/ttyACM0,spispeed=16M -c "MX25L6436E/MX25L6445E/MX25L6465E/MX25L6473E/MX25L6473F" -w x200_bios.rom

...
Using clock_gettime for delay loops (clk_id: 1, resolution: 1ns).
serprog: Programmer name is "pico-serprog"
Found Macronix flash chip "MX25L6436E/MX25L6445E/MX25L6465E/MX25L6473E/MX25L6473F" (8192 kB, SPI) on serprog.
Reading old flash chip contents... done.
Erasing and writing flash chip... Erase/write done.
Verifying flash... VERIFIED.
```

提醒一句，尽量不要接在hub或者台式机的前面板，很可能会供电不足导致写入之后验证失败。

如果杜邦线的长度太长（最好10cm），夹子的质量不好，可能会导致你根本无法用16M的spispeed写入，甚至根本没法读取到芯片，经过我测试，现在我手上的这套设备已经不太行了，只能在64K的速度稳定写入，这消耗了大概50分钟进行一轮读取-擦除/写入-读取，所以当你成功刷入coreboot后，最好保守一点，直接在目标机子上面刷吧。