+++
date = '2025-04-18T23:38:19+08:00'
draft = false
title = '字形、字体以及我的配置'
description = '花了点时间了解字体相关的知识~'
tags = ["Arch"]
+++

终于受不了终端里那丑得要死的宋体了，开干！XML？拿来把你！

## 衬线，无衬线，等宽

这大概是三种最常见的字形了。

### 衬线（Serif)

简单来说，就是字体有小学练字的时候的老师要求你有的那种笔锋。

对于英文版来说，很常见的是`Times New Roman` ，需要注意的是这是一个版权字体。

而对于中文版，衬线字体一般跟宋体都是同一个意思了。不过名字还是会有区分：宋体，仿宋（这个公文用的很多）,楷体，这些字体的版权都是归属于中易中标，得小心。还有一部分宋体是方正的，名字就是方正xx。

### 无衬线（Sans-Serif）

人们发现，衬线字体虽然打印出来显示效果不错，但是在屏幕上，每个字是由像素点组成的，在早期分辨率差的屏幕上，衬线字体的各种装饰部分显示效果也很差。于是就出现了无衬线的字体，简化了装饰部分，使得在屏幕上更易读。

中文，微软雅黑，算是一个历史包袱非常重的字体了，在windows上几乎是独占，效果也比其他字体好，后面还出现了一个等线，在雅黑的基础上简化了。微软名字命名的，优化好点也正常吧（？但是这是微软的小动作！

英文，Arial，这个字体名字不怎么出名，但是你在显示器上看到的，基本都是它。

### 等宽（monospace）

这一种字体是专为代码显示设计的，因为缩进的时候能够更好的对齐，在终端中，也能让Tab更好的对齐；而且易于分辨`I l`以及`O 0`。

我感觉中文和英文的这些名字，常人应该很少能听到吧？只怪Windows和生态的软件把用户驯化得太好了，如果不是用Arch，我可能也不会去了解这些内容。

你问我现在用的什么字体呢？`FiraMono Nerd Font`以及`Noto Sans Mono CJK SC`，这两种字体都是开源的，接下来讲一下他们。

## 开源字体

对于英文字体来说，有一套字体叫做`liberation`，全面实现了对Windows上面的常见字体的兼容，这套字体是红帽开发的。

而对于中文，则是思源/Noto 

> 为什么要Adobe和Google要开发思源字体/Noto CJK呢？

Google在Android 4.4之前使用的字体问题很多，不支持的字符有fallback，导致显示效果不一致。而Adobe的软件使用字体会造成版权争议，同时有自己的字体部门。两家公司一拍即合，由Google出资、提供建议，Adobe设计字体，最终出现了这套字体。这套字体可以说是开源的大胜利了，后面还有以此衍生的更纱黑体。

还有别的开源字体，霞鹜文楷，得意黑什么的，就不一一介绍了。

值得一提的是，这不是第一套中文的开源字体。在AUR上你还能看到文泉驿这款字体，至今有二十年了。虽然它的名字很诗意，但是在Noto之后，已经鲜有人用了，也没人维护了。

思源黑体极大的提高了Linux图形界面上面的字体显示体验，不过我早期使用的时候没注意，从AUR下载了Windows的兼容字体，使得终端一直在随意fallback一些奇怪的字体（捂脸），最近才决定了解一下，从而有了这篇东西。

## 系统字体调优

### Arch

管理字体，现代的Linux系统基本都是fontconfig了。我们主要是用`fc-cache`,`fc-match`两个命令。

先看看你的三种字体会匹配什么？
```shell
fc-match serif # 添加-a参数可以显示依次匹配的字体
fc-match sans-serif
fc-match monospace
```
我的是这样的：
```shell
[texsd@texsd-spin ~]$ fc-match sans-serif
NotoSansCJK-Regular.ttc: "Noto Sans CJK SC" "Regular"
[texsd@texsd-spin ~]$ fc-match serif
NotoSerifCJK-Regular.ttc: "Noto Serif CJK SC" "Regular"
[texsd@texsd-spin ~]$ fc-match monospace
FiraMonoNerdFontMono-Regular.otf: "FiraMono Nerd Font Mono" "Regular"
```

如果群魔乱舞的话，还是先去装一个`noto-cjk`包吧。

安装字体包在`/usr/share/fonts`目录，安装时会自动执行`fc-cache -fv`来刷新字体缓存，你也可以手动来刷新它们。

我还额外安装了`otf-firamono-nerd`来实现shell的emoji图标，记住不！要！安！装！nerd-fonts包集！那总共有`7GiB+`！

我是强烈推荐去修改默认字体配置文件的，虽然xml的可读性确实不怎么样，但是根据别人的改嘛，查找替换也不算太难。这里就贴一下我的方案吧：
`~/.config/fontconfig/conf.d/99-notocjk.conf`
```xml
<?xml version='1.0'?>
<!DOCTYPE fontconfig SYSTEM 'urn:fontconfig:fonts.dtd'>
<fontconfig>
 <!-- 配置黑体-->
 <match target="pattern">
  <test compare="contains" name="lang">
   <string>zh</string>
  </test>
  <test name="family" qual="any">
   <string>sans-serif</string>
  </test>
  <edit binding="strong" mode="prepend" name="family">
   <string>Noto Sans CJK SC</string>
  </edit>
 </match>
 <!-- 配置宋体-->
 <match target="pattern">
  <test compare="contains" name="lang">
   <string>zh</string>
  </test>
  <test name="family" qual="any">
   <string>serif</string>
  </test>
  <edit binding="strong" mode="prepend" name="family">
   <string>Noto Serif CJK SC</string>
  </edit>
 </match>
  <match target="pattern">
  <test name="family" qual="any">
    <string>monospace</string>
  </test>
  <edit binding="strong" mode="prepend" name="family">
 <!-- 这里等宽配置了两个字体，原因是FiraMono没有中文的等宽字体，下面写上Noto的等宽字体就可以自动fallback了-->
    <string>FiraMono Nerd Font Mono</string>
   <string>Noto Sans Mono CJK SC</string>
  </edit>
 </match>
 <dir>~/.local/share/fonts</dir>
</fontconfig>
```
总共三段内容，分别对应衬线，无衬线，等宽，按照自己的喜好修改即可。不知道字体名字可以用`fc-match -a`查看引号内的字体名称，或者看桌面设置里面的字体选项。

### Win
Windows中文版默认是使用微软雅黑的，修改需要改注册表。所以一般来说我们都会在软件里面单独修改，像Firefox，Windows Terminal，VSCode都支持。而其他的应用我选择用微软雅黑，因为Windows运行的旧应用很多都是硬编码微软雅黑的，调整他们会导致一些奇怪的问题，下面说说。

这是个版权字体（属于方正）正因为如此应该不少人吃了官司吧（？
## 点阵字体和矢量字体

点阵字体是以前低分辨率的时代使用的，现在已经基本淘汰了。但是你可能偶尔还能看到有人发那些锯齿感字体非常严重的图片，那大概就是用xp截图出来的。

现代系统基本都是矢量字体，这些字体是通过贝塞尔曲线画出来的。Windows为了兼容旧的程序和低分屏，要求字体都要支持Hinting。而自带的微软雅黑对此有优化，别的字体就不太行。但是微软雅黑尽力了，没法避免100%下的字体发虚。所以还是换4K屏吧，200%的比例放大下，字体渲染还是可以的。

想了解这篇细节，可以看看[Windows 的字体渲染的一些鸟事](https://www.bilibili.com/opus/856322865719410692)