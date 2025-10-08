+++
date = '2025-09-29T08:25:14+08:00'
draft = true
title = 'Learncpp_5'
+++

## 枚举

枚举实现了内容与整形相关联的数据结构，是隐式的编译时常量。

枚举类型，枚举符和枚举变量。

枚举符会放入当前命名空间和其本身的命名空间中，如果是全局的枚举(unscoped),那么可以直接使用。

对枚举变量空初始化会使得枚举符是0，所以推荐把第一个枚举符设置成未知/无效。

枚举类用`enum class Name{};`定义，只能在其本身的作用域使用，无法被隐式转换成整数，在安全性上更优。

可以在需要的使用`using enum Name;`来简化使用(C++20)。

## 结构体

对其中某些参数进行初始化：

```cpp
struct Worker {
    int id{};
    int age{};
    double wage{};
};

Worker John { .id{1},.wage{5000}}; //部分列表初始化，age初始化为0，clangd有bug会警告

Worker John { .id{1},John.age, .wage{5000}}; //这样可以占位，一样使得age初始化为0
```

### 结构体模板

结构体当然也可以传入模板参数，不过在C++20更加完善，如果使用C++17，可能需要手动指定推断：

```cpp
template <typename T>
struct Pair
{
    T first{};
    T second{};
};

// Here's a deduction guide for our Pair (needed in C++17 only)
// Pair objects initialized with arguments of type T and T should deduce to Pair<T>
template <typename T>
Pair(T, T) -> Pair<T>;

int main()
{
    Pair<int> p1{ 1, 2 }; // explicitly specify class template Pair<int> (C++11 onward)
    Pair p2{ 1, 2 };      // CTAD used to deduce Pair<int> from the initializers (C++17)

    return 0;
}
```

可以为类型模板起别名：

```cpp
template <typename T>
using Coord = Pair<T>; // Coord is an alias for Pair<T>
```

## 类

类的成员变量，成员函数是隐式内联的，所以放在头文件中被多个源文件引用的时候，不违反ODR原则。

在类中，不强制声明语句位于使用之前，只要他们都在同一个类中即可。

调用常量类对象内部的函数，要将此成员函数声明为`const`。

```cpp
void foo() const {
  //...
}
```

`struct`和`class`仅有的差异：`struct`默认使用`public:`，而`class`默认使用`private:`。在继承性上也是这样。

`protect:`允许派生的类访问，其可见性介于两者之间。


### 推荐实践

1. 不要让成员函数返回引用，否则将会使得成员变量被以外修改。
2. 不推荐使用成员函数，为了使类的实现更加简洁。

### 成员初始化列表

现代C++使用成员初始化列表，而不是直接初始化列表。具体是：

```cpp
class Foo{
    int m_a{};
    int m_b{};
    
    Foo(int a, int b) : m_a{a}, m_b{b} {
        //other...
    }
}
```

以前(C++03)之前则是用的`()`直接初始化。

成员初始化的顺序和成员初始化列表无关，只跟泪中定义成员变量的顺序有关。

### `std::string_view`特殊处理

一个例子：

```cpp
#include <iostream>
#include <string>
#include <string_view>

class Ball
{
private:
	std::string m_color { "none" };
	double m_radius { 0.0 };

public:
	Ball(std::string_view color, double radius)
		: m_color { color }
		, m_radius { radius }
	{
	}

	const std::string& getColor() const { return m_color; }
	double getRadius() const { return m_radius; }
};

void print(const Ball& ball)
{
    std::cout << "Ball(" << ball.getColor() << ", " << ball.getRadius() << ")\n";
}

int main()
{
	Ball blue { "blue", 10.0 };
	print(blue);

	Ball red { "red", 12.0 };
	print(red);

	return 0;
}
```

> 为什么这里构造函数需要用`string_view`作为参数？不能用`const string&`来替换？

`string_view`提供了灵活性，如果选择后者，那么如果传入一个C语言的字面量字符串的时候，就必须在堆上构建临时的`string`对象，而这对性能开销很大；对于前者，永远不会构造临时对象，而是只有一个指针，在真正初始化的时候完成一次复制。(甚至后面还能用移动语义)

> 为什么`getter`不能像上面一样反过来？

因为在类内部的存储对象就是真正的`string`，给出它的引用使得外部访问的类型明确，不会造成歧义；同时也提示这个引用的生命周期是明确的————跟成员变量一致。