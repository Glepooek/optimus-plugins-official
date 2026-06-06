## Refit：适用于 .NET Core、Xamarin 和 .NET 的自动类型安全 REST 库

Refit 是一个深受 Square 的 [Retrofit](http://square.github.io/retrofit) 库启发的库，它能将你的 REST API 转换为一个可用的接口：

```csharp
public interface IGitHubApi
{
    [Get("/users/{user}")]
    Task<User> GetUser(string user);
}
```

`RestService` 类会生成 `IGitHubApi` 的实现，该实现使用 `HttpClient` 来发起调用：

```csharp
var gitHubApi = RestService.For<IGitHubApi>("https://api.github.com");
var octocat = await gitHubApi.GetUser("octocat");
```

.NET Core 支持通过 HttpClientFactory 进行注册

```csharp
services
    .AddRefitClient<IGitHubApi>()
    .ConfigureHttpClient(c => c.BaseAddress = new Uri("https://api.github.com"));
```

# 目录

- [赞助商](#赞助商)
- [支持平台](#支持平台)
  - [6.x 版本的破坏性变更](#6x-版本的破坏性变更)
  - [11.x 版本的破坏性变更](#11x-版本的破坏性变更)
- [API 属性](#api-属性)
- [查询字符串](#查询字符串)
  - [动态查询字符串参数](#动态查询字符串参数)
  - [集合作为查询字符串参数](#集合作为查询字符串参数)
  - [取消查询字符串参数转义](#取消查询字符串参数转义)
  - [自定义查询字符串参数格式化](#自定义查询字符串参数格式化)
- [请求体内容](#请求体内容)
  - [缓冲与 Content-Length 头](#缓冲与-content-length-头)
  - [JSON 内容](#json-内容)
  - [XML 内容](#xml-内容)
  - [表单提交](#表单提交)
- [设置请求头](#设置请求头)
  - [静态请求头](#静态请求头)
  - [动态请求头](#动态请求头)
  - [Bearer 认证](#bearer-认证)
  - [使用 DelegatingHandler 减少请求头样板代码（Authorization 头实战示例）](#使用-delegatinghandler-减少请求头样板代码authorization-头实战示例)
  - [重定义请求头](#重定义请求头)
  - [移除请求头](#移除请求头)
- [向 DelegatingHandler 传递状态](#向-delegatinghandler-传递状态)
  - [对 Polly 和 Polly.Context 的支持](#对-polly-和-pollycontext-的支持)
  - [目标接口类型](#目标接口类型)
  - [Refit 客户端接口上被调用方法的 MethodInfo](#refit-客户端接口上被调用方法的-methodinfo)
- [多部分上传](#多部分上传)
- [获取响应](#获取响应)
- [使用泛型接口](#使用泛型接口)
- [接口继承](#接口继承)
  - [请求头继承](#请求头继承)
- [默认接口方法](#默认接口方法)
- [使用 HttpClientFactory](#使用-httpclientfactory)
- [提供自定义 HttpClient](#提供自定义-httpclient)
- [处理异常](#处理异常)
  - [返回 Task&lt;IApiResponse&gt;、Task&lt;IApiResponse&lt;T&gt;&gt; 或 Task&lt;ApiResponse&lt;T&gt;&gt; 时](#返回-taskiapiresponsetaskiapiresponset-或-taskapiresponset-时)
  - [返回 Task&lt;T&gt; 时](#返回-taskt-时)
  - [提供自定义 ExceptionFactory](#提供自定义-exceptionfactory)
  - [使用 Serilog 解构 ApiException](#使用-serilog-解构-apiexception)

### 支持平台

Refit 目前支持以下平台以及任何 .NET Standard 2.0 目标：

- WinUI
- Desktop .NET Framework 4.6.2+
- .NET 8 / 9 / 10
- Blazor
- Uno Platform

### SDK 要求

### 8.0.x 版本更新

修复了一些已知问题，这导致了一些破坏性变更。
详见 [发布说明](https://github.com/reactiveui/refit/releases)。

### V6.x.x

Refit 6 需要 Visual Studio 16.8 或更高版本，或 .NET SDK 5.0.100 或更高版本。它可以面向任何 .NET Standard 2.0 平台。

Refit 6 不支持旧的 `packages.config` 格式的 NuGet 引用（因为它们不支持分析器/源代码生成器）。你必须[迁移到 PackageReference](https://devblogs.microsoft.com/nuget/migrate-packages-config-to-package-reference/) 才能使用 Refit v6 及更高版本。

#### 6.x 版本的破坏性变更

Refit 6 将 [System.Text.Json](https://docs.microsoft.com/en-us/dotnet/standard/serialization/system-text-json-overview) 设为默认的 JSON 序列化器。如果你想继续使用 `Newtonsoft.Json`，请添加 `Refit.Newtonsoft.Json` NuGet 包，并在 `RefitSettings` 实例上将 `ContentSerializer` 设置为 `NewtonsoftJsonContentSerializer`。`System.Text.Json` 更快且内存占用更少，但并非所有功能都受支持。[迁移指南](https://docs.microsoft.com/en-us/dotnet/standard/serialization/system-text-json-migrate-from-newtonsoft-how-to?pivots=dotnet-5-0) 包含更多详细信息。

`IContentSerializer` 已重命名为 `IHttpContentSerializer` 以更好地反映其用途。此外，它的两个方法也被重命名：`SerializeAsync<T>` -> `ToHttpContent<T>` 和 `DeserializeAsync<T>` -> `FromHttpContentAsync<T>`。任何现有的实现都需要更新，但改动应该很小。

##### 6.3 版本更新

Refit 6.3 将 XML 序列化功能（通过 `XmlContentSerializer`）拆分为一个单独的包 `Refit.Xml`。这是为了减少在 Web Assembly (WASM) 应用程序中使用 Refit 时的依赖大小。如果你需要 XML，请添加对 `Refit.Xml` 的引用。

### V11.x.x

#### 11.x 版本的破坏性变更

Refit 10 引入了 `ApiRequestException` 来表示在收到服务器响应之前失败的请求。当在请求执行期间发生 `HttpRequestException` 和 `TaskCanceledException` 时，此异常现在将包装这些先前的异常。

- 如果你之前没有使用 `IApiResponse` 包装响应，而是直接捕获这些异常，你需要更新代码以捕获 `ApiRequestException`。
- 如果你之前使用 `IApiResponse` 包装响应，这些异常将不再被抛出，而是被捕获到 `IApiResponse.Error` 属性中。你可以使用新的 `IApiResponse.HasRequestError(out var apiRequestException)` 方法来安全地检查和获取 `ApiRequestException` 实例。

`IApiResponse.Error` 属性的类型也已更改为 `ApiExceptionBase`，它是 `ApiException` 和 `ApiRequestException` 的新基类。如果你的代码访问了 `ApiException` 特有的成员（即与服务器响应相关的任何内容），你可以使用新的 `IApiResponse.HasResponseError(out var apiException)` 方法来安全地检查和获取 `ApiException` 实例。

`IApiResponse` 的所有与响应相关的属性现在都是可空的。新的 `IApiResponse.IsReceived` 属性可用于检查是否收到了服务器响应，并将这些属性标记为非空。原有的 `IApiResponse.IsSuccessful` 和 `IApiResponse.IsSuccessStatusCode` 属性仍然可用于检查响应是否已收到且成功。

### API 属性

每个方法都必须有一个 HTTP 属性，提供请求方法和相对 URL。有六个内置注解：Get、Post、Put、Delete、Patch 和 Head。资源的相对 URL 在注解中指定。

```csharp
[Get("/users/list")]
```

你也可以在 URL 中指定查询参数：

```csharp
[Get("/users/list?sort=desc")]
```

请求 URL 可以使用替换块和方法上的参数进行动态更新。替换块是由 { 和 } 包围的字母数字字符串。

如果你的参数名称与 URL 路径中的名称不匹配，请使用 `AliasAs` 属性。

```csharp
[Get("/group/{id}/users")]
Task<List<User>> GroupList([AliasAs("id")] int groupId);
```

请求 URL 也可以将替换块绑定到自定义对象

```csharp
[Get("/group/{request.groupId}/users/{request.userId}")]
Task<List<User>> GroupList(UserGroupRequest request);

class UserGroupRequest{
    int groupId { get;set; }
    int userId { get;set; }
}

```

未指定为 URL 替换的参数将自动用作查询参数。这与 Retrofit 不同，在 Retrofit 中所有参数都必须显式指定。

参数名称和 URL 参数之间的比较是*不*区分大小写的，因此如果你在路径 `/group/{groupid}/show` 中将参数命名为 `groupId`，它将正常工作。

```csharp
[Get("/group/{groupid}/users")]
Task<List<User>> GroupList(int groupId, [AliasAs("sort")] string sortOrder);

GroupList(4, "desc");
>>> "/group/4/users?sort=desc"
```

往返路由参数语法：使用双星号（\*\*）通配符参数语法时，正斜杠不会被编码。

在链接生成期间，路由系统会对双星号（\*\*）通配符参数（例如 {\*\*myparametername}）中捕获的值进行编码，但正斜杠除外。

往返路由参数的类型必须是 string。

```csharp
[Get("/search/{**page}")]
Task<List<Page>> Search(string page);

Search("admin/products");
>>> "/search/admin/products"
```

### 查询字符串

#### 动态查询字符串参数

如果你将 `object` 指定为查询参数，所有非 null 的公共属性都将用作查询参数。这以前仅适用于 GET 请求，但现在已扩展到所有 HTTP 请求方法，部分原因是 Twitter 的混合 API 要求在非 GET 请求中使用查询字符串参数。使用 `Query` 属性可以将行为更改为"展平"查询参数对象。如果使用此属性，你可以指定用于"展平"对象的分隔符和前缀的值。

```csharp
public class MyQueryParams
{
    [AliasAs("order")]
    public string SortOrder { get; set; }

    public int Limit { get; set; }

    public KindOptions Kind { get; set; }
}

public enum KindOptions
{
    Foo,

    [EnumMember(Value = "bar")]
    Bar
}


[Get("/group/{id}/users")]
Task<List<User>> GroupList([AliasAs("id")] int groupId, MyQueryParams params);

[Get("/group/{id}/users")]
Task<List<User>> GroupListWithAttribute([AliasAs("id")] int groupId, [Query(".","search")] MyQueryParams params);


params.SortOrder = "desc";
params.Limit = 10;
params.Kind = KindOptions.Bar;

GroupList(4, params)
>>> "/group/4/users?order=desc&Limit=10&Kind=bar"

GroupListWithAttribute(4, params)
>>> "/group/4/users?search.order=desc&search.Limit=10&search.Kind=bar"
```

使用 Dictionary 时也有类似的行为，但没有 `AliasAs` 属性的优势，当然也没有智能感知和/或类型安全。

你也可以使用 [Query] 指定查询字符串参数，并在非 GET 请求中展平它们，类似于：

```csharp
[Post("/statuses/update.json")]
Task<Tweet> PostTweet([Query]TweetParams params);
```

其中 `TweetParams` 是一个 POCO，属性也支持 `[AliasAs]` 属性。

如果你需要在查询 DTO 上保留仅内部使用的属性，请使用标准忽略属性之一标记它们，Refit 在构建查询字符串时将跳过它们：

- `[IgnoreDataMember]`
- `[System.Text.Json.Serialization.JsonIgnore]`
- `[Newtonsoft.Json.JsonIgnore]`

#### 集合作为查询字符串参数

使用 `Query` 属性指定集合在查询字符串中的格式化方式

```csharp
[Get("/users/list")]
Task Search([Query(CollectionFormat.Multi)]int[] ages);

Search(new [] {10, 20, 30})
>>> "/users/list?ages=10&ages=20&ages=30"

[Get("/users/list")]
Task Search([Query(CollectionFormat.Csv)]int[] ages);

Search(new [] {10, 20, 30})
>>> "/users/list?ages=10%2C20%2C30"
```

你也可以在 `RefitSettings` 中指定集合格式，除非在 `Query` 属性中明确定义，否则将默认使用该格式。

```csharp
var gitHubApi = RestService.For<IGitHubApi>("https://api.github.com",
    new RefitSettings {
        CollectionFormat = CollectionFormat.Multi
    });
```

#### 取消查询字符串参数转义

使用 `QueryUriFormat` 属性指定查询参数是否应进行 URL 转义

```csharp
[Get("/query")]
[QueryUriFormat(UriFormat.Unescaped)]
Task Query(string q);

Query("Select+Id,Name+From+Account")
>>> "/query?q=Select+Id,Name+From+Account"
```

#### 自定义查询字符串参数格式化

**格式化键**

要自定义查询键的格式，你有两个主要选项：

1. **使用 `AliasAs` 属性**：

   你可以使用 `AliasAs` 属性为属性指定自定义键名。此属性始终优先于你指定的任何键格式化器。

   ```csharp
   public class MyQueryParams
   {
       [AliasAs("order")]
       public string SortOrder { get; set; }

       public int Limit { get; set; }
   }

   [Get("/group/{id}/users")]
   Task<List<User>> GroupList([AliasAs("id")] int groupId, [Query] MyQueryParams params);

   params.SortOrder = "desc";
   params.Limit = 10;

   GroupList(1, params);
   ```

   这将生成以下请求：

   ```
   /group/1/users?order=desc&Limit=10
   ```

2. **使用 `RefitSettings.UrlParameterKeyFormatter` 属性**：

   默认情况下，Refit 使用属性名称作为查询键，不进行任何额外格式化。如果你想对所有查询键应用自定义格式，可以使用 `UrlParameterKeyFormatter` 属性。请记住，如果属性有 `AliasAs` 属性，无论格式化器如何，都将使用该属性。

   以下示例使用内置的 `CamelCaseUrlParameterKeyFormatter`：

   ```csharp
   public class MyQueryParams
   {
       public string SortOrder { get; set; }

       [AliasAs("queryLimit")]
       public int Limit { get; set; }
   }

   [Get("/group/users")]
   Task<List<User>> GroupList([Query] MyQueryParams params);

   params.SortOrder = "desc";
   params.Limit = 10;
   ```

   请求将如下所示：

   ```
   /group/users?sortOrder=desc&queryLimit=10
   ```

**注意**：`AliasAs` 属性始终具有最高优先级。如果同时存在属性和自定义键格式化器，将使用 `AliasAs` 属性的值。

#### 使用 `UrlParameterFormatter` 格式化 URL 参数值

在 Refit 中，`RefitSettings` 中的 `UrlParameterFormatter` 属性允许你自定义参数值在 URL 中的格式化方式。当你需要以特定方式格式化日期、数字或其他类型以符合 API 要求时，这尤其有用。

**使用 `UrlParameterFormatter`**：

将实现 `IUrlParameterFormatter` 接口的自定义格式化器赋值给 `UrlParameterFormatter` 属性。

```csharp
public class CustomDateUrlParameterFormatter : IUrlParameterFormatter
{
    public string? Format(object? value, ICustomAttributeProvider attributeProvider, Type type)
    {
        if (value is DateTime dt)
        {
            return dt.ToString("yyyyMMdd");
        }

        return value?.ToString();
    }
}

var settings = new RefitSettings
{
    UrlParameterFormatter = new CustomDateUrlParameterFormatter()
};
```

在此示例中，为日期值创建了自定义格式化器。每当遇到 `DateTime` 参数时，它会将日期格式化为 `yyyyMMdd`。

**格式化字典键**：

处理字典时，需要注意键被视为值。如果你需要对字典键进行自定义格式化，也应使用 `UrlParameterFormatter`。

例如，如果你有一个字典参数并希望以特定方式格式化其键，可以在自定义格式化器中处理：

```csharp
public class CustomDictionaryKeyFormatter : IUrlParameterFormatter
{
    public string? Format(object? value, ICustomAttributeProvider attributeProvider, Type type)
    {
        // 处理字典键
        if (attributeProvider is PropertyInfo prop && prop.PropertyType.IsGenericType && prop.PropertyType.GetGenericTypeDefinition() == typeof(Dictionary<,>))
        {
            // 字典键的自定义格式化逻辑
            return value?.ToString().ToUpperInvariant();
        }

        return value?.ToString();
    }
}

var settings = new RefitSettings
{
    UrlParameterFormatter = new CustomDictionaryKeyFormatter()
};
```

在上面的示例中，字典键将被转换为大写。

### 请求体内容

方法中的一个参数可以使用 Body 属性作为请求体：

```csharp
[Post("/users/new")]
Task CreateUser([Body] User user);
```

根据参数类型，有四种提供请求体数据的方式：

- 如果类型是 `Stream`，内容将通过 `StreamContent` 进行流式传输
- 如果类型是 `string`，字符串将直接用作内容，除非设置了 `[Body(BodySerializationMethod.Json)]`，此时将作为 `StringContent` 发送
- 如果参数具有 `[Body(BodySerializationMethod.UrlEncoded)]` 属性，内容将进行 URL 编码（参见下面的[表单提交](#表单提交)）
- 对于所有其他类型，对象将使用 RefitSettings 中指定的内容序列化器进行序列化（默认为 JSON）。

#### 缓冲与 `Content-Length` 头

默认情况下，Refit 流式传输请求体内容而不进行缓冲。这意味着你可以从磁盘流式传输文件，而不会产生将整个文件加载到内存中的开销。这样做缺点是*不会*在请求上设置 `Content-Length` 头。如果你的 API 需要发送 `Content-Length` 头，可以通过将 `[Body]` 属性的 `buffered` 参数设置为 `true` 来禁用此流式传输行为：

```csharp
Task CreateUser([Body(buffered: true)] User user);
```

#### JSON 内容

JSON 请求和响应使用 `IHttpContentSerializer` 接口的实例进行序列化/反序列化。Refit 开箱即用地提供了两个实现：`SystemTextJsonContentSerializer`（默认的 JSON 序列化器）和 `NewtonsoftJsonContentSerializer`。前者使用 `System.Text.Json` API，专注于高性能和低内存使用，而后者使用知名的 `Newtonsoft.Json` 库，更加灵活和可定制。你可以[在此链接](https://docs.microsoft.com/dotnet/standard/serialization/system-text-json-migrate-from-newtonsoft-how-to)中阅读有关两个序列化器及其主要区别的更多信息。

例如，以下是如何使用基于 `Newtonsoft.Json` 的序列化器创建新的 `RefitSettings` 实例（你还需要添加对 `Refit.Newtonsoft.Json` 的 `PackageReference`）：

```csharp
var settings = new RefitSettings(new NewtonsoftJsonContentSerializer());
```

如果你使用 `Newtonsoft.Json` API，可以通过设置 `Newtonsoft.Json.JsonConvert.DefaultSettings` 属性来自定义其行为：

```csharp
JsonConvert.DefaultSettings =
    () => new JsonSerializerSettings() {
        ContractResolver = new CamelCasePropertyNamesContractResolver(),
        Converters = {new StringEnumConverter()}
    };

// 序列化为: {"day":"Saturday"}
await PostSomeStuff(new { Day = DayOfWeek.Saturday });
```

由于这些是全局设置，它们会影响整个应用程序。隔离特定 API 调用的设置可能是有益的。在创建 Refit 生成的实时接口时，你可以选择性地传递一个 `RefitSettings`，允许你指定所需的序列化器设置。这使你可以为不同的 API 设置不同的序列化器设置：

```csharp
var gitHubApi = RestService.For<IGitHubApi>("https://api.github.com",
    new RefitSettings {
        ContentSerializer = new NewtonsoftJsonContentSerializer(
            new JsonSerializerSettings {
                ContractResolver = new SnakeCasePropertyNamesContractResolver()
        }
    )});

var otherApi = RestService.For<IOtherApi>("https://api.example.com",
    new RefitSettings {
        ContentSerializer = new NewtonsoftJsonContentSerializer(
            new JsonSerializerSettings {
                ContractResolver = new CamelCasePropertyNamesContractResolver()
        }
    )});
```

属性的序列化/反序列化可以使用 Json.NET 的 JsonProperty 属性进行自定义：

```csharp
public class Foo
{
    // 在表单提交中类似于 [AliasAs("b")]（见下文）
    [JsonProperty(PropertyName="b")]
    public string Bar { get; set; }
}
```

##### JSON 源代码生成器

要应用 .NET 6 中新增的 [JSON 源代码生成器](https://devblogs.microsoft.com/dotnet/try-the-new-system-text-json-source-generator/) 的优势，你可以将 `SystemTextJsonContentSerializer` 与自定义的 `RefitSettings` 和 `JsonSerializerOptions` 实例一起使用：

```csharp
var gitHubApi = RestService.For<IGitHubApi>("https://api.github.com",
    new RefitSettings {
        ContentSerializer = new SystemTextJsonContentSerializer(MyJsonSerializerContext.Default.Options)
    });
```

当使用 `System.Text.Json` 多态性功能（如 `[JsonDerivedType]` / `[JsonPolymorphic]`）时，Refit 使用**声明的 Refit 方法参数类型**而非装箱的运行时 `object` 来序列化请求体。这确保了在基础契约上配置的类型鉴别器在传出请求负载中得以保留。

#### XML 内容

XML 请求和响应使用 _System.Xml.Serialization.XmlSerializer_ 进行序列化/反序列化。默认情况下，Refit 使用 JSON 内容序列化，要使用 XML 内容，请将 ContentSerializer 配置为使用 `XmlContentSerializer`：

```csharp
var gitHubApi = RestService.For<IXmlApi>("https://www.w3.org/XML",
    new RefitSettings {
        ContentSerializer = new XmlContentSerializer()
    });
```

属性的序列化/反序列化可以使用 _System.Xml.Serialization_ 命名空间中的属性进行自定义：

```csharp
    public class Foo
    {
        [XmlElement(Namespace = "https://www.w3.org/XML")]
        public string Bar { get; set; }
    }
```

_System.Xml.Serialization.XmlSerializer_ 提供了许多序列化选项，可以通过向 `XmlContentSerializer` 构造函数提供 `XmlContentSerializerSettings` 来设置这些选项：

```csharp
var gitHubApi = RestService.For<IXmlApi>("https://www.w3.org/XML",
    new RefitSettings {
        ContentSerializer = new XmlContentSerializer(
            new XmlContentSerializerSettings
            {
                XmlReaderWriterSettings = new XmlReaderWriterSettings()
                {
                    ReaderSettings = new XmlReaderSettings
                    {
                        IgnoreWhitespace = true
                    }
                }
            }
        )
    });
```

#### <a name="form-posts"></a>表单提交

对于接受表单提交的 API（即序列化为 `application/x-www-form-urlencoded`），请使用 `BodySerializationMethod.UrlEncoded` 初始化 Body 属性。

参数可以是 `IDictionary`：

```csharp
public interface IMeasurementProtocolApi
{
    [Post("/collect")]
    Task Collect([Body(BodySerializationMethod.UrlEncoded)] Dictionary<string, object> data);
}

var data = new Dictionary<string, object> {
    {"v", 1},
    {"tid", "UA-1234-5"},
    {"cid", new Guid("d1e9ea6b-2e8b-4699-93e0-0bcbd26c206c")},
    {"t", "event"},
};

// 序列化为: v=1&tid=UA-1234-5&cid=d1e9ea6b-2e8b-4699-93e0-0bcbd26c206c&t=event
await api.Collect(data);
```

或者你可以只传递任何对象，所有*公共的、可读的*属性将被序列化为请求中的表单字段。这种方法允许你使用 `[AliasAs("whatever")]` 为属性名设置别名，如果 API 有晦涩的字段名，这会很有帮助：

```csharp
public interface IMeasurementProtocolApi
{
    [Post("/collect")]
    Task Collect([Body(BodySerializationMethod.UrlEncoded)] Measurement measurement);
}

public class Measurement
{
    // 属性可以是只读的，不需要 [AliasAs]
    public int v { get { return 1; } }

    [AliasAs("tid")]
    public string WebPropertyId { get; set; }

    [AliasAs("cid")]
    public Guid ClientId { get; set; }

    [AliasAs("t")]
    public string Type { get; set; }

    public object IgnoreMe { private get; set; }
}

var measurement = new Measurement {
    WebPropertyId = "UA-1234-5",
    ClientId = new Guid("d1e9ea6b-2e8b-4699-93e0-0bcbd26c206c"),
    Type = "event"
};

// 序列化为: v=1&tid=UA-1234-5&cid=d1e9ea6b-2e8b-4699-93e0-0bcbd26c206c&t=event
await api.Collect(measurement);
```

如果你的类型具有设置属性别名的 `[JsonProperty(PropertyName)]` 属性，Refit 也会使用它们（当同时存在 `[AliasAs]` 时，`[AliasAs]` 优先）。这意味着以下类型将序列化为 `one=value1&two=value2`：

```csharp

public class SomeObject
{
    [JsonProperty(PropertyName = "one")]
    public string FirstProperty { get; set; }

    [JsonProperty(PropertyName = "notTwo")]
    [AliasAs("two")]
    public string SecondProperty { get; set; }
}

```

**注意：** 此处 `AliasAs` 的使用适用于查询字符串参数和表单体提交，但不适用于响应对象；对于响应对象上的字段别名，你仍然需要使用 `[JsonProperty("full-property-name")]`。

### 设置请求头

#### 静态请求头

你可以通过在方法上应用 `Headers` 属性来为请求设置一个或多个静态请求头：

```csharp
[Headers("User-Agent: Awesome Octocat App")]
[Get("/users/{user}")]
Task<User> GetUser(string user);
```

也可以通过在接口上应用 `Headers` 属性来为*API 中的每个请求*添加静态请求头：

```csharp
[Headers("User-Agent: Awesome Octocat App")]
public interface IGitHubApi
{
    [Get("/users/{user}")]
    Task<User> GetUser(string user);

    [Post("/users/new")]
    Task CreateUser([Body] User user);
}
```

#### 动态请求头

如果请求头的内容需要在运行时设置，可以通过在参数上应用 `Header` 属性来为请求添加具有动态值的请求头：

```csharp
[Get("/users/{user}")]
Task<User> GetUser(string user, [Header("Authorization")] string authorization);

// 将向请求添加头 "Authorization: token OAUTH-TOKEN"
var user = await GetUser("octocat", "token OAUTH-TOKEN");
```

添加 `Authorization` 头是一个非常常见的用例，你可以通过在参数上应用 `Authorize` 属性并可选地指定方案来向请求添加访问令牌：

```csharp
[Get("/users/{user}")]
Task<User> GetUser(string user, [Authorize("Bearer")] string token);

// 将向请求添加头 "Authorization: Bearer OAUTH-TOKEN"
var user = await GetUser("octocat", "OAUTH-TOKEN");

// 注意：如果未提供方案，默认为 Bearer
```

如果需要在运行时设置多个请求头，可以添加一个 `IDictionary<string, string>` 并在参数上应用 `HeaderCollection` 属性，它将把请求头注入到请求中：

[//]: # '{% raw %}'

```csharp

[Get("/users/{user}")]
Task<User> GetUser(string user, [HeaderCollection] IDictionary<string, string> headers);

var headers = new Dictionary<string, string> {{"Authorization","Bearer tokenGoesHere"}, {"X-Tenant-Id","123"}};
var user = await GetUser("octocat", headers);
```

[//]: # '{% endraw %}'

#### Bearer 认证

大多数 API 需要某种形式的认证。最常见的是 OAuth Bearer 认证。每个请求都会添加一个格式为 `Authorization: Bearer <token>` 的头。Refit 使你可以轻松插入获取令牌的逻辑，无论你的应用程序需要何种方式，这样你就不必在每个方法中传递令牌。

1. 在需要令牌的接口或方法上添加 `[Headers("Authorization: Bearer")]`。
2. 在 `RefitSettings` 实例中设置 `AuthorizationHeaderValueGetter`。Refit 每次需要获取令牌时都会调用你的委托，因此你的机制最好在令牌生命周期内缓存令牌值一段时间。

无论你使用 `RestService.For<T>("https://...")` 创建客户端还是通过 `RestService.For<T>(httpClient, settings)` 提供自己的 `HttpClient`，`AuthorizationHeaderValueGetter` 都可以工作。如果你的 API 方法接受 `CancellationToken`，该令牌会传播到 getter 委托。

#### 使用 DelegatingHandler 减少请求头样板代码（Authorization 头实战示例）

虽然我们提供了在 Refit 中直接在运行时添加动态请求头的条款，但大多数用例可能会受益于注册自定义 `DelegatingHandler`，以便将请求头作为 `HttpClient` 中间件管道的一部分注入，从而无需添加大量 `[Header]` 或 `[HeaderCollection]` 属性。

在上面的示例中，我们利用 `[HeaderCollection]` 参数注入 `Authorization` 和 `X-Tenant-Id` 头。如果你正在集成使用 OAuth2 的第三方，这是一个相当常见的情景。虽然对于偶尔的端点来说没问题，但如果我们必须在接口中的每个方法上添加该样板代码，那将非常繁琐。

在此示例中，我们将假设我们的应用程序是一个多租户应用程序，能够通过某个接口 `ITenantProvider` 获取租户信息，并且有一个数据存储 `IAuthTokenStore` 可用于获取要附加到出站请求的认证令牌。

```csharp

 // 用于向出站请求添加 Auth 头的自定义委托处理程序
 class AuthHeaderHandler : DelegatingHandler
 {
     private readonly ITenantProvider tenantProvider;
     private readonly IAuthTokenStore authTokenStore;

    public AuthHeaderHandler(ITenantProvider tenantProvider, IAuthTokenStore authTokenStore)
    {
         this.tenantProvider = tenantProvider ?? throw new ArgumentNullException(nameof(tenantProvider));
         this.authTokenStore = authTokenStore ?? throw new ArgumentNullException(nameof(authTokenStore));
         // 使用 DI 时 InnerHandler 必须保留为 null，但使用 RestService.For<IMyApi> 时必须赋值
         // InnerHandler = new HttpClientHandler();
    }

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        var token = await authTokenStore.GetToken();

        // 如果令牌过期等，可能在此处刷新令牌

        request.Headers.Authorization = new AuthenticationHeaderValue("Bearer", token);
        request.Headers.Add("X-Tenant-Id", tenantProvider.GetTenantId());

        return await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }
}

//Startup.cs
public void ConfigureServices(IServiceCollection services)
{
    services.AddTransient<ITenantProvider, TenantProvider>();
    services.AddTransient<IAuthTokenStore, AuthTokenStore>();
    services.AddTransient<AuthHeaderHandler>();

    // 这将添加我们的 refit api 实现和一个配置为向所有请求添加 auth 头的 HttpClient

    // 注意：AddRefitClient<T> 需要引用 Refit.HttpClientFactory
    // 注意：委托处理程序的顺序很重要，它们按添加顺序运行！

    services.AddRefitClient<ISomeThirdPartyApi>()
        .ConfigureHttpClient(c => c.BaseAddress = new Uri("https://api.example.com"))
        .AddHttpMessageHandler<AuthHeaderHandler>();
        // 你可以在此处添加 Polly 来处理 HTTP 429 / HTTP 503 等
}

// 你的应用程序代码
public class SomeImportantBusinessLogic
{
    private ISomeThirdPartyApi thirdPartyApi;

    public SomeImportantBusinessLogic(ISomeThirdPartyApi thirdPartyApi)
    {
        this.thirdPartyApi = thirdPartyApi;
    }

    public async Task DoStuffWithUser(string username)
    {
        var user = await thirdPartyApi.GetUser(username);
        // 做你的事情
    }
}
```

如果你不使用依赖注入，可以通过以下方式实现相同的效果：

```csharp
var api = RestService.For<ISomeThirdPartyApi>(new HttpClient(new AuthHeaderHandler(tenantProvider, authTokenStore))
    {
        BaseAddress = new Uri("https://api.example.com")
    }
);

var user = await thirdPartyApi.GetUser(username);
// 做你的事情
```

#### 重定义请求头

与 Retrofit 不同（在 Retrofit 中请求头不会相互覆盖，无论同一请求头定义多少次都会添加到请求中），Refit 采取了与 ASP.NET MVC 中操作过滤器类似的方法 —— **重定义请求头将替换它**，优先级顺序如下：

- 接口上的 `Headers` 属性 _（最低优先级）_
- 方法上的 `Headers` 属性
- 方法参数上的 `Header` 属性或 `HeaderCollection` 属性 _（最高优先级）_

```csharp
[Headers("X-Emoji: :rocket:")]
public interface IGitHubApi
{
    [Get("/users/list")]
    Task<List> GetUsers();

    [Get("/users/{user}")]
    [Headers("X-Emoji: :smile_cat:")]
    Task<User> GetUser(string user);

    [Post("/users/new")]
    [Headers("X-Emoji: :metal:")]
    Task CreateUser([Body] User user, [Header("X-Emoji")] string emoji);
}

// X-Emoji: :rocket:
var users = await GetUsers();

// X-Emoji: :smile_cat:
var user = await GetUser("octocat");

// X-Emoji: :trollface:
await CreateUser(user, ":trollface:");
```

**注意：** 此重定义行为仅适用于*同名*的请求头。不同名称的请求头不会被替换。以下代码将导致所有请求头都被包含：

```csharp
[Headers("Header-A: 1")]
public interface ISomeApi
{
    [Headers("Header-B: 2")]
    [Post("/post")]
    Task PostTheThing([Header("Header-C")] int c);
}

// Header-A: 1
// Header-B: 2
// Header-C: 3
var user = await api.PostTheThing(3);
```

#### 移除请求头

可以通过重定义没有值的静态请求头（即没有 `: <value>`）或为动态请求头传递 `null` 来移除在接口或方法上定义的请求头。_空字符串将被包含为空请求头。_

```csharp
[Headers("X-Emoji: :rocket:")]
public interface IGitHubApi
{
    [Get("/users/list")]
    [Headers("X-Emoji")] // 移除 X-Emoji 头
    Task<List> GetUsers();

    [Get("/users/{user}")]
    [Headers("X-Emoji:")] // 将 X-Emoji 头重定义为空
    Task<User> GetUser(string user);

    [Post("/users/new")]
    Task CreateUser([Body] User user, [Header("X-Emoji")] string emoji);
}

// 没有 X-Emoji 头
var users = await GetUsers();

// X-Emoji:
var user = await GetUser("octocat");

// 没有 X-Emoji 头
await CreateUser(user, null);

// X-Emoji:
await CreateUser(user, "");
```

### 向 DelegatingHandler 传递状态

如果你需要将运行时状态传递给 `DelegatingHandler`，可以通过在参数上应用 `Property` 属性来向底层 `HttpRequestMessage.Properties` 添加具有动态值的属性：

```csharp
public interface IGitHubApi
{
    [Post("/users/new")]
    Task CreateUser([Body] User user, [Property("SomeKey")] string someValue);

    [Post("/users/new")]
    Task CreateUser([Body] User user, [Property] string someOtherKey);
}
```

属性构造函数可选地接受一个字符串，该字符串成为 `HttpRequestMessage.Properties` 字典中的键。如果没有明确定义键，则参数名称成为键。如果一个键被定义多次，`HttpRequestMessage.Properties` 中的值将被覆盖。参数本身可以是任何 `object`。可以在 `DelegatingHandler` 中访问属性，如下所示：

> ⚠️ **`IHttpClientFactory` 用户重要提示：** `DelegatingHandler` 实例是池化的，可能比单个请求范围存活更长。避免从可能在处理程序生命周期内被作用域化/缓存的服务中读取每请求状态（例如存储在处理程序上的租户/客户解析器）。对于像 `CustomerId` 这样的每请求值，请通过 `[Property]` 传递值，以便每个请求携带自己的状态。

```csharp
class RequestPropertyHandler : DelegatingHandler
{
    public RequestPropertyHandler(HttpMessageHandler innerHandler = null) : base(innerHandler ?? new HttpClientHandler()) {}

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        // 检查请求是否具有该属性
        if(request.Properties.ContainsKey("SomeKey"))
        {
            var someProperty = request.Properties["SomeKey"];
            // 做一些事情
        }

        if(request.Properties.ContainsKey("someOtherKey"))
        {
            var someOtherProperty = request.Properties["someOtherKey"];
            // 做一些事情
        }

        return await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }
}
```

注意：在 .NET 5 中 `HttpRequestMessage.Properties` 已被标记为 `Obsolete`，Refit 将改为把值填充到新的 `HttpRequestMessage.Options` 中。

#### 对 Polly 和 Polly.Context 的支持

因为 Refit 支持 `HttpClientFactory`，所以可以在你的 HttpClient 上配置 Polly 策略。如果你的策略使用 `Polly.Context`，可以通过添加 `[Property("PolicyExecutionContext")] Polly.Context context` 来通过 Refit 传递，因为 `Polly.Context` 在底层只是存储在 `HttpRequestMessage.Properties` 中，键为 `PolicyExecutionContext`，类型为 `Polly.Context`。仅当你的用例需要 `Polly.Context` 以运行时才知道的动态内容初始化时，才建议以这种方式传递 `Polly.Context`。如果你的 `Polly.Context` 每次只需要相同的内容（例如你想在策略内部使用的 `ILogger`），更简洁的方法是通过 `DelegatingHandler` 注入 `Polly.Context`，如 [#801](https://github.com/reactiveui/refit/issues/801#issuecomment-1137318526) 中所述。

#### 目标接口类型和方法信息

有时你可能想知道 Refit 实例的目标接口类型是什么。一个例子是你有一个实现了公共基础接口的派生接口，如下所示：

```csharp
public interface IGetAPI<TEntity>
{
    [Get("/{key}")]
    Task<TEntity> Get(long key);
}

public interface IUsersAPI : IGetAPI<User>
{
}

public interface IOrdersAPI : IGetAPI<Order>
{
}
```

你可以在处理程序中访问接口的具体类型，例如用于更改请求的 URL：

[//]: # '{% raw %}'

```csharp
class RequestPropertyHandler : DelegatingHandler
{
    public RequestPropertyHandler(HttpMessageHandler innerHandler = null) : base(innerHandler ?? new HttpClientHandler()) {}

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        // 获取目标接口的类型
        Type interfaceType = (Type)request.Properties[HttpMessageRequestOptions.InterfaceType];

        var builder = new UriBuilder(request.RequestUri);
        // 基于接口或其上的属性以某种方式更改路径
        builder.Path = $"/{interfaceType.Name}{builder.Path}";
        // 在传出消息上设置新的 Uri
        request.RequestUri = builder.Uri;

        return await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }
}
```

[//]: # '{% endraw %}'

完整的方法信息（`RestMethodInfo`）也始终在请求选项中可用。`RestMethodInfo` 包含有关被调用方法的更多信息，例如需要使用反射时的完整 `MethodInfo`：

[//]: # '{% raw %}'

```csharp
class RequestPropertyHandler : DelegatingHandler
{
    public RequestPropertyHandler(HttpMessageHandler innerHandler = null) : base(innerHandler ?? new HttpClientHandler()) {}

    protected override async Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
    {
        // 获取方法信息
        if (request.Options.TryGetValue(new HttpRequestOptionsKey<RestMethodInfo>(HttpRequestMessageOptions.RestMethodInfo), out RestMethodInfo restMethodInfo))
        {
            var builder = new UriBuilder(request.RequestUri);
            // 基于方法信息或其上的属性以某种方式更改路径
            builder.Path = $"/{restMethodInfo.MethodInfo.Name}{builder.Path}";
            // 在传出消息上设置新的 Uri
            request.RequestUri = builder.Uri;
        }

        return await base.SendAsync(request, cancellationToken).ConfigureAwait(false);
    }
}
```

[//]: # '{% endraw %}'

注意：在 .NET 5 中 `HttpRequestMessage.Properties` 已被标记为 `Obsolete`，Refit 将改为把值填充到新的 `HttpRequestMessage.Options` 中。Refit 提供了 `HttpRequestMessageOptions.InterfaceType` 和 `HttpRequestMessageOptions.RestMethodInfo` 来分别从选项中访问接口类型和 REST 方法信息。

### 多部分上传

使用 `Multipart` 属性装饰的方法将以多部分内容类型提交。目前，多部分方法支持以下参数类型：

- `string`（参数名称将用作名称，字符串值用作值）
- 字节数组
- `Stream`
- `FileInfo`

多部分数据中字段名称的优先级顺序：

- `multipartItem.Name`（如果指定且不为 null）（可选）；动态的，允许在执行时命名表单数据部分。
- `[AliasAs]` 属性（可选），装饰方法签名中的 streamPart 参数（见下文）；静态的，在代码中定义。
- `MultipartItem` 参数名称（默认），如方法签名中所定义；静态的，在代码中定义。

可以通过 `Multipart` 属性的可选字符串参数指定自定义边界。如果留空，默认为 `----MyGreatBoundary`。

要为字节数组（`byte[]`）、`Stream` 和 `FileInfo` 参数指定文件名和内容类型，需要使用包装类。这些类型的包装类分别是 `ByteArrayPart`、`StreamPart` 和 `FileInfoPart`。

```csharp
public interface ISomeApi
{
    [Multipart]
    [Post("/users/{id}/photo")]
    Task UploadPhoto(int id, [AliasAs("myPhoto")] StreamPart stream);
}
```

要将 `Stream` 传递给此方法，请按如下方式构造 StreamPart 对象：

```csharp
someApiInstance.UploadPhoto(id, new StreamPart(myPhotoStream, "photo.jpg", "image/jpeg"));
```

注意：本节中先前描述的 `AttachmentName` 属性已被弃用，不建议使用。

### 获取响应

请注意，在 Refit 中与 Retrofit 不同，没有同步网络请求的选项 - 所有请求必须是异步的，通过 `Task` 或 `IObservable`。也没有通过 Callback 参数创建异步方法的选项，因为我们已经生活在 async/await 的时代。

与请求体内容通过参数类型变化类似，返回类型将决定返回的内容。

返回没有类型参数的 Task 将丢弃内容，仅告诉你调用是否成功：

```csharp
[Post("/users/new")]
Task CreateUser([Body] User user);

// 如果网络调用失败，这将抛出异常
await CreateUser(someUser);
```

如果类型参数是 'HttpResponseMessage' 或 'string'，将分别返回原始响应消息或内容的字符串。

```csharp
// 返回内容的字符串（即 JSON 数据）
[Get("/users/{user}")]
Task<string> GetUser(string user);

// 返回原始响应，作为 IObservable 可与响应式扩展一起使用
[Get("/users/{user}")]
IObservable<HttpResponseMessage> GetUser(string user);
```

还有一个名为 `ApiResponse<T>` 的通用包装类可用作返回类型。使用此类作为返回类型不仅可以获取内容作为对象，还可以获取与请求/响应关联的任何元数据。这包括响应头、HTTP 状态码和原因短语（例如 404 Not Found）、响应版本、发送的原始请求消息以及在出错时包含错误详细信息的 `ApiException` 对象等信息。以下是一些如何获取响应元数据的示例。

```csharp
// 返回包含请求/响应元数据的包装类中的内容
[Get("/users/{user}")]
Task<ApiResponse<User>> GetUser(string user);

// 调用 API
var response = await gitHubApi.GetUser("octocat");

// 确定是否收到了成功状态码且没有其他错误
//（例如在内容反序列化期间）
if(response.IsSuccessful)
{
    // 太好了！做你的事情...
}

if (response.IsReceived)
{
    // 获取状态码（返回 System.Net.HttpStatusCode 枚举中的值）
    var httpStatus = response.StatusCode;

    // 获取已知的头值（例如 "Server" 头）
    var serverHeaderValue = response.Headers.Server != null ? response.Headers.Server.ToString() : string.Empty;

    // 获取自定义头值
    var customHeaderValue = string.Join(',', response.Headers.GetValues("A-Custom-Header"));

    // 遍历所有头
    foreach(var header in response.Headers)
    {
        var headerName = header.Key;
        var headerValue = string.Join(',', header.Value);
    }

    // 最后，将响应体中的内容作为强类型对象获取
    var user = response.Content;
}
```

### 使用泛型接口

当使用像 ASP.NET Web API 这样的框架时，拥有一整套 CRUD REST 服务是一个相当常见的模式。Refit 现在支持这些，允许你使用泛型类型定义单个 API 接口：

```csharp
public interface IReallyExcitingCrudApi<T, in TKey> where T : class
{
    [Post("")]
    Task<T> Create([Body] T payload);

    [Get("")]
    Task<List<T>> ReadAll();

    [Get("/{key}")]
    Task<T> ReadOne(TKey key);

    [Put("/{key}")]
    Task Update(TKey key, [Body]T payload);

    [Delete("/{key}")]
    Task Delete(TKey key);
}
```

可以这样使用：

```csharp
// 这里的 "/users" 部分相当重要，如果你希望它适用于多种类型
//（除非你为每种类型使用不同的域）
var api = RestService.For<IReallyExcitingCrudApi<User, string>>("http://api.example.com/users");
```

### 接口继承

当需要保持分离的多个服务共享一些 API 时，可以利用接口继承来避免在不同服务中多次定义相同的 Refit 方法：

```csharp
public interface IBaseService
{
    [Get("/resources")]
    Task<Resource> GetResource(string id);
}

public interface IDerivedServiceA : IBaseService
{
    [Delete("/resources")]
    Task DeleteResource(string id);
}

public interface IDerivedServiceB : IBaseService
{
    [Post("/resources")]
    Task<string> AddResource([Body] Resource resource);
}
```

在此示例中，`IDerivedServiceA` 接口将公开 `GetResource` 和 `DeleteResource` API，而 `IDerivedServiceB` 将公开 `GetResource` 和 `AddResource`。

#### 请求头继承

使用继承时，现有的头属性也会被传递，并且最内层的头具有优先权：

```csharp
[Headers("User-Agent: AAA")]
public interface IAmInterfaceA
{
    [Get("/get?result=Ping")]
    Task<string> Ping();
}

[Headers("User-Agent: BBB")]
public interface IAmInterfaceB : IAmInterfaceA
{
    [Get("/get?result=Pang")]
    [Headers("User-Agent: PANG")]
    Task<string> Pang();

    [Get("/get?result=Foo")]
    Task<string> Foo();
}
```

在这里，`IAmInterfaceB.Pang()` 将使用 `PANG` 作为其用户代理，而 `IAmInterfaceB.Foo` 和 `IAmInterfaceB.Ping` 将使用 `BBB`。请注意，如果 `IAmInterfaceB` 没有头属性，`Foo` 将使用从 `IAmInterfaceA` 继承的 `AAA` 值。如果接口继承了多个接口，优先级顺序与继承接口的声明顺序相同：

```csharp
public interface IAmInterfaceC : IAmInterfaceA, IAmInterfaceB
{
    [Get("/get?result=Foo")]
    Task<string> Foo();
}
```

这里 `IAmInterfaceC.Foo` 将使用从 `IAmInterfaceA` 继承的头属性（如果存在），或者从 `IAmInterfaceB` 继承的头属性，依此类推。

### 默认接口方法

从 C# 8.0 开始，可以在接口上定义默认接口方法（也称为 DIM）。Refit 接口可以使用 DIM 提供额外的逻辑，可选地与私有和/或静态辅助方法结合使用：

```csharp
public interface IApiClient
{
    // 由 Refit 实现但不公开暴露
    [Get("/get")]
    internal Task<string> GetInternal();
    // 公开可用，对 API 调用的结果应用了额外逻辑
    public async Task<string> Get()
        => FormatResponse(await GetInternal());
    private static String FormatResponse(string response)
        => $"The response is: {response}";
}
```

Refit 生成的类型将实现 `IApiClient.GetInternal` 方法。如果在调用之前或之后需要额外逻辑，它不应该直接暴露，因此可以通过标记为 `internal` 来对使用者隐藏。默认接口方法 `IApiClient.Get` 将被实现 `IApiClient` 的所有类型继承，包括 - 当然 - Refit 生成的类型。`IApiClient` 的使用者将调用公共的 `Get` 方法，并从其实现中提供的额外逻辑中受益（可选地，在此情况下，借助私有静态辅助方法 `FormatResponse`）。为了支持没有 DIM 支持的运行时（.NET Core 2.x 及以下或 .NET Standard 2.0 及以下），相同的解决方案需要两个额外的类型。

```csharp
internal interface IApiClientInternal
{
    [Get("/get")]
    Task<string> Get();
}
public interface IApiClient
{
    public Task<string> Get();
}
internal class ApiClient : IApiClient
{
    private readonly IApiClientInternal client;
    public ApiClient(IApiClientInternal client) => this.client = client;
    public async Task<string> Get()
        => FormatResponse(await client.Get());
    private static String FormatResponse(string response)
        => $"The response is: {response}";
}
```

### 使用 HttpClientFactory

Refit 对 ASP.Net Core 2.1 HttpClientFactory 提供了一流的支持。添加对 `Refit.HttpClientFactory` 的引用，并在 `ConfigureServices` 方法中调用提供的扩展方法来配置你的 Refit 接口：

```csharp
services.AddRefitClient<IWebApi>()
        .ConfigureHttpClient(c => c.BaseAddress = new Uri("https://api.example.com"));
        // 根据需要在此处添加额外的 IHttpClientBuilder 链式方法：
        // .AddHttpMessageHandler<MyHandler>()
        // .SetHandlerLifetime(TimeSpan.FromMinutes(2));
```

可选地，可以包含一个 `RefitSettings` 对象：

```csharp
var settings = new RefitSettings();
// 在此配置 refit 设置

services.AddRefitClient<IWebApi>(settings)
        .ConfigureHttpClient(c => c.BaseAddress = new Uri("https://api.example.com"));
        // 根据需要在此处添加额外的 IHttpClientBuilder 链式方法：
        // .AddHttpMessageHandler<MyHandler>()
        // .SetHandlerLifetime(TimeSpan.FromMinutes(2));

// 或从容器中注入
services.AddRefitClient<IWebApi>(provider => new RefitSettings() { /* 配置设置 */ })
        .ConfigureHttpClient(c => c.BaseAddress = new Uri("https://api.example.com"));
        // 根据需要在此处添加额外的 IHttpClientBuilder 链式方法：
        // .AddHttpMessageHandler<MyHandler>()
        // .SetHandlerLifetime(TimeSpan.FromMinutes(2));

```

请注意，`RefitSettings` 的某些属性将被忽略，因为 `HttpClient` 和 `HttpClientHandlers` 将由 `HttpClientFactory` 而不是 Refit 管理。

然后你可以使用构造函数注入获取 API 接口：

```csharp
public class HomeController : Controller
{
    public HomeController(IWebApi webApi)
    {
        _webApi = webApi;
    }

    private readonly IWebApi _webApi;

    public async Task<IActionResult> Index(CancellationToken cancellationToken)
    {
        var thing = await _webApi.GetSomethingWeNeed(cancellationToken);
        return View(thing);
    }
}
```

### 提供自定义 HttpClient

你可以通过简单地将自定义 `HttpClient` 实例作为参数传递给 `RestService.For<T>` 方法来提供它：

```csharp
RestService.For<ISomeApi>(new HttpClient()
{
    BaseAddress = new Uri("https://www.someapi.com/api/")
});
```

但是，当提供自定义 `HttpClient` 实例时，`HttpMessageHandlerFactory` 将不会被使用，因为你已经控制了处理程序管道。

当请求包含 `Authorization` 头占位符（例如 `[Headers("Authorization: Bearer")]`）时，`AuthorizationHeaderValueGetter` 仍然可以与 `RestService.For<T>(httpClient, settings)` 一起工作。

如果你仍然希望能够配置 `Refit` 提供的 `HttpClient` 实例，同时使用上述设置，只需在 API 接口上公开 `HttpClient`：

```csharp
interface ISomeApi
{
    // 如果属性存在，Refit 将自动填充它
    HttpClient Client { get; }

    [Headers("Authorization: Bearer")]
    [Get("/endpoint")]
    Task<string> SomeApiEndpoint();
}
```

然后，在创建 REST 服务后，你可以设置任何你想要的 `HttpClient` 属性，例如 `Timeout`：

```csharp
SomeApi = RestService.For<ISomeApi>("https://www.someapi.com/api/", new RefitSettings()
{
    AuthorizationHeaderValueGetter = (rq, ct) => GetTokenAsync()
});

SomeApi.Client.Timeout = timeout;
```

### 原生 AoT / 裁剪指导

Refit 推荐的用于原生 AoT 和裁剪应用程序的**源代码生成器优先**设置是：

1. 使用普通的 Refit 接口，以便 Refit 源代码生成器在构建时生成客户端实现。
2. 尽可能优先使用 `RestService.For<T>(...)` 而非围绕 `Type` 的反射密集型手动模式。
3. 为你的 DTO 提供源代码生成的 `System.Text.Json` 元数据。

对于 .NET 8+ 上的默认 `SystemTextJsonContentSerializer`，Refit 在可用时优先使用你配置的 `JsonSerializerOptions` 中的 `JsonTypeInfo` 元数据。这意味着原生 AoT 应用可以通过在传入 `SystemTextJsonContentSerializer` 的序列化器选项上提供源代码生成的元数据（通过 `JsonSerializerContext` 或 `TypeInfoResolver`）来提高兼容性。

```csharp
[JsonSerializable(typeof(Todo))]
public partial class TodoJsonContext : JsonSerializerContext
{
}

var settings = new RefitSettings(
    new SystemTextJsonContentSerializer(
        new JsonSerializerOptions(JsonSerializerDefaults.Web)
        {
            TypeInfoResolver = TodoJsonContext.Default
        }
    )
);

var api = RestService.For<ITodoApi>("https://api.example.com", settings);
```

如果在运行时找不到生成的 Refit 客户端，Refit 现在会明确将你指向源代码生成器/构建输出，并推荐为原生 AoT 场景使用生成的客户端加上源代码生成的 `System.Text.Json` 元数据。

Refit 还为较新的 Roslyn 工具链提供了分析器，包括为较新 Visual Studio 版本准备的 Roslyn 5.0 构建。

### 处理异常

Refit 根据你的 Refit 接口方法返回 `Task<T>` 还是返回 `Task<IApiResponse>`、`Task<IApiResponse<T>>` 或 `Task<ApiResponse<T>>` 有不同的异常处理行为。

#### <a id="当返回-taskapiresponset-时"></a>返回 `Task<IApiResponse>`、`Task<IApiResponse<T>>` 或 `Task<ApiResponse<T>>` 时

Refit 将 `HttpClient` 抛出的任何 `HttpRequestException` 或 `TaskCanceledException` 捕获到 `ApiRequestException` 中。Refit 还会捕获处理响应时 `ExceptionFactory` 抛出的任何 `ApiException`，以及在尝试将响应反序列化为 `ApiResponse<T>` 时发生的任何错误。在两种情况下，它都会将异常填充到 `ApiResponse<T>` 的 `Error` 属性中，而不会抛出异常。

然后你可以决定如何处理：

```csharp
var response = await _myRefitClient.GetSomeStuff();
if(response.IsSuccessful)
{
   // 做你的事情
}
else
{
    // 如果你想区分请求错误和响应错误
    if (response.HasRequestError(out var requestError))
        _logger.LogError(requestError, "发送请求时发生错误。");
    else if (response.HasResponseError(out var responseError))
        _logger.LogError(responseError, responseError.Content);

    // 或者直接记录错误
    _logger.LogError(response.Error, "调用 API 时发生错误。");
}
```

> [!NOTE]
> `IsSuccessful` 属性检查响应状态代码是否在 200-299 范围内且没有其他错误（例如在内容反序列化期间）。如果你只想检查 HTTP 响应状态代码，可以使用 `IsSuccessStatusCode` 属性。

#### 返回 `Task<T>` 时

Refit 抛出 `HttpClient` 抛出的任何异常，并将其包装在 `ApiRequestException` 中。它还抛出处理响应时 `ExceptionFactory` 抛出的任何 `ApiException`，以及在尝试将响应反序列化为 `Task<T>` 时发生的任何错误。

```csharp
// ...
try
{
   var result = await awesomeApi.GetFooAsync("bar");
}
catch (ApiRequestException exception)
{
    // 未从服务器收到响应时的异常处理
}
catch (ApiException exception)
{
   // 收到服务器响应时的异常处理
}
// 或者不区分请求/响应异常
catch (ApiExceptionBase exception)
{
   // 请求/响应期间发生错误时的异常处理
}
// ...
```

Refit 也可以抛出 `ValidationApiException`，除了 `ApiException` 上的信息外，当服务实现了 [RFC 7807](https://tools.ietf.org/html/rfc7807) 问题详细信息规范且响应内容类型为 `application/problem+json` 时，它还包含 `ProblemDetails`。

要获取验证异常的问题详细信息的具体信息，只需捕获 `ValidationApiException`：

```csharp
// ...
try
{
   var result = await awesomeApi.GetFooAsync("bar");
}
catch (ValidationApiException validationException)
{
   // 通过使用 validationException.Content 在此处处理验证，
   // 其类型为 RFC 7807 中的 ProblemDetails

   // 如果响应包含问题详细信息上的额外属性，
   // 它们将被添加到 validationException.Content.Extensions 集合中。
}
catch (ApiException exception)
{
   // 其他异常处理
}
// ...
```

#### 提供自定义 `ExceptionFactory`

你还可以通过在 `RefitSettings` 中提供自定义异常工厂来覆盖处理结果时 `ExceptionFactory` 抛出的默认异常行为。例如，你可以使用以下代码抑制所有 `ApiException`：

```csharp
var nullTask = Task.FromResult<Exception>(null);

var gitHubApi = RestService.For<IGitHubApi>("https://api.github.com",
    new RefitSettings {
        ExceptionFactory = httpResponse => nullTask;
    });
```

对于尝试反序列化响应时引发的异常，请使用下面描述的 DeserializationExceptionFactory。

#### 提供自定义 `DeserializationExceptionFactory`

你可以通过在 `RefitSettings` 中提供自定义异常工厂来覆盖处理结果时 `DeserializationExceptionFactory` 抛出的默认反序列化异常行为。例如，你可以使用以下代码抑制所有反序列化异常：

```csharp
var nullTask = Task.FromResult<Exception>(null);

var gitHubApi = RestService.For<IGitHubApi>("https://api.github.com",
    new RefitSettings {
        DeserializationExceptionFactory = (httpResponse, exception) => nullTask;
    });
```

#### 使用 Serilog 解构 `ApiException`

对于 [Serilog](https://serilog.net) 的用户，你可以使用 [Serilog.Exceptions.Refit](https://www.nuget.org/packages/Serilog.Exceptions.Refit) NuGet 包来丰富 `ApiException` 的日志记录。有关如何将此包集成到你的应用程序中的详细信息，请参见[此处](https://github.com/RehanSaeed/Serilog.Exceptions#serilogexceptionsrefit)。
