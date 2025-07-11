+++
date = '2025-06-20T23:53:22+08:00'
draft = false
title = '维护Esxi的小记'
+++

## 前言

学校社团的虚拟机空间快要不够了，派我进行整理以下虚拟机。看了一通，发现好多虚拟机是厚制备的，感叹当时买新硬盘的时候真是奢侈！

现在空间快要用尽了，用了百分之八十左右，大家还在讨论要不要给esxi加一块硬盘。我提出其实没必要，因为很多空间是可以压缩的，比如一台`FreshCup`机子，本身就只有一个服务，但是当时磁盘选了厚置备，只用了13G，但是占用了快50G，这真浪费啊！于是便有了这篇文。

## 初探ESXi内部结构

开始我脑子没转过来，还想着找一台大硬盘的电脑，用WorkStation来进行压缩。不知道是不是无线的问题，下载速度不过百兆出头，这对于几十个G来说真是挑战！

但是你看ESXi的那个webui叫作一个完成度低啊，根本找不到转换的选项。

我之前也听说过ESXi用的是定制的系统，但是人家竟然能用22端口访问，登录进去甚至还有bash，GNU的基本工具还是有的，但是稍微常见一点的工具比如`curl`就没有了。

### 这个系统是什么呢？

```shell

[root@localhost:/vmfs/volumes/65522cf6-65fd4b38-f248-6c92bfca102e] uname -a
VMkernel localhost 7.0.3 #1 SMP Release build-21686933 Apr 28 2023 08:42:51 x86_64 x86_64 x86_64 ESXi

```

呃呃，`VMkernel`，大概是基于`unix`定制的吧，但是我觉得也有可能是`linux`。

### 看看硬盘占用情况？

```shell

[root@localhost:/vmfs/volumes/65522cf6-65fd4b38-f248-6c92bfca102e] df -h
Filesystem   Size   Used Available Use% Mounted on
VMFS-6     745.0G 481.7G    263.3G  65% /vmfs/volumes/99-datastore0
VFFS       103.5G   3.5G    100.0G   3% /vmfs/volumes/OSDATA-654f485c-fa8f3400-bbb9-6c92bfca102e
vfat         4.0G 204.8M      3.8G   5% /vmfs/volumes/BOOTBANK1
vfat         4.0G  64.0K      4.0G   0% /vmfs/volumes/BOOTBANK2

```

（完成了才贴上来，假装没看到剩余的263G空间吧）

### 有什么特殊工具？

当然，这个系统里面有一大堆vm开头的工具，这就是为了命令行管理用的ESXi专有工具了。

我主要用的就是`vmkfstools`这个工具。

这个工具用起来思路也非常清晰：

- **用`-i`来指定输入的虚拟磁盘。**这里注意是那个后缀最短的`vmdk`，如果是多文件的话，这个文件包含了一个虚拟磁盘使用的所有文件清单。
- **用`-K`压缩现有的精简置备磁盘。**
- **用`-d thin`指定创建一个精简置备磁盘**

最后跟上你要输出的磁盘名字，跟不跟都行，看参数。

## 坑点

本来这块硬盘空间就不剩多少了，所以我开始直接根据厚置备的磁盘生成一个精简置备的磁盘。因为按照正常的逻辑，生成的精简置备磁盘大小只有十几G，那么我现有的空间还是够的。

结果失败了，试了好几次，都不行。（***坑点1***）

我决定把磁盘搞到电脑上面，用WorkStation来转换。转换也成功，生成的磁盘是我需要的精简类型，占用正常。然后我就转移回ESXi上面，结果导入失败。

ESXi不支持多文件的磁盘格式，这台是7.0。可能旧的确实不可以吧？（***坑点2***）

我又创建了一个单文件的精简置备移回去，这时候我正好删除了其他不要的虚拟机，总空间>50G了，传上去了我也没管这台是否占用了这么大的空间。

然后我觉得这样太费事了，怎么不能在主机上面直接压缩？接着我就使用那个命令行工具压缩，但是压了好几次，该填零的也用`dd/sdelete`填充了，但是使用`ls`发现显示的还是50G！

我以为这是bug，但是真正的问题在`ls`和`vmfs`上。（***坑点3***）

众所周知，Android上使用KernelSU的时候，有的人会看到自己的手机显示成使用2T的存储，但是事实上很多人根本没有2T的手机，这是因为稀疏文件（Sparse file）造成的。使用ls列出的就是2T，我估计手机厂商获取的时候也是用类似的方法做统计，所以闹出了这一出。

其实还有别的例子，比如说btrfs就不能用`du`正确显示，就是因为文件系统的各种特性导致的。

所以说，其实我使用`-K`压缩，结果是成功的，而且使用`du`也可以直接看到，ESXi的状态面板也可以直接看到存储被释放了。但是我怎么在这个坑上面找问题，找了那么久，唉唉唉


