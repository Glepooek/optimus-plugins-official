# 第 5 章 · 栈与队列

> **来源声明**
>
> 本文提取自《Hello 算法》（Hello Algo）第 5 章「栈与队列」。
>
> - **原作者**：krahets
> - **书名**：Hello 算法（Hello Algo）
> - **版本**：1.3.0
> - **原书地址**：https://www.hello-algo.com/
> - **源码仓库**：https://github.com/krahets/hello-algo（tag `1.3.0`）
> - **许可证**：CC BY-NC-SA 4.0（全文见本目录 `LICENSE`）
> - **提取日期**：2026-08-29
>
> 本文为原书的演绎作品，依 SA 条款同样以 CC BY-NC-SA 4.0 授权，该授权独立于本仓库其余部分。
> 相对原书的改动：代码示例仅保留 C# 一种语言（原书含 12 种），图解未导出、原位置以指针指向原书。

---

> 📊 原书图：栈与队列（图解见 https://www.hello-algo.com/chapter_stack_and_queue/index/）

> **摘要**
>
> 栈如同叠猫猫，而队列就像猫猫排队。
>
> 两者分别代表先入后出和先入先出的逻辑关系。

## 5.1 栈

<u>栈（stack）</u>是一种遵循先入后出逻辑的线性数据结构。

我们可以将栈类比为桌面上的一摞盘子，规定每次只能移动一个盘子，那么想取出底部的盘子，则需要先将上面的盘子依次移走。我们将盘子替换为各种类型的元素（如整数、字符、对象等），就得到了栈这种数据结构。

如下图所示，我们把堆叠元素的顶部称为“栈顶”，底部称为“栈底”。将把元素添加到栈顶的操作叫作“入栈”，删除栈顶元素的操作叫作“出栈”。

> 📊 原书图：栈的先入后出规则（图解见 https://www.hello-algo.com/chapter_stack_and_queue/stack/）

### 栈的常用操作

栈的常用操作如下表所示，具体的方法名需要根据所使用的编程语言来确定。在此，我们以常见的 `push()`、`pop()`、`peek()` 命名为例。

<p align="center"> 表 <id> &nbsp; 栈的操作效率 </p>

| 方法     | 描述                   | 时间复杂度 |
| -------- | ---------------------- | ---------- |
| `push()` | 元素入栈（添加至栈顶） | $O(1)$     |
| `pop()`  | 栈顶元素出栈           | $O(1)$     |
| `peek()` | 访问栈顶元素           | $O(1)$     |

通常情况下，我们可以直接使用编程语言内置的栈类。然而，某些语言可能没有专门提供栈类，这时我们可以将该语言的“数组”或“链表”当作栈来使用，并在程序逻辑上忽略与栈无关的操作。

```csharp
/* 初始化栈 */
Stack<int> stack = new();

/* 元素入栈 */
stack.Push(1);
stack.Push(3);
stack.Push(2);
stack.Push(5);
stack.Push(4);

/* 访问栈顶元素 */
int peek = stack.Peek();

/* 元素出栈 */
int pop = stack.Pop();

/* 获取栈的长度 */
int size = stack.Count;

/* 判断是否为空 */
bool isEmpty = stack.Count == 0;
```

> **可视化运行**
>
> https://pythontutor.com/render.html#code=%22%22%22Driver%20Code%22%22%22%0Aif%20__name__%20%3D%3D%20%22__main__%22%3A%0A%20%20%20%20%23%20%E5%88%9D%E5%A7%8B%E5%8C%96%E6%A0%88%0A%20%20%20%20%23%20Python%20%E6%B2%A1%E6%9C%89%E5%86%85%E7%BD%AE%E7%9A%84%E6%A0%88%E7%B1%BB%EF%BC%8C%E5%8F%AF%E4%BB%A5%E6%8A%8A%20list%20%E5%BD%93%E4%BD%9C%E6%A0%88%E6%9D%A5%E4%BD%BF%E7%94%A8%0A%20%20%20%20stack%20%3D%20%5B%5D%0A%0A%20%20%20%20%23%20%E5%85%83%E7%B4%A0%E5%85%A5%E6%A0%88%0A%20%20%20%20stack.append%281%29%0A%20%20%20%20stack.append%283%29%0A%20%20%20%20stack.append%282%29%0A%20%20%20%20stack.append%285%29%0A%20%20%20%20stack.append%284%29%0A%20%20%20%20print%28%22%E6%A0%88%20stack%20%3D%22,%20stack%29%0A%0A%20%20%20%20%23%20%E8%AE%BF%E9%97%AE%E6%A0%88%E9%A1%B6%E5%85%83%E7%B4%A0%0A%20%20%20%20peek%20%3D%20stack%5B-1%5D%0A%20%20%20%20print%28%22%E6%A0%88%E9%A1%B6%E5%85%83%E7%B4%A0%20peek%20%3D%22,%20peek%29%0A%0A%20%20%20%20%23%20%E5%85%83%E7%B4%A0%E5%87%BA%E6%A0%88%0A%20%20%20%20pop%20%3D%20stack.pop%28%29%0A%20%20%20%20print%28%22%E5%87%BA%E6%A0%88%E5%85%83%E7%B4%A0%20pop%20%3D%22,%20pop%29%0A%20%20%20%20print%28%22%E5%87%BA%E6%A0%88%E5%90%8E%20stack%20%3D%22,%20stack%29%0A%0A%20%20%20%20%23%20%E8%8E%B7%E5%8F%96%E6%A0%88%E7%9A%84%E9%95%BF%E5%BA%A6%0A%20%20%20%20size%20%3D%20len%28stack%29%0A%20%20%20%20print%28%22%E6%A0%88%E7%9A%84%E9%95%BF%E5%BA%A6%20size%20%3D%22,%20size%29%0A%0A%20%20%20%20%23%20%E5%88%A4%E6%96%AD%E6%98%AF%E5%90%A6%E4%B8%BA%E7%A9%BA%0A%20%20%20%20is_empty%20%3D%20len%28stack%29%20%3D%3D%200%0A%20%20%20%20print%28%22%E6%A0%88%E6%98%AF%E5%90%A6%E4%B8%BA%E7%A9%BA%20%3D%22,%20is_empty%29&cumulative=false&curInstr=2&heapPrimitives=nevernest&mode=display&origin=opt-frontend.js&py=311&rawInputLstJSON=%5B%5D&textReferences=false

### 栈的实现

为了深入了解栈的运行机制，我们来尝试自己实现一个栈类。

栈遵循先入后出的原则，因此我们只能在栈顶添加或删除元素。然而，数组和链表都可以在任意位置添加和删除元素，**因此栈可以视为一种受限制的数组或链表**。换句话说，我们可以“屏蔽”数组或链表的部分无关操作，使其对外表现的逻辑符合栈的特性。

#### 基于链表的实现

使用链表实现栈时，我们可以将链表的头节点视为栈顶，尾节点视为栈底。

如下图所示，对于入栈操作，我们只需将元素插入链表头部，这种节点插入方法被称为“头插法”。而对于出栈操作，只需将头节点从链表中删除即可。

> 📊 原书图：基于链表实现栈的入栈出栈操作（3 张分步图：LinkedListStack、push()、pop()）（图解见 https://www.hello-algo.com/chapter_stack_and_queue/stack/）

以下是基于链表实现栈的示例代码：

```csharp
/* 基于链表实现的栈 */
class LinkedListStack {
ListNode? stackPeek;  // 将头节点作为栈顶
int stkSize = 0;   // 栈的长度

public LinkedListStack() {
    stackPeek = null;
}

/* 获取栈的长度 */
public int Size() {
    return stkSize;
}

/* 判断栈是否为空 */
public bool IsEmpty() {
    return Size() == 0;
}

/* 入栈 */
public void Push(int num) {
    ListNode node = new(num) {
        next = stackPeek
    };
    stackPeek = node;
    stkSize++;
}

/* 出栈 */
public int Pop() {
    int num = Peek();
    stackPeek = stackPeek!.next;
    stkSize--;
    return num;
}

/* 访问栈顶元素 */
public int Peek() {
    if (IsEmpty())
        throw new Exception();
    return stackPeek!.val;
}

/* 将 List 转化为 Array 并返回 */
public int[] ToArray() {
    if (stackPeek == null)
        return [];

    ListNode? node = stackPeek;
    int[] res = new int[Size()];
    for (int i = res.Length - 1; i >= 0; i--) {
        res[i] = node!.val;
        node = node.next;
    }
    return res;
}
}
```

#### 基于数组的实现

使用数组实现栈时，我们可以将数组的尾部作为栈顶。如下图所示，入栈与出栈操作分别对应在数组尾部添加元素与删除元素，时间复杂度都为 $O(1)$ 。

> 📊 原书图：基于数组实现栈的入栈出栈操作（3 张分步图：ArrayStack、push()、pop()）（图解见 https://www.hello-algo.com/chapter_stack_and_queue/stack/）

由于入栈的元素可能会源源不断地增加，因此我们可以使用动态数组，这样就无须自行处理数组扩容问题。以下为示例代码：

```csharp
/* 基于数组实现的栈 */
class ArrayStack {
List<int> stack;
public ArrayStack() {
    // 初始化列表（动态数组）
    stack = [];
}

/* 获取栈的长度 */
public int Size() {
    return stack.Count;
}

/* 判断栈是否为空 */
public bool IsEmpty() {
    return Size() == 0;
}

/* 入栈 */
public void Push(int num) {
    stack.Add(num);
}

/* 出栈 */
public int Pop() {
    if (IsEmpty())
        throw new Exception();
    var val = Peek();
    stack.RemoveAt(Size() - 1);
    return val;
}

/* 访问栈顶元素 */
public int Peek() {
    if (IsEmpty())
        throw new Exception();
    return stack[Size() - 1];
}

/* 将 List 转化为 Array 并返回 */
public int[] ToArray() {
    return [.. stack];
}
}
```

### 两种实现对比

**支持操作**

两种实现都支持栈定义中的各项操作。数组实现额外支持随机访问，但这已超出了栈的定义范畴，因此一般不会用到。

**时间效率**

在基于数组的实现中，入栈和出栈操作都在预先分配好的连续内存中进行，具有很好的缓存本地性，因此效率较高。然而，如果入栈时超出数组容量，会触发扩容机制，导致该次入栈操作的时间复杂度变为 $O(n)$ 。

在基于链表的实现中，链表的扩容非常灵活，不存在上述数组扩容时效率降低的问题。但是，入栈操作需要初始化节点对象并修改指针，因此效率相对较低。不过，如果入栈元素本身就是节点对象，那么可以省去初始化步骤，从而提高效率。

综上所述，当入栈与出栈操作的元素是基本数据类型时，例如 `int` 或 `double` ，我们可以得出以下结论。

- 基于数组实现的栈在触发扩容时效率会降低，但由于扩容是低频操作，因此平均效率更高。
- 基于链表实现的栈可以提供更加稳定的效率表现。

**空间效率**

在初始化列表时，系统会为列表分配“初始容量”，该容量可能超出实际需求；并且，扩容机制通常是按照特定倍率（例如 2 倍）进行扩容的，扩容后的容量也可能超出实际需求。因此，**基于数组实现的栈可能造成一定的空间浪费**。

然而，由于链表节点需要额外存储指针，**因此链表节点占用的空间相对较大**。

综上，我们不能简单地确定哪种实现更加节省内存，需要针对具体情况进行分析。

### 栈的典型应用

- **浏览器中的后退与前进、软件中的撤销与反撤销**。每当我们打开新的网页，浏览器就会对上一个网页执行入栈，这样我们就可以通过后退操作回到上一个网页。后退操作实际上是在执行出栈。如果要同时支持后退和前进，那么需要两个栈来配合实现。
- **程序内存管理**。每次调用函数时，系统都会在栈顶添加一个栈帧，用于记录函数的上下文信息。在递归函数中，向下递推阶段会不断执行入栈操作，而向上回溯阶段则会不断执行出栈操作。

## 5.2 队列

<u>队列（queue）</u>是一种遵循先入先出规则的线性数据结构。顾名思义，队列模拟了排队现象，即新来的人不断加入队列尾部，而位于队列头部的人逐个离开。

如下图所示，我们将队列头部称为“队首”，尾部称为“队尾”，将把元素加入队尾的操作称为“入队”，删除队首元素的操作称为“出队”。

> 📊 原书图：队列的先入先出规则（图解见 https://www.hello-algo.com/chapter_stack_and_queue/queue/）

### 队列常用操作

队列的常见操作如下表所示。需要注意的是，不同编程语言的方法名称可能会有所不同。我们在此采用与栈相同的方法命名。

<p align="center"> 表 <id> &nbsp; 队列操作效率 </p>

| 方法名   | 描述                         | 时间复杂度 |
| -------- | ---------------------------- | ---------- |
| `push()` | 元素入队，即将元素添加至队尾 | $O(1)$     |
| `pop()`  | 队首元素出队                 | $O(1)$     |
| `peek()` | 访问队首元素                 | $O(1)$     |

我们可以直接使用编程语言中现成的队列类：

```csharp
/* 初始化队列 */
Queue<int> queue = new();

/* 元素入队 */
queue.Enqueue(1);
queue.Enqueue(3);
queue.Enqueue(2);
queue.Enqueue(5);
queue.Enqueue(4);

/* 访问队首元素 */
int peek = queue.Peek();

/* 元素出队 */
int pop = queue.Dequeue();

/* 获取队列的长度 */
int size = queue.Count;

/* 判断队列是否为空 */
bool isEmpty = queue.Count == 0;
```

> **可视化运行**
>
> https://pythontutor.com/render.html#code=from%20collections%20import%20deque%0A%0A%22%22%22Driver%20Code%22%22%22%0Aif%20__name__%20%3D%3D%20%22__main__%22%3A%0A%20%20%20%20%23%20%E5%88%9D%E5%A7%8B%E5%8C%96%E9%98%9F%E5%88%97%0A%20%20%20%20%23%20%E5%9C%A8%20Python%20%E4%B8%AD%EF%BC%8C%E6%88%91%E4%BB%AC%E4%B8%80%E8%88%AC%E5%B0%86%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%E7%B1%BB%20deque%20%E7%9C%8B%E4%BD%9C%E9%98%9F%E5%88%97%E4%BD%BF%E7%94%A8%0A%20%20%20%20%23%20%E8%99%BD%E7%84%B6%20queue.Queue%28%29%20%E6%98%AF%E7%BA%AF%E6%AD%A3%E7%9A%84%E9%98%9F%E5%88%97%E7%B1%BB%EF%BC%8C%E4%BD%86%E4%B8%8D%E5%A4%AA%E5%A5%BD%E7%94%A8%0A%20%20%20%20que%20%3D%20deque%28%29%0A%0A%20%20%20%20%23%20%E5%85%83%E7%B4%A0%E5%85%A5%E9%98%9F%0A%20%20%20%20que.append%281%29%0A%20%20%20%20que.append%283%29%0A%20%20%20%20que.append%282%29%0A%20%20%20%20que.append%285%29%0A%20%20%20%20que.append%284%29%0A%20%20%20%20print%28%22%E9%98%9F%E5%88%97%20que%20%3D%22,%20que%29%0A%0A%20%20%20%20%23%20%E8%AE%BF%E9%97%AE%E9%98%9F%E9%A6%96%E5%85%83%E7%B4%A0%0A%20%20%20%20front%20%3D%20que%5B0%5D%0A%20%20%20%20print%28%22%E9%98%9F%E9%A6%96%E5%85%83%E7%B4%A0%20front%20%3D%22,%20front%29%0A%0A%20%20%20%20%23%20%E5%85%83%E7%B4%A0%E5%87%BA%E9%98%9F%0A%20%20%20%20pop%20%3D%20que.popleft%28%29%0A%20%20%20%20print%28%22%E5%87%BA%E9%98%9F%E5%85%83%E7%B4%A0%20pop%20%3D%22,%20pop%29%0A%20%20%20%20print%28%22%E5%87%BA%E9%98%9F%E5%90%8E%20que%20%3D%22,%20que%29%0A%0A%20%20%20%20%23%20%E8%8E%B7%E5%8F%96%E9%98%9F%E5%88%97%E7%9A%84%E9%95%BF%E5%BA%A6%0A%20%20%20%20size%20%3D%20len%28que%29%0A%20%20%20%20print%28%22%E9%98%9F%E5%88%97%E9%95%BF%E5%BA%A6%20size%20%3D%22,%20size%29%0A%0A%20%20%20%20%23%20%E5%88%A4%E6%96%AD%E9%98%9F%E5%88%97%E6%98%AF%E5%90%A6%E4%B8%BA%E7%A9%BA%0A%20%20%20%20is_empty%20%3D%20len%28que%29%20%3D%3D%200%0A%20%20%20%20print%28%22%E9%98%9F%E5%88%97%E6%98%AF%E5%90%A6%E4%B8%BA%E7%A9%BA%20%3D%22,%20is_empty%29&cumulative=false&curInstr=3&heapPrimitives=nevernest&mode=display&origin=opt-frontend.js&py=311&rawInputLstJSON=%5B%5D&textReferences=false

### 队列实现

为了实现队列，我们需要一种数据结构，可以在一端添加元素，并在另一端删除元素，链表和数组都符合要求。

#### 基于链表的实现

如下图所示，我们可以将链表的“头节点”和“尾节点”分别视为“队首”和“队尾”，规定队尾仅可添加节点，队首仅可删除节点。

> 📊 原书图：基于链表实现队列的入队出队操作（3 张分步图：LinkedListQueue、push()、pop()）（图解见 https://www.hello-algo.com/chapter_stack_and_queue/queue/）

以下是用链表实现队列的代码：

```csharp
/* 基于链表实现的队列 */
class LinkedListQueue {
ListNode? front, rear;  // 头节点 front ，尾节点 rear 
int queSize = 0;

public LinkedListQueue() {
    front = null;
    rear = null;
}

/* 获取队列的长度 */
public int Size() {
    return queSize;
}

/* 判断队列是否为空 */
public bool IsEmpty() {
    return Size() == 0;
}

/* 入队 */
public void Push(int num) {
    // 在尾节点后添加 num
    ListNode node = new(num);
    // 如果队列为空，则令头、尾节点都指向该节点
    if (front == null) {
        front = node;
        rear = node;
        // 如果队列不为空，则将该节点添加到尾节点后
    } else if (rear != null) {
        rear.next = node;
        rear = node;
    }
    queSize++;
}

/* 出队 */
public int Pop() {
    int num = Peek();
    // 删除头节点
    front = front?.next;
    queSize--;
    return num;
}

/* 访问队首元素 */
public int Peek() {
    if (IsEmpty())
        throw new Exception();
    return front!.val;
}

/* 将链表转化为 Array 并返回 */
public int[] ToArray() {
    if (front == null)
        return [];

    ListNode? node = front;
    int[] res = new int[Size()];
    for (int i = 0; i < res.Length; i++) {
        res[i] = node!.val;
        node = node.next;
    }
    return res;
}
}
```

#### 基于数组的实现

在数组中删除首元素的时间复杂度为 $O(n)$ ，这会导致出队操作效率较低。然而，我们可以采用以下巧妙方法来避免这个问题。

我们可以使用一个变量 `front` 指向队首元素的索引，并维护一个变量 `size` 用于记录队列长度。定义 `rear = front + size` ，这个公式计算出的 `rear` 指向队尾元素之后的下一个位置。

基于此设计，**数组中包含元素的有效区间为 `[front, rear - 1]`**，各种操作的实现方法如下图所示。

- 入队操作：将输入元素赋值给 `rear` 索引处，并将 `size` 增加 1 。
- 出队操作：只需将 `front` 增加 1 ，并将 `size` 减少 1 。

可以看到，入队和出队操作都只需进行一次操作，时间复杂度均为 $O(1)$ 。

> 📊 原书图：基于数组实现队列的入队出队操作（3 张分步图：ArrayQueue、push()、pop()）（图解见 https://www.hello-algo.com/chapter_stack_and_queue/queue/）

你可能会发现一个问题：在不断进行入队和出队的过程中，`front` 和 `rear` 都在向右移动，**当它们到达数组尾部时就无法继续移动了**。为了解决此问题，我们可以将数组视为首尾相接的“环形数组”。

对于环形数组，我们需要让 `front` 或 `rear` 在越过数组尾部时，直接回到数组头部继续遍历。这种周期性规律可以通过“取余操作”来实现，代码如下所示：

```csharp
/* 基于环形数组实现的队列 */
class ArrayQueue {
int[] nums;  // 用于存储队列元素的数组
int front;   // 队首指针，指向队首元素
int queSize; // 队列长度

public ArrayQueue(int capacity) {
    nums = new int[capacity];
    front = queSize = 0;
}

/* 获取队列的容量 */
int Capacity() {
    return nums.Length;
}

/* 获取队列的长度 */
public int Size() {
    return queSize;
}

/* 判断队列是否为空 */
public bool IsEmpty() {
    return queSize == 0;
}

/* 入队 */
public void Push(int num) {
    if (queSize == Capacity()) {
        Console.WriteLine("队列已满");
        return;
    }
    // 计算队尾指针，指向队尾索引 + 1
    // 通过取余操作实现 rear 越过数组尾部后回到头部
    int rear = (front + queSize) % Capacity();
    // 将 num 添加至队尾
    nums[rear] = num;
    queSize++;
}

/* 出队 */
public int Pop() {
    int num = Peek();
    // 队首指针向后移动一位，若越过尾部，则返回到数组头部
    front = (front + 1) % Capacity();
    queSize--;
    return num;
}

/* 访问队首元素 */
public int Peek() {
    if (IsEmpty())
        throw new Exception();
    return nums[front];
}

/* 返回数组 */
public int[] ToArray() {
    // 仅转换有效长度范围内的列表元素
    int[] res = new int[queSize];
    for (int i = 0, j = front; i < queSize; i++, j++) {
        res[i] = nums[j % this.Capacity()];
    }
    return res;
}
}
```

以上实现的队列仍然具有局限性：其长度不可变。然而，这个问题不难解决，我们可以将数组替换为动态数组，从而引入扩容机制。有兴趣的读者可以尝试自行实现。

两种实现的对比结论与栈一致，在此不再赘述。

### 队列典型应用

- **淘宝订单**。购物者下单后，订单将加入队列中，系统随后会根据顺序处理队列中的订单。在双十一期间，短时间内会产生海量订单，高并发成为工程师们需要重点攻克的问题。
- **各类待办事项**。任何需要实现“先来后到”功能的场景，例如打印机的任务队列、餐厅的出餐队列等，队列在这些场景中可以有效地维护处理顺序。

## 5.3 双向队列

在队列中，我们仅能删除头部元素或在尾部添加元素。如下图所示，<u>双向队列（double-ended queue）</u>提供了更高的灵活性，允许在头部和尾部执行元素的添加或删除操作。

> 📊 原书图：双向队列的操作（图解见 https://www.hello-algo.com/chapter_stack_and_queue/deque/）

### 双向队列常用操作

双向队列的常用操作如下表所示，具体的方法名称需要根据所使用的编程语言来确定。

<p align="center"> 表 <id> &nbsp; 双向队列操作效率 </p>

| 方法名         | 描述             | 时间复杂度 |
| -------------- | ---------------- | ---------- |
| `push_first()` | 将元素添加至队首 | $O(1)$     |
| `push_last()`  | 将元素添加至队尾 | $O(1)$     |
| `pop_first()`  | 删除队首元素     | $O(1)$     |
| `pop_last()`   | 删除队尾元素     | $O(1)$     |
| `peek_first()` | 访问队首元素     | $O(1)$     |
| `peek_last()`  | 访问队尾元素     | $O(1)$     |

同样地，我们可以直接使用编程语言中已实现的双向队列类：

```csharp
/* 初始化双向队列 */
// 在 C# 中，将链表 LinkedList 看作双向队列来使用
LinkedList<int> deque = new();

/* 元素入队 */
deque.AddLast(2);   // 添加至队尾
deque.AddLast(5);
deque.AddLast(4);
deque.AddFirst(3);  // 添加至队首
deque.AddFirst(1);

/* 访问元素 */
int peekFirst = deque.First.Value;  // 队首元素
int peekLast = deque.Last.Value;    // 队尾元素

/* 元素出队 */
deque.RemoveFirst();  // 队首元素出队
deque.RemoveLast();   // 队尾元素出队

/* 获取双向队列的长度 */
int size = deque.Count;

/* 判断双向队列是否为空 */
bool isEmpty = deque.Count == 0;
```

> **可视化运行**
>
> https://pythontutor.com/render.html#code=from%20collections%20import%20deque%0A%0A%22%22%22Driver%20Code%22%22%22%0Aif%20__name__%20%3D%3D%20%22__main__%22%3A%0A%20%20%20%20%23%20%E5%88%9D%E5%A7%8B%E5%8C%96%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%0A%20%20%20%20deq%20%3D%20deque%28%29%0A%0A%20%20%20%20%23%20%E5%85%83%E7%B4%A0%E5%85%A5%E9%98%9F%0A%20%20%20%20deq.append%282%29%20%20%23%20%E6%B7%BB%E5%8A%A0%E8%87%B3%E9%98%9F%E5%B0%BE%0A%20%20%20%20deq.append%285%29%0A%20%20%20%20deq.append%284%29%0A%20%20%20%20deq.appendleft%283%29%20%20%23%20%E6%B7%BB%E5%8A%A0%E8%87%B3%E9%98%9F%E9%A6%96%0A%20%20%20%20deq.appendleft%281%29%0A%20%20%20%20print%28%22%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%20deque%20%3D%22,%20deq%29%0A%0A%20%20%20%20%23%20%E8%AE%BF%E9%97%AE%E5%85%83%E7%B4%A0%0A%20%20%20%20front%20%3D%20deq%5B0%5D%20%20%23%20%E9%98%9F%E9%A6%96%E5%85%83%E7%B4%A0%0A%20%20%20%20print%28%22%E9%98%9F%E9%A6%96%E5%85%83%E7%B4%A0%20front%20%3D%22,%20front%29%0A%20%20%20%20rear%20%3D%20deq%5B-1%5D%20%20%23%20%E9%98%9F%E5%B0%BE%E5%85%83%E7%B4%A0%0A%20%20%20%20print%28%22%E9%98%9F%E5%B0%BE%E5%85%83%E7%B4%A0%20rear%20%3D%22,%20rear%29%0A%0A%20%20%20%20%23%20%E5%85%83%E7%B4%A0%E5%87%BA%E9%98%9F%0A%20%20%20%20pop_front%20%3D%20deq.popleft%28%29%20%20%23%20%E9%98%9F%E9%A6%96%E5%85%83%E7%B4%A0%E5%87%BA%E9%98%9F%0A%20%20%20%20print%28%22%E9%98%9F%E9%A6%96%E5%87%BA%E9%98%9F%E5%85%83%E7%B4%A0%20%20pop_front%20%3D%22,%20pop_front%29%0A%20%20%20%20print%28%22%E9%98%9F%E9%A6%96%E5%87%BA%E9%98%9F%E5%90%8E%20deque%20%3D%22,%20deq%29%0A%20%20%20%20pop_rear%20%3D%20deq.pop%28%29%20%20%23%20%E9%98%9F%E5%B0%BE%E5%85%83%E7%B4%A0%E5%87%BA%E9%98%9F%0A%20%20%20%20print%28%22%E9%98%9F%E5%B0%BE%E5%87%BA%E9%98%9F%E5%85%83%E7%B4%A0%20%20pop_rear%20%3D%22,%20pop_rear%29%0A%20%20%20%20print%28%22%E9%98%9F%E5%B0%BE%E5%87%BA%E9%98%9F%E5%90%8E%20deque%20%3D%22,%20deq%29%0A%0A%20%20%20%20%23%20%E8%8E%B7%E5%8F%96%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%E7%9A%84%E9%95%BF%E5%BA%A6%0A%20%20%20%20size%20%3D%20len%28deq%29%0A%20%20%20%20print%28%22%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%E9%95%BF%E5%BA%A6%20size%20%3D%22,%20size%29%0A%0A%20%20%20%20%23%20%E5%88%A4%E6%96%AD%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%E6%98%AF%E5%90%A6%E4%B8%BA%E7%A9%BA%0A%20%20%20%20is_empty%20%3D%20len%28deq%29%20%3D%3D%200%0A%20%20%20%20print%28%22%E5%8F%8C%E5%90%91%E9%98%9F%E5%88%97%E6%98%AF%E5%90%A6%E4%B8%BA%E7%A9%BA%20%3D%22,%20is_empty%29&cumulative=false&curInstr=3&heapPrimitives=nevernest&mode=display&origin=opt-frontend.js&py=311&rawInputLstJSON=%5B%5D&textReferences=false

### 双向队列实现 *

双向队列的实现与队列类似，可以选择链表或数组作为底层数据结构。

#### 基于双向链表的实现

回顾上一节内容，我们使用普通单向链表来实现队列，因为它可以方便地删除头节点（对应出队操作）和在尾节点后添加新节点（对应入队操作）。

对于双向队列而言，头部和尾部都可以执行入队和出队操作。换句话说，双向队列需要实现另一个对称方向的操作。为此，我们采用“双向链表”作为双向队列的底层数据结构。

如下图所示，我们将双向链表的头节点和尾节点视为双向队列的队首和队尾，同时实现在两端添加和删除节点的功能。

> 📊 原书图：基于链表实现双向队列的入队出队操作（5 张分步图：LinkedListDeque、push_last()、push_first()、pop_last()、pop_first()）（图解见 https://www.hello-algo.com/chapter_stack_and_queue/deque/）

实现代码如下所示：

```csharp
/* 基于双向链表实现的双向队列 */
public class LinkedListDeque {
ListNode? front, rear; // 头节点 front, 尾节点 rear
int queSize = 0;      // 双向队列的长度

public LinkedListDeque() {
    front = null;
    rear = null;
}

/* 获取双向队列的长度 */
public int Size() {
    return queSize;
}

/* 判断双向队列是否为空 */
public bool IsEmpty() {
    return Size() == 0;
}

/* 入队操作 */
void Push(int num, bool isFront) {
    ListNode node = new(num);
    // 若链表为空，则令 front 和 rear 都指向 node
    if (IsEmpty()) {
        front = node;
        rear = node;
    }
    // 队首入队操作
    else if (isFront) {
        // 将 node 添加至链表头部
        front!.prev = node;
        node.next = front;
        front = node; // 更新头节点                           
    }
    // 队尾入队操作
    else {
        // 将 node 添加至链表尾部
        rear!.next = node;
        node.prev = rear;
        rear = node;  // 更新尾节点
    }

    queSize++; // 更新队列长度
}

/* 队首入队 */
public void PushFirst(int num) {
    Push(num, true);
}

/* 队尾入队 */
public void PushLast(int num) {
    Push(num, false);
}

/* 出队操作 */
int? Pop(bool isFront) {
    if (IsEmpty())
        throw new Exception();
    int? val;
    // 队首出队操作
    if (isFront) {
        val = front?.val; // 暂存头节点值
        // 删除头节点
        ListNode? fNext = front?.next;
        if (fNext != null) {
            fNext.prev = null;
            front!.next = null;
        }
        front = fNext;   // 更新头节点
    }
    // 队尾出队操作
    else {
        val = rear?.val;  // 暂存尾节点值
        // 删除尾节点
        ListNode? rPrev = rear?.prev;
        if (rPrev != null) {
            rPrev.next = null;
            rear!.prev = null;
        }
        rear = rPrev;    // 更新尾节点
    }

    queSize--; // 更新队列长度
    return val;
}

/* 队首出队 */
public int? PopFirst() {
    return Pop(true);
}

/* 队尾出队 */
public int? PopLast() {
    return Pop(false);
}

/* 访问队首元素 */
public int? PeekFirst() {
    if (IsEmpty())
        throw new Exception();
    return front?.val;
}

/* 访问队尾元素 */
public int? PeekLast() {
    if (IsEmpty())
        throw new Exception();
    return rear?.val;
}

/* 返回数组用于打印 */
public int?[] ToArray() {
    ListNode? node = front;
    int?[] res = new int?[Size()];
    for (int i = 0; i < res.Length; i++) {
        res[i] = node?.val;
        node = node?.next;
    }

    return res;
}
}
```

#### 基于数组的实现

如下图所示，与基于数组实现队列类似，我们也可以使用环形数组来实现双向队列。

> 📊 原书图：基于数组实现双向队列的入队出队操作（5 张分步图：ArrayDeque、push_last()、push_first()、pop_last()、pop_first()）（图解见 https://www.hello-algo.com/chapter_stack_and_queue/deque/）

在队列的实现基础上，仅需增加“队首入队”和“队尾出队”的方法：

```csharp
/* 基于环形数组实现的双向队列 */
public class ArrayDeque {
int[] nums;  // 用于存储双向队列元素的数组
int front;   // 队首指针，指向队首元素
int queSize; // 双向队列长度

/* 构造方法 */
public ArrayDeque(int capacity) {
    nums = new int[capacity];
    front = queSize = 0;
}

/* 获取双向队列的容量 */
int Capacity() {
    return nums.Length;
}

/* 获取双向队列的长度 */
public int Size() {
    return queSize;
}

/* 判断双向队列是否为空 */
public bool IsEmpty() {
    return queSize == 0;
}

/* 计算环形数组索引 */
int Index(int i) {
    // 通过取余操作实现数组首尾相连
    // 当 i 越过数组尾部后，回到头部
    // 当 i 越过数组头部后，回到尾部
    return (i + Capacity()) % Capacity();
}

/* 队首入队 */
public void PushFirst(int num) {
    if (queSize == Capacity()) {
        Console.WriteLine("双向队列已满");
        return;
    }
    // 队首指针向左移动一位
    // 通过取余操作实现 front 越过数组头部后回到尾部
    front = Index(front - 1);
    // 将 num 添加至队首
    nums[front] = num;
    queSize++;
}

/* 队尾入队 */
public void PushLast(int num) {
    if (queSize == Capacity()) {
        Console.WriteLine("双向队列已满");
        return;
    }
    // 计算队尾指针，指向队尾索引 + 1
    int rear = Index(front + queSize);
    // 将 num 添加至队尾
    nums[rear] = num;
    queSize++;
}

/* 队首出队 */
public int PopFirst() {
    int num = PeekFirst();
    // 队首指针向后移动一位
    front = Index(front + 1);
    queSize--;
    return num;
}

/* 队尾出队 */
public int PopLast() {
    int num = PeekLast();
    queSize--;
    return num;
}

/* 访问队首元素 */
public int PeekFirst() {
    if (IsEmpty()) {
        throw new InvalidOperationException();
    }
    return nums[front];
}

/* 访问队尾元素 */
public int PeekLast() {
    if (IsEmpty()) {
        throw new InvalidOperationException();
    }
    // 计算尾元素索引
    int last = Index(front + queSize - 1);
    return nums[last];
}

/* 返回数组用于打印 */
public int[] ToArray() {
    // 仅转换有效长度范围内的列表元素
    int[] res = new int[queSize];
    for (int i = 0, j = front; i < queSize; i++, j++) {
        res[i] = nums[Index(j)];
    }
    return res;
}
}
```

### 双向队列应用

双向队列兼具栈与队列的逻辑，**因此它可以实现这两者的所有应用场景，同时提供更高的自由度**。

我们知道，软件的“撤销”功能通常使用栈来实现：系统将每次更改操作 `push` 到栈中，然后通过 `pop` 实现撤销。然而，考虑到系统资源的限制，软件通常会限制撤销的步数（例如仅允许保存 $50$ 步）。当栈的长度超过 $50$ 时，软件需要在栈底（队首）执行删除操作。**但栈无法实现该功能，此时就需要使用双向队列来替代栈**。请注意，“撤销”的核心逻辑仍然遵循栈的先入后出原则，只是双向队列能够更加灵活地实现一些额外逻辑。

## 5.4 小结

### 重点回顾

- 栈是一种遵循先入后出原则的数据结构，可通过数组或链表来实现。
- 在时间效率方面，栈的数组实现具有较高的平均效率，但在扩容过程中，单次入栈操作的时间复杂度会劣化至 $O(n)$ 。相比之下，栈的链表实现具有更为稳定的效率表现。
- 在空间效率方面，栈的数组实现可能导致一定程度的空间浪费。但需要注意的是，链表节点所占用的内存空间比数组元素更大。
- 队列是一种遵循先入先出原则的数据结构，同样可以通过数组或链表来实现。在时间效率和空间效率的对比上，队列的结论与前述栈的结论相似。
- 双向队列是一种具有更高自由度的队列，它允许在两端进行元素的添加和删除操作。

### Q & A

**Q**：浏览器的前进后退是否是双向链表实现？

浏览器的前进后退功能本质上是“栈”的体现。当用户访问一个新页面时，该页面会被添加到栈顶；当用户点击后退按钮时，该页面会从栈顶弹出。使用双向队列可以方便地实现一些额外操作，这个在“双向队列”章节有提到。

**Q**：在出栈后，是否需要释放出栈节点的内存？

如果后续仍需要使用弹出节点，则不需要释放内存。若之后不需要用到，`Java` 和 `Python` 等语言拥有自动垃圾回收机制，因此不需要手动释放内存；在 `C` 和 `C++` 中需要手动释放内存。

**Q**：双向队列像是两个栈拼接在了一起，它的用途是什么？

双向队列就像是栈和队列的组合或两个栈拼在了一起。它表现的是栈 + 队列的逻辑，因此可以实现栈与队列的所有应用，并且更加灵活。

**Q**：撤销（undo）和反撤销（redo）具体是如何实现的？

使用两个栈，栈 `A` 用于撤销，栈 `B` 用于反撤销。

1. 每当用户执行一个操作，将这个操作压入栈 `A` ，并清空栈 `B` 。
2. 当用户执行“撤销”时，从栈 `A` 中弹出最近的操作，并将其压入栈 `B` 。
3. 当用户执行“反撤销”时，从栈 `B` 中弹出最近的操作，并将其压入栈 `A` 。
