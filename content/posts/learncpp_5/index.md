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

