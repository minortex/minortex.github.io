+++
date = '2025-09-23T08:50:10+08:00'
draft = false
title = 'cpp学习笔记(3)'
lastmod = '2025-09-26T09:27:20+08:00'
+++

## 循环，条件与分支

这个东西老生常谈了，我本来没有看的欲望，但是有一道题目很有意思，在此记录：

> 从 1 开始，向上计数，将任何只能被 3 整除的数字替换为“fizz”一词，将任何只能被 5 整除的数字替换为“buzz”一词，将任何可被 3 和 5 整除的数字替换为“fizzbuzz”一词，如果还可被7整除，那么替换为“fizzbuzzpop”。

首先，介绍一个名词：分支预测。

简单来说，现代CPU在进行多分支的判断（`if-else`）的时候，其实会去猜程序下一步的路径，如果猜对了，那么效率会提升；如果猜错了，那么只能把流水线上面的内容清空，然后重新执行指令。

所以无论如何，应该尽量避免写`if-else`。

题目给出的答案是这么写的：

```cpp
// h/t to reader Waldo for suggesting this quiz
#include <iostream>

void fizzbuzz(int count) {
    for (int i{1}; i <= count; ++i) {
        bool printed{false};
        if (i % 3 == 0) {
            std::cout << "fizz";
            printed = true;
        }
        if (i % 5 == 0) {
            std::cout << "buzz";
            printed = true;
        }
        if (i % 7 == 0) {
            std::cout << "pop";
            printed = true;
        }

        if (!printed)
            std::cout << i;

        std::cout << '\n';
    } // end for loop
}

int main() {
    fizzbuzz(150);

    return 0;
}
```

能运行吗？能，优雅吗？我不太满意。


所以说，有没有一个办法，不同于这个思路，同时又能更计算机一点？

评论区的思路：

```cpp
#include <iostream>

void fizzbuzz(int n)
{
  for (int i{ 1 }; i <= n; i++)
  {
    int f = (i%7 == 0)*4 + (i%5 == 0)*2 + (i%3 == 0);
    switch (f)
    {
    case 0:
      std::cout << i;
      break;
    case 1:
      std::cout << "fizz";
      break;
    case 2:
      std::cout << "buzz";
      break;
    case 3:
      std::cout << "fizzbuzz";
      break;
    case 4:
      std::cout << "pop";
      break;
    case 5:
      std::cout << "fizzpop";
      break;
    case 6:
      std::cout << "buzzpop";
      break;
    case 7:
      std::cout << "fizzbuzzpop";
      break;
    }
    std::cout << '\n';
  }
  return;
}

int main()
{
  fizzbuzz(22);
}
```

这个方法非常巧妙，把每一个分支映射到了一个二进制的向量空间上面，这将会极大的提高性能，因为对于CPU来说，移位操作是原生的。但是，带来的就是更多相似字符串的重复占用，不知道这是不是良好的实践呢？

如果还想减少的话，还是用`if`来去测试位，不过这样又引入了分支。

其实这么用的地方还是很多的，POSIX的权限就是个例子。但是，用的时候就是想不到啊！

## 标准输出，标准错误和标准输入

这三者是这样的:

|名字|文件描述符|在c++中的对应|
|----|----|----|
|标准输入|0|`std::cin`|
|标准输出|1|`std::cout`|
|标准错误|2|`std::cerr`|

## 类型转换

### 数值提升(numberic promotion):

同类型，把一个更短的类型转换成一个更长的类型，安全，不会造成精度丢失。

只有两条路径：

1. `bool`，有/无负号的短整形，字符型->`int`->`unsigned int`
2. `float`->`double`

注意，从`int`到`long`不是提升，是转换。

### 数值转换(numberic conversion):

基本类型的转换，包括：

窄化(narrowing conversion)：长的类型转化成一个更短的类型，在{}中不被允许。

> 但是`constexpr`是允许的，因为是编译时求值，所以实际上是截断不是转化。

### 算术转换(arithmetic conversion):

对基本算术操作符两端的不同类型进行转换，有些规则：

1. 整数转浮点。
2. 对于无符号/有符号：
  
  - 如果没超过有符号上限，那就转换成有符号。
  - 超过了，那就转换成无符号。

`static_cast`在编译时检查（类型在编译时是确定的），`dynamic_cast`在运行时检查。

不建议使用C-Style的转换，因为他可能使用上面中的任意一个以及`const_cast`。

## auto

对于`auto`来说，必须要先确定得到的结果是什么，才能做推断,不能对没有初始化值的变量做推断。

在用`std::cin`的时候，给的类型是`istream`，所以自动推断会推出这个类型，肯定不是你想要的结果。

`auto`不会保留`const`的修饰，所以如果需要保留，用`const auto`。

---

### auto的尾随返回值

这其实一点都不`auto`，只是为了让函数名对齐，然后用`->`给出返回类型罢了。

```cpp
auto add(int x, int y) -> int;
auto divide(double x, double y) -> double;
auto printSomething() -> void;
auto generateSubstring(const std::string &s, int start, int len) -> std::string;
```