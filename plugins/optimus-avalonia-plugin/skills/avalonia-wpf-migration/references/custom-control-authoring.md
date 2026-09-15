# Authoring Custom Properties and Events

Reference for writing **new** properties and routed events on custom controls after migrating. Most WPF→Avalonia migrations only consume properties, not define them — that is why this material lives here rather than in `SKILL.md`. Load it when you subclass `TemplatedControl`/`Control` and need to add a property or event.

## DirectProperty

Backs a CLR auto-property. Use it for read-only or performance-sensitive properties. There is no direct WPF equivalent — the closest is a read-only dependency property.

```csharp
public static readonly DirectProperty<MyControl, string> StatusProperty =
    AvaloniaProperty.RegisterDirect<MyControl, string>(nameof(Status), o => o.Status);

private string _status = "Ready";
public string Status
{
    get => _status;
    private set => SetAndRaise(StatusProperty, ref _status, value);
}
```

Two hard requirements:

- The **getter accessor lambda** (`o => o.Status`) is mandatory — the property system uses it to read the current value.
- The CLR setter must call **`SetAndRaise`**, not `SetValue`. Calling `SetValue` on a `DirectProperty` **throws**. `SetAndRaise` updates the backing field and raises the change notification together.

## AttachedProperty

For properties you set on *child* elements from a parent — `Grid.Row`, `DockPanel.Dock`.

```csharp
public static readonly AttachedProperty<Dock> DockProperty =
    AvaloniaProperty.RegisterAttached<DockPanel, Control, Dock>(
        "Dock", defaultValue: Dock.Left);

public static Dock GetDock(Control element) => element.GetValue(DockProperty);
public static void SetDock(Control element, Dock value) => element.SetValue(DockProperty, value);
```

⚠️ The accessor parameter type changes: WPF's `DependencyObject` becomes `Control`.

## Coercion

Replaces `CoerceValueCallback` from WPF's `PropertyMetadata`. Passed as the `coerce:` named argument at registration.

```csharp
public static readonly StyledProperty<double> ProgressProperty =
    AvaloniaProperty.Register<MyControl, double>(
        nameof(Progress), defaultValue: 0.0, coerce: CoerceProgress);

private static double CoerceProgress(AvaloniaObject sender, double value)
    => Math.Clamp(value, 0.0, 1.0);
```

## Sharing and overriding properties

WPF's `OverrideMetadata` splits into two mechanisms depending on intent.

```csharp
// Adopting another control's property as your own (cross-type sharing)
public static readonly StyledProperty<IBrush> BackgroundProperty =
    Border.BackgroundProperty.AddOwner<MyControl>();

// …optionally with a new default value
public static readonly StyledProperty<IBrush> BackgroundProperty =
    Border.BackgroundProperty.AddOwner<MyControl>(
        new StyledPropertyMetadata<IBrush>(Brushes.Gray));

// Changing only the default in a subclass — runs in the static constructor
static MyDerivedControl()
{
    BackgroundProperty.OverrideDefaultValue<MyDerivedControl>(Brushes.Black);
}
```

## Custom routed events

`EventManager.RegisterRoutedEvent` becomes `RoutedEvent.Register`. Both the owner type and the event-args type are **generic parameters**, so no delegate type is passed — and no `typeof()` calls.

```csharp
// WPF: EventManager.RegisterRoutedEvent(name, strategy, typeof(Handler), typeof(Owner))
public static readonly RoutedEvent<RoutedEventArgs> TapEvent =
    RoutedEvent.Register<MyControl, RoutedEventArgs>(
        "Tap", RoutingStrategy.Bubble);

// CLR wrapper uses EventHandler<T>, not RoutedEventHandler
public event EventHandler<RoutedEventArgs>? Tap;

RaiseEvent(new RoutedEventArgs(TapEvent));
```

## Class handlers

WPF registers a **static** handler via `EventManager.RegisterClassHandler`; Avalonia calls `AddClassHandler` on the event instance from a static constructor, and the handler is an **instance** method — the notification routes to the correct instance automatically, so no `sender` parameter is needed.

```csharp
// WPF: EventManager.RegisterClassHandler(typeof(MyControl), MyEvent, HandleMyEvent)
static MyControl()
{
    MyEvent.AddClassHandler<MyControl>((x, e) => x.HandleMyEvent(e));
}

private void HandleMyEvent(RoutedEventArgs e) { }
```

## Handling the tunnel phase

Avalonia has no separate `Preview*` CLR events — tunnelling and bubbling share one `RoutedEvent` instance. Subscribe to the tunnel phase explicitly:

```csharp
myControl.AddHandler(InputElement.KeyDownEvent,
    OnPreviewKeyDown, RoutingStrategies.Tunnel);

// Both phases
myControl.AddHandler(InputElement.KeyDownEvent, OnKeyDown,
    RoutingStrategies.Tunnel | RoutingStrategies.Bubble);
```

Two signature details: `AddHandler` takes the delegate directly (no `new RoutedEventHandler(...)` wrapper), and `RoutingStrategies` must be supplied **before** `handledEventsToo` when you need both.
