---
name: csharp-code-review
description: Use when reviewing C# code for Microsoft coding conventions, naming standards, or preparing code for merge. Triggers on C# file review requests, PR reviews, or code quality checks.
---

# C# Code Review

## Overview

Systematic C# code review against [Microsoft's official C# coding conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions) and [naming guidelines](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/identifier-names).

Core principle: **Comprehensive checklist-driven review prevents missed violations.**

## When to Use

Use when:
- Reviewing C# code for PRs or merges
- Checking code quality before commit
- User asks to "review C# code" or "check C# conventions"
- Ensuring team coding standards compliance

Don't use for:
- Non-C# languages (use appropriate language-specific skill)
- Architecture reviews (focus is conventions, not design)
- Performance profiling (use dotnet-diag skills)

## Review Checklist

Work through each category systematically. Mark each item ✅ checked or ⚠️ violation found.

### 1. Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Interface | `IPascalCase` | `IDataService` |
| Class/Struct/Record | `PascalCase` | `UserManager` |
| Attribute | `PascalCase` + `Attribute` suffix | `CustomAttribute` |
| Enum | Singular (non-flags), Plural (flags) | `Color`, `FileOptions` |
| Public members | `PascalCase` | `ProcessData()`, `UserName` |
| Private instance fields | `_camelCase` | `_userName` |
| Private static fields | `s_camelCase` | `s_maxUsers` |
| Thread-static fields | `t_camelCase` | `t_threadId` |
| Method parameters | `camelCase` | `userName`, `maxCount` |
| Local variables | `camelCase` | `totalCount`, `isValid` |
| Generic type params | `T` or `TPascalCase` | `T`, `TItem`, `TKey` |
| Constants | `PascalCase` | `MaxValue`, `DefaultTimeout` |

**Primary constructor parameters:**
- `record` types: `PascalCase` (become public properties)
- `class`/`struct` types: `camelCase` (standard parameters)

**Check:**
- [ ] No consecutive underscores `__` (reserved for compiler)
- [ ] No Hungarian notation or type prefixes
- [ ] Meaningful descriptive names (not `x`, `temp`, `data` unless in tight loop)

### 2. Type Usage

| Use | Not | Reason |
|-----|-----|--------|
| `string` | `String` | C# keyword > BCL type |
| `int` | `Int32` | C# keyword > BCL type |
| `object` | `Object` | C# keyword > BCL type |
| `bool` | `Boolean` | C# keyword > BCL type |

Apply to: all types with C# keywords (`long`, `short`, `byte`, `decimal`, `float`, `double`, etc.)

### 3. String Handling

| Scenario | Use | Avoid |
|----------|-----|-------|
| Simple concatenation | `$"Hello {name}"` | `"Hello " + name` |
| Loop concatenation | `StringBuilder` | `result += item` |
| Multi-line / escape-heavy | Raw string `"""..."""` | `@"..."` or `\"` |

### 4. Logical Operators

| Use | Not | Reason |
|-----|-----|--------|
| `&&` | `&` | Short-circuit evaluation |
| `\|\|` | `\|` | Short-circuit evaluation |

Exception: Intentional bitwise operations on integers.

### 5. Code Structure

**Namespace:**
- [ ] File-scoped namespace declaration: `namespace X;` (C# 10+)
- [ ] `using` directives outside namespace (avoid relative resolution issues)
- [ ] Allman brace style: braces on new line

**Layout:**
- [ ] One statement per line
- [ ] One declaration per line
- [ ] 4-space indentation (not tabs)
- [ ] Blank line between methods/properties
- [ ] Line breaks before operators if line too long

**Comments:**
- [ ] Single-line `//` for brief notes
- [ ] XML comments `///` for public members
- [ ] No multi-line `/* */` (localization incompatible)
- [ ] Comment on separate line, not end of code line
- [ ] Start with capital, end with period

### 6. var Usage

| Use `var` | Use explicit type |
|-----------|-------------------|
| `var list = new List<int>();` | `object data = GetComplexData();` |
| `var name = "John";` | `int count = Convert.ToInt32(input);` |
| LINQ queries (often anonymous types) | When type isn't obvious from right side |

Rule: Use `var` when type is obvious from right side, explicit type otherwise.

### 7. Collections & LINQ

**Initialization:**
```csharp
string[] vowels = [ "a", "e", "i", "o", "u" ];  // Collection expressions (C# 12+)
```

**LINQ:**
- [ ] Meaningful query variable names (not `q`, `result`)
- [ ] Implicit typing: `var query = from...`
- [ ] `from` clause alignment: subsequent clauses aligned under `from`
- [ ] `where` before `orderby`/`select` (filter early)
- [ ] Multiple `from` preferred over `join` when suitable

### 8. Object Creation

**Prefer:**
```csharp
ExampleClass instance = new();          // Target-typed (C# 9+)
var instance = new ExampleClass();      // When type obvious

// Required properties (C# 11+)
public required string Name { get; init; }
```

**Avoid:**
- Constructor overload explosion (use `required` properties)
- Unnecessary type repetition: `ExampleClass x = new ExampleClass();`

### 9. Delegates & Events

- [ ] Use `Func<>` and `Action<>` over custom delegate types
- [ ] Lambda for event handlers that don't need removal
- [ ] Concise syntax: `Del handler = MethodName;`

### 10. Exception Handling

- [ ] `using` statement over `try-finally` for `IDisposable`
- [ ] Catch specific exceptions (not `Exception`)
- [ ] Only catch what you can handle
- [ ] Provide meaningful error messages

### 11. Async Patterns (if present)

- [ ] `async`/`await` for I/O-bound operations
- [ ] `Task.ConfigureAwait(false)` in library code
- [ ] Avoid blocking async code (`Task.Result`, `Task.Wait()`)

## Common Violations

| Symptom | Issue | Fix |
|---------|-------|-----|
| `public string userName;` | Public field | Use property: `public string UserName { get; set; }` |
| `if(x > 0 & y > 0)` | Bitwise instead of logical | Use `&&` |
| `result = result + item` in loop | Inefficient string concat | Use `StringBuilder` |
| `var data = GetData();` (returns `object`) | Unclear type with `var` | Explicit: `object data = ...` |
| Interface `DataService` | Missing `I` prefix | `IDataService` |
| `private string userName` | Missing `_` prefix | `_userName` |

## Quick Start

For fast review:

1. **Name check**: Interface `I`, Attribute suffix, private `_`, static `s_`, public `PascalCase`, params `camelCase`
2. **Type check**: `string` not `String`, `int` not `Int32`
3. **Operator check**: `&&` not `&`, `||` not `|`
4. **String check**: Interpolation `$""` or `StringBuilder` in loops
5. **Structure check**: File-scoped namespace, `using` outside namespace, Allman braces

## Authority

This skill is based on:
- [Microsoft C# Coding Conventions](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/coding-conventions)
- [Microsoft Identifier Naming Rules](https://learn.microsoft.com/dotnet/csharp/fundamentals/coding-style/identifier-names)
- [.NET Runtime Team Coding Style](https://github.com/dotnet/runtime/blob/main/docs/coding-guidelines/coding-style.md)
