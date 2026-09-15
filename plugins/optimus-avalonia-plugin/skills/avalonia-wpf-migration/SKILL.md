---
name: avalonia-wpf-migration
description: Use when migrating a WPF application to Avalonia, mapping WPF concepts to Avalonia equivalents, or understanding differences between WPF and Avalonia APIs.
metadata:
  version: "1.1.1"
  author: desktop client team
  category: platform
---
# Avalonia WPF Migration

## Overview
Avalonia's API is intentionally WPF-like. Most XAML, binding, and MVVM patterns transfer directly. Key differences: styling system, ControlTemplates → ControlThemes, no Triggers, `.axaml` extension, namespace differences.

Sections below lead with the highest-risk differences. Styling, `TemplateBinding`, and the property system each contain traps that fail **silently** — the code compiles and runs, but does the wrong thing. Prioritise those over the mechanical renames.

## Quick Mapping Table
| WPF | Avalonia | Notes |
|---|---|---|
| `.xaml` | `.axaml` | Extension differs |
| `xmlns="http://schemas.microsoft.com/winfx/2006/xaml/presentation"` | `xmlns="https://github.com/avaloniaui"` | Root namespace |
| `xmlns:local="clr-namespace:MyApp"` | `xmlns:local="using:MyApp"` | `clr-namespace:` still works |
| `DependencyProperty` | `StyledProperty` / `DirectProperty` / `AttachedProperty` | Three types — see Property System |
| `FrameworkElement`, `UIElement` | `Control` | Base for custom controls |
| `UserControl` (base) | `UserControl` | Same name, similar API |
| `Control` (for lookless) | `TemplatedControl` | Different base class |
| `Visibility` (`Visible`/`Collapsed`/`Hidden`) | `IsVisible` (bool) | `Hidden` → `Opacity="0"` |
| `Style` with `TargetType`, no `x:Key` | `ControlTheme` | Implicit style role — see Style vs ControlTheme |
| `Style` with `TargetType` + setters | `Style` with `Selector` | Not every style is a ControlTheme |
| `Style x:Key` + `Style="{StaticResource ...}"` | Style class (`Classes="..."`) | |
| `Style` with `Triggers` | `Style` with nested styles + pseudoclasses | No Triggers in Avalonia |
| `DataTrigger` | Binding + pseudoclass / converter | Pattern change |
| `TemplateBinding` | `TemplateBinding` | **OneWay only** — see below |
| `{Binding RelativeSource={RelativeSource TemplatedParent}}` | `{TemplateBinding X}` | Or full `Binding` for TwoWay |
| `RelativeSource Self` | `{Binding $self.Property}` | Different syntax |
| `RelativeSource AncestorType` | `{Binding $parent[TypeName].Property}` | Different syntax |
| `ElementName=myControl` | `#myControl` | e.g. `{Binding #myControl.Text}` |
| `ResourceDictionary` `Source=` | `ResourceInclude Source="avares://..."` | No `Source` property — add to `MergedDictionaries` |
| `pack://application:,,,/` | `avares://AssemblyName/` | Asset URI scheme |
| `EventManager.RegisterRoutedEvent` | `RoutedEvent.Register<TOwner, TArgs>` | Generic, not `typeof()` |
| `MouseLeftButtonDown` / `MouseRightButtonDown` | `PointerPressed` | Branch on `PointerUpdateKind` |
| `MouseMove` / `MouseEnter` / `MouseLeave` | `PointerMoved` / `PointerEntered` / `PointerExited` | Pointer naming |
| `MouseWheel` | `PointerWheelChanged` | |
| `Preview*` events | `AddHandler` + `RoutingStrategies.Tunnel` | No separate Preview events |
| `PropertyMetadata` | `defaultValue:` / `coerce:` args on `Register` | No `PropertyMetadata` class |
| `OverrideMetadata` | `AddOwner<T>()` / `OverrideDefaultValue<T>()` | Different mechanism |
| `RoutedCommand` / `CommandBinding` | No built-in equivalent | Use `ICommand` |
| `Window.ShowDialog()` | `window.ShowDialog(owner)` | Requires owner parameter |
| `MessageBox.Show()` | No built-in — use dialog or notification | API removed |
| `Dispatcher.Invoke()` | `Dispatcher.UIThread.InvokeAsync()` | Async-first |
| `Dispatcher.BeginInvoke()` | `Dispatcher.UIThread.Post()` | Fire-and-forget |
| `BindingOperations.ClearBinding()` | `control.ClearValue(prop)` | Avalonia `BindingOperations` has no `ClearBinding` |
| `AllowsTransparency="True"` | `TransparencyLevelHint="Transparent"` | No click-through support |
| `WindowStyle="None"` | `WindowDecorations="None"` | |
| `ResizeMode` | `CanResize` (bool) | Enum → bool |
| `LayoutTransform` | `LayoutTransformControl` | Needs a wrapper control |
| `DrawingBrush` | `VisualBrush` | `DrawingBrush` unavailable |
| `RenderTransformOrigin` default `TopLeft` | default `Center` | Silent rendering difference |
| `SystemParameters.PrimaryScreenWidth` | `TopLevel.GetTopLevel(this).Screens.Primary.Bounds.Width` | See Platform Services |
| `x:Static` | `x:Static` | Same |
| `IValueConverter` / `IMultiValueConverter` | Same | Same interface |
| `ObservableCollection<T>` | `ObservableCollection<T>` | Same |
| `ICommand` | `ICommand` | Same |
| `CollectionViewSource` | `DataGridCollectionView` | No general equivalent — `DataGrid` only, separate package |
| `Frame` + `NavigationService` | ContentControl + ViewModel swap | MVVM pattern preferred |

## Styles: No Triggers
WPF:
```xml
<!-- WPF - DOES NOT WORK in Avalonia -->
<Style TargetType="Button">
    <Style.Triggers>
        <Trigger Property="IsMouseOver" Value="True">
            <Setter Property="Background" Value="Red"/>
        </Trigger>
    </Style.Triggers>
</Style>
```
Avalonia:
```xml
<Style Selector="Button:pointerover">
    <Setter Property="Background" Value="Red"/>
</Style>
```

### Trigger → pseudoclass mapping
| WPF trigger property | Avalonia pseudoclass |
|---|---|
| `IsMouseOver` | `:pointerover` |
| `IsPressed` | `:pressed` |
| `IsEnabled="False"` | `:disabled` |
| `IsChecked="True"` | `:checked` |
| `IsFocused` | `:focus` |
| `IsSelected` | `:selected` |
| `IsExpanded` | `:expanded` |

## Style vs ControlTheme
**Do not map every `Style TargetType` to `ControlTheme`.** Only the implicit-style role does. Decide by what the WPF style was for:

| WPF style was… | Migrate to… |
|---|---|
| Setting the default look/template of a control type — implicit `Style TargetType` with no `x:Key`, including one that sets `Template` | **`ControlTheme`** |
| Applying setters to controls matched by type, class, state, or nesting | **`Style`** with `Selector` |
| Named via `x:Key` and referenced with `Style="{StaticResource ...}"` | **Style class** — `Classes="..."` |

Three mechanical differences follow:

- `ControlTheme` lives in `Resources`, normally keyed `{x:Type ControlType}` so it auto-applies. `Style` lives in the `Styles` collection.
- `ControlTheme` **does not cascade** — only one applies to a control at a time. Styles are matched top-down by selector specificity.
- Inside a `ControlTheme`, nested `Style` elements use the `^` selector to refer to the templated control itself.

```xml
<ControlTheme x:Key="{x:Type Button}" TargetType="Button">
    <Setter Property="Template">
        <ControlTemplate>
            <Border Background="{TemplateBinding Background}">
                <ContentPresenter HorizontalAlignment="Center"
                                  VerticalAlignment="Center"/>
            </Border>
        </ControlTemplate>
    </Setter>
    <Style Selector="^:pointerover">
        <Setter Property="Background" Value="LightBlue"/>
    </Style>
</ControlTheme>
```

WPF explicit styles become style classes — this removes the need to manage resource keys:

```xml
<Window.Styles>
    <Style Selector="Button.primary">
        <Setter Property="Background" Value="SteelBlue"/>
    </Style>
</Window.Styles>
<Button Classes="primary" Content="Save"/>
```

## ControlTemplate → ControlTheme
WPF:
```xml
<Style TargetType="Button">
    <Setter Property="Template">
        <Setter.Value>
            <ControlTemplate TargetType="Button">
                ...
            </ControlTemplate>
        </Setter.Value>
    </Setter>
</Style>
```
Avalonia:
```xml
<ControlTheme TargetType="Button" x:Key="{x:Type Button}">
    <Setter Property="Template">
        <ControlTemplate>
            ...
        </ControlTemplate>
    </Setter>
</ControlTheme>
```

## TemplateBinding Is OneWay Only
`TemplateBinding` looks like a direct port but its binding direction differs: **WPF's is TwoWay by default, Avalonia's is OneWay only.** A template that relied on the TwoWay default compiles and runs, then silently fails to push edits back to the source — the classic symptom is a templated `TextBox` that never updates its bound property.

```xml
<!-- OneWay only in Avalonia -->
<TextBox Text="{TemplateBinding SearchText}"/>
```

For TwoWay inside a template, use a full `Binding` with an explicit `Mode`:

```xml
<TextBox Text="{Binding SearchText, RelativeSource={RelativeSource TemplatedParent}, Mode=TwoWay}"/>
```

`TemplateBinding` also accepts a single property only — no property paths. For paths, or for elements that aren't `IStyledElement`, use the `Binding` form above.

## RelativeSource Binding
```xml
<!-- WPF -->
<TextBlock Text="{Binding RelativeSource={RelativeSource AncestorType=Window}, Path=Title}"/>

<!-- Avalonia -->
<TextBlock Text="{Binding $parent[Window].Title}"/>
<TextBlock Text="{Binding $self.Tag}"/>
<TextBlock Text="{Binding $parent.Tag}"/>
```

## Events
### No separate Preview events
Avalonia has no `Preview*` CLR events. Tunnelling and bubbling share one `RoutedEvent`; subscribe to the tunnel phase via `AddHandler`:

```csharp
myControl.AddHandler(InputElement.KeyDownEvent,
    OnPreviewKeyDown, RoutingStrategies.Tunnel);

// Both phases
myControl.AddHandler(InputElement.KeyDownEvent, OnKeyDown,
    RoutingStrategies.Tunnel | RoutingStrategies.Bubble);
```

### Input event names
| WPF | Avalonia |
|---|---|
| `MouseLeftButtonDown` / `MouseRightButtonDown` | `PointerPressed` |
| `MouseLeftButtonUp` / `MouseRightButtonUp` | `PointerReleased` |
| `MouseMove` | `PointerMoved` |
| `MouseEnter` | `PointerEntered` |
| `MouseLeave` | `PointerExited` |
| `MouseWheel` | `PointerWheelChanged` |
| `PreviewKeyDown` | `KeyDownEvent` + `RoutingStrategies.Tunnel` |

Which mouse button fired is read from `PointerUpdateKind`, not from the event name — Avalonia unified mouse, touch, and pen into pointers.

### Class handlers and custom event registration
Both are custom-control authoring concerns, not migration mappings — see `references/custom-control-authoring.md`.

Two signature notes for the `AddHandler` calls you keep: it takes the delegate directly (no `new RoutedEventHandler(...)` wrapper), and `RoutingStrategies` must be specified *before* `handledEventsToo`.

## Property System
WPF has one `DependencyProperty` class; Avalonia splits the role three ways over a shared `AvaloniaProperty` base.

| WPF | Avalonia | Use for |
|---|---|---|
| `DependencyProperty` | `StyledProperty` | Styling, animation, inheritance |
| `DependencyProperty` (read-only) | `DirectProperty` | Read-only, performance-sensitive, CLR-field-backed |
| `RegisterAttached` | `AttachedProperty` | Properties set on child elements, e.g. `Grid.Row` |

```csharp
// StyledProperty — generics remove the cast in GetValue; default value is a named arg
public static readonly StyledProperty<IBrush> BackgroundProperty =
    AvaloniaProperty.Register<MyControl, IBrush>(
        nameof(Background), defaultValue: Brushes.Transparent);

public IBrush Background
{
    get => GetValue(BackgroundProperty);
    set => SetValue(BackgroundProperty, value);
}
```

`DirectProperty` and `AttachedProperty` registration follow the same generic shape — full examples and their two traps (the mandatory getter lambda; `SetValue` throwing on a `DirectProperty`) are in `references/custom-control-authoring.md`.

### There is no `PropertyMetadata` class
Default values go straight into `Register`. `PropertyChangedCallback` has two replacements, both equivalent:

```csharp
// Option 1 — override (preferred; clearer when handling several properties together)
protected override void OnPropertyChanged(AvaloniaPropertyChangedEventArgs change)
{
    base.OnPropertyChanged(change);
    if (change.Property == IsActiveProperty)
        UpdateVisualState();
}

// Option 2 — class handler, registered separately from the property definition
static MyControl()
{
    IsActiveProperty.Changed.AddClassHandler<MyControl>((control, args) =>
        control.UpdateVisualState());
}
```

### Coercion, overrides, and ownership
WPF's `CoerceValueCallback` becomes the `coerce:` named argument at registration. `OverrideMetadata` splits by intent into `AddOwner<T>()` (cross-type sharing) and `OverrideDefaultValue<T>()` (subclass default). Code for both is in `references/custom-control-authoring.md`.

⚠️ `StyledProperty` does **not** use a backing field — the property system stores the value. Adding your own field and reading from it returns stale data; always use `GetValue`/`SetValue`.

Value precedence is the same order in both frameworks: animation → local value → style setters → template parent → inherited → default.

## Layout
Containers carry over with the same names and attached properties. Three additions change how you'd write them.

**`StackPanel.Spacing`** replaces per-child margins:

```xml
<!-- WPF: margin on each child -->
<StackPanel>
    <Button Content="First" Margin="0,0,0,8" />
    <Button Content="Second" />
</StackPanel>
```
```xml
<!-- Avalonia -->
<StackPanel Spacing="8">
    <Button Content="First" />
    <Button Content="Second" />
</StackPanel>
```

**Grid definition shorthand** — one attribute instead of nested elements:

```xml
<Grid ColumnDefinitions="Auto,*,200" RowDefinitions="Auto,*" />
```

⚠️ This shorthand also works in WPF on .NET 6+, so it is not a migration requirement — but it is idiomatic Avalonia.

**`Panel` for layering.** WPF developers overlap elements with a `Grid` that defines no rows or columns. Avalonia has a lightweight `Panel` for exactly this; it avoids spinning up the Grid layout engine:

```xml
<!-- WPF approach -->
<Grid>
    <Image Source="background.png" />
    <TextBlock Text="Overlay" />
</Grid>
```
```xml
<!-- Avalonia preferred -->
<Panel>
    <Image Source="background.png" />
    <TextBlock Text="Overlay" />
</Panel>
```

Two defaults worth checking: `DockPanel.LastChildFill` defaults to **`true`** (verify if the WPF code set it explicitly), and `ScrollViewer` scrollbar behaviors are identical in name but default slightly differently per platform — test on each target. `UseLayoutRounding` behaves as in WPF.

## Controls
| WPF / UWP | Avalonia |
|---|---|
| `UIElement`, `FrameworkElement` | `Control` |
| `Control` (lookless) | `TemplatedControl` |

Most controls keep their names: `Window`, `UserControl`, `Button`, `TextBlock`, `TextBox`, `CheckBox`, `RadioButton`, `ComboBox`, `ListBox`, `TreeView`, `TabControl`, `Expander`, `Slider`, `ProgressBar`, `Menu`, `ContextMenu`, `Popup`, `ScrollViewer`, `Image`, `Viewbox`, `ContentControl`, `ItemsControl`, `StackPanel`, `Grid`, `DockPanel`, `WrapPanel`, `Canvas`, `UniformGrid`, `GroupBox`.

### Controls with no direct equivalent
- **`StatusBar`** — none. Use a styled `Border` docked to the bottom:

```xml
<DockPanel>
  <Border DockPanel.Dock="Bottom"
          Background="{DynamicResource SystemChromeLowColor}"
          Padding="8,4">
    <TextBlock Text="Ready" />
  </Border>
  <!-- main content -->
</DockPanel>
```

- **`RichTextBox`** — no built-in rich text editor; use a third-party control (e.g. AvalonEdit).

### Controls that need extra setup
- **`DataGrid`** ships in its own package (`Avalonia.Controls.DataGrid`) **and** needs its theme registered in `App.axaml` — missing the theme registration is the usual cause of an unstyled or blank grid.

```xml
<PackageReference Include="Avalonia.Controls.DataGrid" Version="$(AvaloniaVersion)" />
```
```xml
<Application.Styles>
  <FluentTheme />
  <StyleInclude Source="avares://Avalonia.Controls.DataGrid/Themes/Fluent.xaml" />
</Application.Styles>
```

- **`ToolTip`** becomes an attached property: `<Button ToolTip.Tip="Save" Content="Save" />`.

### `Items` is read-only
`ItemsControl.Items` cannot be assigned a collection in Avalonia. Bind through `ItemsSource` (or add children directly in XAML).

`ListView` has no separate control — use `ListBox` with an `ItemTemplate`:

```xml
<ListBox ItemsSource="{Binding MyItems}">
  <ListBox.ItemTemplate>
    <DataTemplate>
      <TextBlock Text="{Binding Name}" />
    </DataTemplate>
  </ListBox.ItemTemplate>
</ListBox>
```

## Commands
`ICommand` is unchanged, and MVVM Toolkit's `RelayCommand` works as-is.

What doesn't survive is WPF's *routed command infrastructure*:

| WPF | Avalonia |
|---|---|
| `RoutedCommand` | No built-in equivalent — implement `ICommand` |
| `CommandBinding` | No equivalent — bind the command directly to the control |
| `InputBinding` / `KeyBinding` | `KeyBinding` — same concept |
| `RelayCommand` (MVVM Toolkit) | Same library works |

The practical migration: replace `RoutedCommand` + `CommandBinding` pairs with a view-model `ICommand` bound to `Command`, and wire keyboard shortcuts with `KeyBinding`. Prefer `CommunityToolkit.Mvvm` over hand-rolling `ICommand`.

## Windows
| WPF | Avalonia | Note |
|---|---|---|
| `AllowsTransparency="True"` | `TransparencyLevelHint="Transparent"` | Avalonia has no click-through equivalent |
| `WindowStyle="None"` | `WindowDecorations="None"` | Removes title bar and border |
| `ResizeMode` (enum) | `CanResize` (bool) | Enum collapses to a boolean |

## Graphics and Transforms
| WPF | Avalonia |
|---|---|
| `SolidColorBrush`, `LinearGradientBrush`, `RadialGradientBrush`, `ImageBrush`, `VisualBrush`, `Clip`, `OpacityMask`, `Path` | Same |
| `DrawingBrush` | Unavailable — use `VisualBrush` |
| `BitmapEffect` | `Effect` — e.g. `BlurEffect`, `DropShadowEffect` |
| `DropShadowEffect` | `BoxShadow` on `Border` (CSS-style API) |
| `RenderTransform` | Same, plus a CSS-style shorthand |
| `LayoutTransform` | `LayoutTransformControl` — wrap the element in it |

### `RenderTransformOrigin` defaults differ — silent rendering bug
Avalonia defaults `RenderTransformOrigin` to **`RelativePoint.Center`**; WPF defaults it to **`RelativePoint.TopLeft`** (0,0). Identical markup therefore renders differently — rotation and scale pivot around a different point, which shows up most visibly inside a `Viewbox`.

To reproduce WPF's behaviour, set the origin explicitly:

```xml
<Border RenderTransformOrigin="0,0">
    <Border.RenderTransform>
        <RotateTransform Angle="45"/>
    </Border.RenderTransform>
</Border>
```

## Platform Services
WPF's static `SystemParameters` / `Screen` API is replaced by instance services reached through `TopLevel`. It returns `null` before the control is attached to the visual tree, so call it from `OnAttachedToVisualTree` or later.

```csharp
var topLevel = TopLevel.GetTopLevel(this);   // 'this' = any attached control
```

| WPF | Avalonia |
|---|---|
| `SystemParameters.PrimaryScreenWidth` | `topLevel.Screens.Primary.Bounds.Width` |
| `Screen.AllScreens` | `topLevel.Screens.All` |
| `Screen.PrimaryScreen.WorkingArea` | `topLevel.Screens.Primary.WorkingArea` (excludes taskbar/Dock) |
| `CompositionTarget.TransformToDevice` | `topLevel.Screens.Primary.Scaling` (DPI scale factor) |

Clipboard, file dialogs, launcher, and notifications are also `TopLevel` services — see the `avalonia-services` skill.

## Asset URIs
```xml
<!-- WPF -->
<Image Source="pack://application:,,,/Assets/logo.png"/>

<!-- Avalonia -->
<Image Source="avares://MyApp/Assets/logo.png"/>
```

## Dialogs
```csharp
// WPF
MessageBox.Show("Hello");
var dialog = new OpenFileDialog();
dialog.ShowDialog();

// Avalonia
// Use StorageProvider for file dialogs (see avalonia-services skill)
// Use WindowNotificationManager for notifications
// For message dialogs: use a community library like MessageBox.Avalonia
// or implement a simple dialog Window
var result = await new ConfirmDialog("Are you sure?").ShowDialog<bool>(owner);
```

## Dispatcher
```csharp
// WPF
Dispatcher.Invoke(() => { /* UI update */ });

// Avalonia
await Dispatcher.UIThread.InvokeAsync(() => { /* UI update */ });
// or
Dispatcher.UIThread.Post(() => { /* fire-and-forget */ });
```

`Dispatcher.BeginInvoke()` maps to `UIThread.Post()`. `Dispatcher.CurrentDispatcher`, `Dispatcher.FromThread()`, `Dispatcher.Yield()`, and `DispatcherPriority` keep the same names. `DependencyObject.Dispatcher` becomes `AvaloniaObject.Dispatcher`.

## Bindings Compile by Default
WPF's `{Binding}` resolves paths by reflection at runtime. Avalonia 12 compiles bindings, so each one needs a starting type — normally an `x:DataType` directive on the enclosing scope (`Window`, `UserControl`, `DataTemplate`); the compiler infers it in a few template cases, such as an `ItemTemplate` from its items. Without a starting type the XAML compiler raises `Cannot parse a compiled binding without an explicit x:DataType directive` and **the build fails** — it does not quietly fall back to reflection. `{ReflectionBinding}` is the per-binding equivalent of WPF's `{Binding}`: it restores runtime reflection resolution and needs no `x:DataType`. Full topic: `avalonia-data-binding`.

## What Works Without Changes
- `INotifyPropertyChanged` implementations
- `ICommand` implementations
- `ObservableCollection<T>` usage
- `IValueConverter` / `IMultiValueConverter` implementations
- Data binding patterns (namespace and `RelativeSource` syntax adjustments — but bindings now also need a starting type; see **Bindings Compile by Default**)
- Most MVVM framework code (ReactiveUI, CommunityToolkit.Mvvm)
- `ItemsControl`, `ListBox` (similar APIs — but see the `Items` / `ItemsSource` note above)
- `DataGrid` (same API, but requires the separate package and theme registration)
- Grid, StackPanel, DockPanel layouts (same attached properties; add `Spacing`, prefer `Panel` for layering)

## Common Mistakes
Ordered by how quietly they fail — the first four compile and run but behave wrongly, which is why they cost the most to find.

- **Assuming `TemplateBinding` is TwoWay.** Avalonia's is OneWay only, so template edits never reach the source. Use `{Binding X, RelativeSource={RelativeSource TemplatedParent}, Mode=TwoWay}`.
- **Turning every `Style TargetType` into a `ControlTheme`.** Apply the decision rule above — only the implicit-default-look role maps to `ControlTheme`; setters matched by type/class/state stay as `Style` with a `Selector`.
- **Porting `RenderTransformOrigin` unchanged.** The default pivot differs (`Center` vs `TopLeft`), so transforms render differently. Set it explicitly to reproduce WPF.
- **Relying on WPF's `Visibility` three-state semantics.** Avalonia's `IsVisible` is a boolean — the XAML won't compile. `IsVisible="False"` covers `Collapsed`; for `Hidden`'s "invisible but still occupying space", use `Opacity="0"`.
- Assuming `{Binding}` still resolves by reflection — v12 compiles bindings, so one with no `x:DataType` in scope fails the build; `{ReflectionBinding}` restores the WPF behavior
- Using WPF Trigger syntax — silently ignored or compile error
- Using `pack://` URIs — assets not found
- Calling `MessageBox.Show()` — doesn't exist
- Using `FrameworkElement` as base class — use `Control`
- Assigning to `ItemsControl.Items` — read-only; use `ItemsSource`
- Adding `DataGrid` without registering its theme in `App.axaml` — renders unstyled or blank
- Reaching for `RoutedCommand` / `CommandBinding` — neither exists; use `ICommand`
- Reaching for `CollectionViewSource` / `ICollectionView` — no general equivalent; `DataGridCollectionView` serves `DataGrid` only and needs its own package
- Reading a `StyledProperty` from your own backing field — returns stale data; use `GetValue`
- Calling `SetValue` on a `DirectProperty` — throws; use `SetAndRaise`
