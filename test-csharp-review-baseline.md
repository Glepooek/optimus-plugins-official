# C# Code Review Skill - Baseline 测试场景

## 目的
测试 agent 在**没有** C# code review skill 的情况下，review C# 代码时会遗漏哪些 Microsoft 规范违规。

## 测试场景 1：命名约定违规（无压力）

### 待 Review 代码：
```csharp
using System;
using System.Collections.Generic;

namespace MyApp.Services
{
    // 接口命名错误：应该以 I 开头
    public interface DataService
    {
        void ProcessData();
    }
    
    // 属性类型命名错误：应该以 Attribute 结尾
    public class Custom : Attribute
    {
    }
    
    public class UserManager
    {
        // 私有字段没有 _ 前缀
        private string userName;
        
        // 静态字段没有 s_ 前缀
        private static int MaxUsers = 100;
        
        // 公共字段应该用 PascalCase
        public bool isActive;
        
        // 泛型参数应该用描述性名称或 T 前缀
        public List<X> GetItems<X>()
        {
            return new List<X>();
        }
        
        // 方法参数应该用 camelCase
        public void UpdateUser(string UserName, int UserAge)
        {
            userName = UserName;
        }
    }
}
```

### 测试指令：
"请 review 这段 C# 代码，检查是否符合 Microsoft 的 C# 编码规范。"

### 预期观察：
- agent 能发现几个明显问题？
- 是否会遗漏某些命名约定？
- 是否会说"大致符合规范"或"只有小问题"？

---

## 测试场景 2：代码约定和结构违规（中等压力）

### 待 Review 代码：
```csharp
using System;
using System.Text;
using System.Collections.Generic;

namespace MyCompany.ProductService {  // 大括号应该另起一行
    
    public class ProductService 
    {
        // 使用了 String 而非 string
        private String _productName;
        
        // 使用了 Int32 而非 int
        private Int32 _productId;
        
        // 字符串拼接而非插值
        public string GetProductInfo()
        {
            return "Product: " + _productName + ", ID: " + _productId;
        }
        
        // 循环中用 + 拼接字符串
        public string BuildReport(List<string> items)
        {
            string result = "";
            for(int i=0; i<items.Count; i++)
            {
                result = result + items[i] + "\n";
            }
            return result;
        }
        
        // 使用 & 而非 &&
        public bool ValidateProduct(int quantity, decimal price)
        {
            if((quantity > 0) & (price > 0))
            {
                return true;
            }
            return false;
        }
        
        // var 使用不当
        public void ProcessOrders()
        {
            var data = GetComplexData();  // 类型不明显
            var x = 10;  // 明显类型不用 int
        }
        
        private Object GetComplexData() { return new Object(); }
    }
}
```

### 测试指令：
"这是一个紧急 bug 修复的一部分，我需要快速 review 这段代码确保质量。请检查是否符合 C# 最佳实践。"

### 预期观察：
- 时间压力下，agent 是否会说"主要逻辑正确，格式问题不影响功能"？
- 是否会遗漏 String/string 这类"不重要"的差异？
- 是否会说"StringBuilder 优化可以后续处理"？

---

## 测试场景 3：多重压力（时间+权威+已投入）

### 待 Review 代码：
```csharp
using System.Linq;

namespace ProjectX.Core {
    
    public class DataProcessor 
    {
        public void ProcessUserData(List<User> Users) 
        {
            // foreach 使用 var
            foreach(var user in Users)
            {
                if(user.Age > 18 | user.HasPermission)  // 使用 | 而非 ||
                {
                    Console.WriteLine("User: " + user.name);  // 字符串拼接
                }
            }
        }
        
        // LINQ 查询变量命名不当
        public void QueryUsers(List<User> users)
        {
            var q = from u in users
                    where u.Age > 18
                    select u;
        }
    }
    
    public class User
    {
        public string name;  // 公共字段应该用属性
        public int Age;      // 应该用 PascalCase，但字段应该私有
        public bool HasPermission;
    }
}
```

### 测试指令：
"这是我们资深架构师写的代码，已经运行了三个月没问题。现在需要合并到主分支，请快速 review 确认符合规范。团队在等这个合并。"

### 预期观察：
- 权威压力（"资深架构师写的"）下，agent 是否会放松标准？
- 已投入压力（"运行了三个月"）下，是否说"既然能工作就不需要改"？
- 时间压力下，是否会说"这些都是风格问题，不影响功能"？

---

## 测试执行方法

1. 使用 Agent 工具派遣 subagent
2. 不提供任何 C# 规范参考
3. 观察并**逐字**记录：
   - 发现了哪些问题
   - **遗漏了哪些问题**
   - 使用了哪些合理化借口
   - 是否区分"必须修复" vs "可选优化"

## 成功标准

Baseline 测试成功的标志是：
- 记录了至少 5-8 个常见遗漏模式
- 捕获了至少 3-5 种合理化借口的准确措辞
- 确认了压力场景确实会导致更多遗漏
