+++
date = '2025-10-13T08:25:04+08:00'
draft = false
title = 'cpp学习笔记(6)'
+++

## std::vector

此向量非彼向量。

### 对于字符串

推荐使用`string_view`配合C风格的字符串，这样效率最高，只发生一次堆内存分配。

```cpp
std::vector<std::string_view> names{ "Alex", "Betty", "Caroline", "Dave","Emily","Fred","Greg","Holly" };
```
### 列表初始化器

- `std::vector vec(3)`会初始化一个全0，长度为3的向量；
- `std::vecotr vec(2,3)`会初始化一个长度2，值都为3的向量。
- 但是`std::vector vec({3})`会初始化一个长度1值为3的向量。

因为给出单参数的时候，会优先调用列表初始化器，这个初始化器的行为是初始化长度为参数的向量。

### 下标

当时设计让`size_t`是一个无符号的整数，从现在看来是一个错误，因为下标访问最容易导致环绕，最好的办法是不使用下标访问而是迭代器，次选是使用C风格的访问`.data()`。然后全部使用有符号整数。

### for-each

推荐使用这些：

1. **修改元素副本**：`auto`
2. **修改原始元素**：`auto`
3. **只需要查看**：`const auto&`（大多数情况）

反向查看：使用`std::view::reverse()`

### 容量和长度

容量是分配给向量的内存，长度是实际使用的部分。

`pop`的时候长度减少容量不变；`push`时如果遇到容量瓶颈，会自动复制扩容（2/1.5）倍。

`resize`成员函数会同时改变容量和长度，`reserve`只改变容量。

`emplace_back`会显示调用构造函数，直接在堆上预留的内存构建对象，如果是是临时对象，那么要注意如果有`explicit`那么不能执行隐式转换。而`push_back`会发生一次拷贝。

在 `make_unique` 下，始终会产生一次拷贝，此时两者表现一致。

## std::array

`array` 大部分功能都与 `constexpr` 兼容。

在 `constexpr` 表达式执行的从 `unsign` 到 `sign` 的转换是允许的，因为编译器对此信任程度很高。

### .at()、[]和std::get()

- **`.at()`**: 运行时边界检查。(C++17后编译时检查)
- **`std::get<index>(arr)`**: 编译时边界检查。
- **`[]`**: 不进行边界检查，C++11后可为 `constexpr` 。

对于现代C++来说， `.at` 是更安全的选择。

因为会在越界访问的时候抛出异常。而 `[]` 不会进行越界检查。

### 用模板创建数组

```cpp

template<typename T, size_t N>
void passByRef(const std::array<T,N>& arr){
    static_assert(N!=0);
    std::cout<<arr[N];
}
```

由于模板参数是编译时常量，所以可以用 `static_assert` ，同时，更加推荐把这两句用 `std::get<N>(arr)` 替代。

在C++20，可以把 `size_t` 替换成 `auto` 。

### 在函数内返回array

由于 `array` 是在栈上分配的，那么一般来说会执行返回值优化，但是移动语义就没有意义（因为不是在堆上分配的就不能仅转移指针）。如果在C++17之前为了避免不确定性，那用 `vector` ？但是怎么感觉开销在堆上更大了说...

### 初始化聚合数组

列表初始化，但是兼容C带来的技术债。

```cpp
constexpr std::array<House, 3> houses { // 1. 初始化 std::array
    { // 2. 初始化底层 C 风格数组 (元素列表)
        { 13, 1, 7 }, // 3. 初始化第一个 House 结构体
        { 14, 2, 5 }, // 3. 初始化第二个 House 结构体
        { 15, 2, 4 }  // 3. 初始化第三个 House 结构体
    }
};
```

此时不使用CTAD，但是必须手动指定模板参数，或者，指定每一个元素的类型，此时可以CTAD：

```cpp
constexpr std::array houses { // 1. 初始化 std::array
    {
        Horse{ 13, 1, 7 }, // 3. 初始化第一个 House 结构体
        Horse{ 14, 2, 5 }, // 3. 初始化第二个 House 结构体
        Horse{ 15, 2, 4 }  // 3. 初始化第三个 House 结构体
    }
};
```

### reference_wrapper

容器中不能给模板传入 `int&` 但是可以传入一个 `std::reference_wrapper<int>` 起到同样的作用，或者直接用 `std::ref()` `std::cref()` 直接把变量转换成引用。

## 迭代器

迭代器一般使用 `!=end` 来判断是否到达末尾，因为不是所有迭代器都可以比较。

其本身是一个指针，指向当前的容器元素。

写的 `range based for` 实际上就是迭代器的语法糖。

## algorithems 库

这是一个算法库，用于偷懒（不是

### 补充知识

二元谓词：就是接受两个参数，返回一个布尔值的函数。

在算法库中，二元谓词都需要弱序，即非自反性(自己不能小于自己)，非对称性(a小于b，那么b不能小于a)，传递性。

对于 `Comp` 这个类型，我们假设前一个参数是 `a`，后一个是 `b`。那么有：

> 对 `a` 和 `b` 进行某种运算，如果希望最后算法需要保持 `a` 排在 `b` 的前面，那么就返回 `true`；如果算法认为 `a` **不**应该排在 `b` 的前面，那么就返回 `false`。

最简单的办法是，假设已经按照一个顺序排列，然后取出前两个元素为 `a` 和 `b`，将他们放入表达式，如果返回 `true`，那么这就是你要的顺序，为 `false` 则是另外一个顺序。

### std::sort

sort 有第三个参数，传入一个二元谓词，在 `cppreference` 中类型为 `Comp` ,如果是一个函数的话，只需要传地址所以不用 `()`。这个函数必须严格弱序的。

### std::for_each

`foreach` 可以用于方便的遍历可以迭代的容器。给定开始和结束的迭代器，和要调用的函数地址（这个函数只能传入一个参数，可用 `auto` ），就可以自动迭代。

同时和 `std::next` 配合使用，可以跳过一部分迭代器，获得很高的灵活性。这时候就有了比基于范围的 `for` 循环更加灵活。

### ranges (C++20)

从C++20开始，很多算法添加了对应的重载，直接传入容器的地址就可以实现操作，即 `std::ranges::for_each(arr)`。

## 函数指针

C的函数指针如果不用 `typedef`将会非常复杂，而C++提供了一个模板，以一个传入 `int, int` 返回 `int` 的函数指针为例：

```cpp
#include<functional>
std::function<int(int, int)> ptr {&foo};
std::function<int(int, int)> bar(){
    // some implementation
}
```