---
type: llm
weight: 1
---

The review must remain limited to `Views/SearchView.axaml` and clearly identify the WPF presentation namespace as an Avalonia build blocker, the use of `Style.Triggers` / `Trigger` as an invalid WPF pattern, and the absence of an `x:DataType` for compiled bindings as a potential build blocker under the project’s compiled-binding configuration. It must distinguish confirmed findings from the configuration-dependent binding finding, cite the specific official Avalonia Docs MCP material or API it queried, provide a minimal corrected AXAML example, and avoid inventing unrelated findings or claiming that the project was built.
