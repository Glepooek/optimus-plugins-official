---
type: llm
weight: 1
---

The response must reject using Parcel CLI without the required license and choose the manual `dpkg-deb` route. It must publish for `linux-arm64` and set Debian `Architecture: arm64`; describe a package layout containing `DEBIAN/control`, `/usr/bin/field-console`, `/usr/lib/field-console`, and a `.desktop` entry plus icon; use an `exec` wrapper that passes arguments; and explain that Avalonia dependencies and target-distribution .NET native runtime dependencies must be verified rather than copied from a stale list. It must require `dpkg-deb` metadata/content inspection, clean Debian 12 installation, application launch, and uninstall validation. It must not state that self-contained publishing removes all native OS dependencies.