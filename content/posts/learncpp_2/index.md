+++
date = '2025-09-19T19:13:57+08:00'
draft = false
title = 'cpp学习笔记(2)'
lastmod = '2025-09-25T10:55:18+08:00'
+++
## 符号变量

magic number这个词，我一直认为是大家约定好了的一组数，但是这里是不同的含义。

它指的是直接放在函数里面，没有任何交代的数据，使得程序更加难读。

所以做法一般是推荐用`const`修饰，如果标准高的话，`constexpr`，请。

## 字符串

从c开始那么久，都一直没认真了解过字符串，这会终于明白了`std::string`的一些基本操作。

众所周知，字符串里面不可避免包含空白字符，那么办法就是通过`std::getline()`，但是如果在`std::cin`之后使用，大概率这么传入`(std::cin, target)`是无效的，因为`cin`在读到空白字符之后会停止，并且把空白字符留在缓冲区，那么下一次读取的时候，直接就把一个`\n`传入了，所以你的字符串啥都没有。

问题解决是通过流操纵符`std::ws`（这个需要每次cin的时候都提供），控制如果一开始就读取到空白字符，那么就忽略掉这个字符继续读取后面的东西。

这时就很好的解决了读取到`\n`的问题，除非读取到下一个`\n`，那么`getline`才停止读取，此时字符串也成功存入了这一行。

怎么说呢，感觉比c先进一点点（？

## string_view

```cpp
// 用string_view指向string的话，不产生多余的拷贝，只是在初始化的时候拷贝进入string
std::string name {"John"}; //此处产生拷贝
std::string_view name_v {name}; // 不拷贝

// 实际上，是让string_view指向一个c风格的字符串，这个过程没有拷贝。
std::string_view name {"John"};
```
如果常量能够在编译时确定，那么就可以应用`constexpr`。很显然，前者是不可行的，后者可以。

---

> ⚠️ string_view的行为与普通的引用和指针不一致。


当用`string`来初始化`string_view`，然后`string`被修改之后，`string_view`并不会更新`string`的新长度。

如果要避免，得更新视图。（不知道智能指针是否有帮助？）

---

不建议用`string_view`来返回，除非它是用C式的字符串初始化的。

对于用`string_view`来说，推荐用法：

```cpp
std::string_view s{"aaa"sv};
```

实现零成本抽象，原因嘛，以后再补充...

## 对于流程控制的一些建议

对于只有两个分支的`if`，可以考虑用三元运算符`? :`。

如果表达式本身只有为`0/1`两种可能，那么就无须写`==`，直接把表达式扔上去即可。

## static与内部链接

在变量前加入`static`关键字，不仅仅会使变量在整个程序的生命周期有效，还会使得无法被外部文件访问此变量。

现代cpp已经不推荐使用此关键字了。转而替代的是匿名命名空间，后者可以实现里面的变量直接在当前文件访问，其他文件不可访问。

没加`static`的变量默认是全局变量，在别的文件使用`extern`引入，`const`默认就是内部变量。

> static的最佳用法

`static`最适合用于函数内的计数场景，比如调用了函数几次，只需在函数内声明一个静态局部变量即可。

不推荐使用此方法实现相同的输入不同的输出内容，这其实也不符合fp的原则。如果必须要这么用，那么最好的办法是将条件一起传入。[参考](https://www.learncpp.com/cpp-tutorial/static-local-variables/)

## inline关键字

从cpp17开始，完善了`inline`，使得`constexpr`对于编译时常量跨文件有了最佳解决方案。

`inline`本义其实指的是把函数展开到调用的地方，但是修饰`constexpr`时，它被赋予了不同的意义。

`inline`修饰`constexpr`特殊，当在多个文件中定义的时候，会告诉链接器从任意一份中取出一份定义，并且在所有文件中共享，同时并不违反ODR原则，这使得把`inline`放在文件头里面，就可以向引入这个头文件的所有源文件进行分发。

`inline`同时还可以修饰命名空间，修饰非匿名的命名空间可以使得本来需要域解析操作符的使用，直接被透传到全局的命名空间中去。

下面是一个嵌套的命名空间的例子，使得接口能够安全的对当前文件中的其他函数暴露：

```cpp
#include <iostream>

namespace V1 // declare a normal namespace named V1
{
    void doSomething()
    {
        std::cout << "V1\n";
    }
}

inline namespace V2 // declare an inline namespace named V2
{
    namespace // unnamed namespace
    {
        void doSomething() // has internal linkage
        {
            std::cout << "V2\n";
        }

    }
}

int main()
{
    V1::doSomething(); // calls the V1 version of doSomething()
    V2::doSomething(); // calls the V2 version of doSomething()

    doSomething(); // calls the inline version of doSomething() (which is V2)

    return 0;
}
```

`inline`作用于`V2`命名空间，使得内部内容能够无须域解析操作符，但是匿名命名空间保护性最强，使得内部内容只能有当前文件访问，无法暴露给外部文件。

> In modern C++, the term inline has evolved to mean “multiple definitions are allowed”.

总结下，`inline`除了内联的意义，其实还有：

1. 对于变量： 在头文件中定义，使得此头被多次引入的时候只使用共享的一次，避免每次都加载到文件，在头文件被多次引用的时候很有用(c++17)。
2. 对于函数：在头文件中定义的函数需要加（但是不推荐，等到后面看到类的构造函数再会来补充），声明的函数无须加。
3. 对于命名空间： 把某个命名空间中的内容暴露到全局的命名空间，使得其中内容访问无须加域解析操作符。

## using语句和using声明

语句指的是用一个命名空间，这个一般范围过大，不推荐，此处狠狠批评那些教用`using namespace std;`的人。

using声明是可以接受的，因为它比起别名更加清晰，而不是只让写代码的人看懂。