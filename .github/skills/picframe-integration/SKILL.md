---
name: picframe-integration
description: "Use when working on picadre integration with helgeerbe/picframe: photo uploads and filesystem watching, HEIC/EXIF handling, MQTT/Home Assistant, configuration, startup, or debugging what the installed Picframe version supports."
---

# Picframe integration

Use this skill to investigate and change the boundary between this repository
(`picadre`) and the upstream `helgeerbe/picframe` application.

## Procedure

1. **Identify the Picframe version actually running on the frame.** Do not infer
   it from the latest upstream branch or from this repository's configuration.
   Inspect the service's `ExecStart` and its Python environment, then query that
   environment for `picframe.__file__`, `picframe.__version__`, and installed
   package metadata. If the Pi is unavailable, say so and distinguish verified
   local facts from upstream assumptions.
2. **Match upstream source to that version.** Check its Git tag/commit or
   installed package source. Read the relevant implementation and configuration
   schema; do not rely solely on old wiki pages, README summaries, or this
   skill's snapshots.
3. **Trace the integration boundary end to end.** For media, follow upload
   storage to the configured media directory and the corresponding watcher or
   indexer. For MQTT, verify the exact topic, payload shape, retain/QoS behavior,
   and `device_id` in the matching source. For configuration and startup, verify
   the actual service command, runtime config source, and environment.
4. **Implement against the installed generation.** Keep Picframe-specific
   assumptions isolated in the adapter. Do not silently switch a deployed
   installation from legacy YAML/HTTP/MQTT to a different upstream generation.
5. **Validate the behavior at the integration boundary.** Prefer a focused
   test with the real service/package when available. Otherwise test the
   adapter's request/topic construction and state explicitly what was simulated.
6. **Update this reference** if verified upstream behavior changes materially.
   Keep upstream-specific facts tagged with the branch/commit and observation
   date; never present them as universal behavior across Picframe versions.

## Reference

See [Picframe architecture and integration notes](./references/picframe-map.md)
for the upstream generations inspected, their media/config/MQTT boundaries,
and source links.
