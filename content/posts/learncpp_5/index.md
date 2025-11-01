+++
date = '2025-09-29T08:25:14+08:00'
draft = false
title = 'cpp学习笔记(5)'
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

### 构造函数

构造函数用于初始化类，在此我们可以手动指定成员变量如何初始化。

#### 转化构造函数

转化构造函数其实就是特殊的构造函数，其只拥有一个参数。如果传入一个该参数类型的变量，那么就会自动把这这个变量转化成类。

#### 默认构造函数

```cpp
class Foo{
    int m_a;
    int m_b{};
    
  public:
    Foo () = default; //可以显式的声明构造函数为默认构造函数，此时m_a会被默认初始化为0。
    Foo () {} //用户自己初始化，但是空初始化，此时m_a不会被初始化，是垃圾值。
}
```

#### 委托构造函数

在一个构造函数的`:`后面写上参数更多的重载构造函数，可以用另一个构造函数来初始化，但是此构造函数就不能再初始化成员变量。

尽量不要使用太多的构造函数。

#### 复制构造函数

复制构造函数的参数必须是引用，要不然就会发生无限递归的调用复制函数。

复制构造函数不应用于复制以外的意图，因为编译器可能会发生复制省略(copy elision)

### explicit关键字

禁止隐式转换：从单个参数隐式转换成类对象；从列表`{xxx,xxx}`转换成类对象。

在具有单个参数的构造函数前加入，避免编译器执行隐式转换。

由于C++对于用户定义的转换，只允许转换一次，所以下面的代码会报错：

```cpp
#include <iostream>
#include <string>
#include <string_view>

class Employee
{
private:
    std::string m_name{};

public:
    Employee(std::string_view name)
        : m_name{ name }
    {
    }

    const std::string& getName() const { return m_name; }
};

void printEmployee(Employee e) // has an Employee parameter
{
    std::cout << e.getName();
}

int main()
{
    // 此时要经历两次转换：C-Style string -> string_view -> class Employee
    printEmployee("Joe"); // compile error
    
    // 修正：
    // 方法1:
    // using std::literals;
    // printEmployee("Joe"sv);
    // 方法2:
    // printEmployee(Employee{"Joe"});


    return 0;
}
```

不对复制/移动构造函数使用`explicit`，因为他们不执行隐式转换。

如果转换的时候两者等效且零开销，可以不使用`explicit`。

比如：

1. `const char*` -> `string_view`
2. `string` -> `string_view`

### constexpr问题

从C++14开始，`constexpr`修饰函数仅仅是作为编译时求值的提示，如果传入的变量不是一个`constexpr`，那么这个函数就具有运行时的上下文，`constexpr`修饰就不起作用。

对于`struct`，其作为一个聚合体，默认的构造函数无须加入`constexpr`就可以用它初始化一个类对象。但是对于`class`，就必须`public`，同时手动指定构造函数是`constexpr`，比如：

```cpp
Foo {
  public:
    constexpr Foo = default;
}
```

而`constexpr`修饰一个类对象的时候，如果涉及到的函数（构造函数、`setter`以及使用到的成员函数）都有`constexpr`修饰，表示这个类具有编译时的上下文，会让此对象成为一个编译时常量。在编译时如果此对象是用临时对象初始化的，对临时对象是可以修改的，但是一旦这个对象初始化完毕，那么就不再可以修改。

后续要访问此`constexpr`对象，那么所有的函数`()`后，都必须有`const`，保证不修改此对象。

参考(learncpp - 14.17)[https://www.learncpp.com/cpp-tutorial/constexpr-aggregates-and-classes/]

### this指针

`this`指针是一个`const`指针（顶层），指向当前操作的类。

`this`指针出现比引用早，不然它多少是个引用。

### 成员函数类外定义

成员函数可以在类外定义，要加上域访问解析符`::`。如果是类的正下方（`.h`中），前面加`inline`关键字以防止重复包含；如果是对应的cpp中，无须加`inline`。

默认参数在声明时给出。

### 类型模板参数

可以在类指定类型模板参数，不过如果成员函数先声明，然后在类外定义，那么需要单独再指定一次模板参数。

模板类外的成员函数要紧挨着类定义的下面。

注意：

1. 所有的模板函数都是默认内联的，所以就算在类外定义，已经隐式`inline`了。
2. 类外定义的函数的类型模板参数必须与类的一致。

传入类模板的参数，无须加`<T>`，因为已经在`Pair<T>::`作用域中了。

```cpp
template <typename T>
bool Pair<T>::isEqual(const Pair& pair) // note the parameter has type Pair, not Pair<T>
{
    return m_first == pair.m_first && m_second == pair.m_second;
}
```

### 静态成员变量

静态成员变量在所有实例化的对象都可用，具有相同的值，在未实例化的时候也可以使用，直接用类名和域访问解析符访问。

声明的时候，在类内加`static`关键字，类外定义不能加关键字。

位置：直接在类后面/类对应的`cpp`，头文件中可以加`inline`。

只有静态成员变量可以自动推断，普通的不允许。

用途：一个根据数量递增的ID

### 静态成员函数

静态成员函数用于访问静态全局变量。

有替代品：

- 命名空间：没有访问控制
- 静态全局类对象

### 友元

在被访问的类中声明，从而使得外部的类/函数能够访问`private`和`protected`的对象。

#### 友元函数

在类中声明，自动成为非成员的函数，类外定义。

此项特性对于运算符重载非常有用。

#### 友元类

直接在类内定义。