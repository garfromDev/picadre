# Picframe architecture and integration notes

This is a navigation aid, not a replacement for the installed version's source.
Upstream was inspected on 2026-10-15. The observations below are pinned to the
listed commits so that branch movement does not silently change their meaning.

## Two materially different upstream generations

| Upstream ref inspected | Architecture | Integration consequence |
| --- | --- | --- |
| [`main` at `180368c9`](https://github.com/helgeerbe/picframe/tree/180368c9fb1d8b28fd6a3e548043177b009694ff) | Legacy pi3d application. Source includes `controller.py`, `model.py`, `interface_mqtt.py`, `interface_http.py`, and `start.py`. Configuration is YAML. | This is the generation whose MQTT image-attributes topic matches the current picadre integration. |
| [`dev` at `ccb7d36b`](https://github.com/helgeerbe/picframe/tree/ccb7d36b231a5f2936bd93d8580277955d329507) | Next-generation CLI, SQLite settings/cache, FastAPI/Vue control plane, event bus, pi3d renderer and GStreamer video worker. | Do not apply its API, runtime paths, configuration storage, or MQTT topics to a frame until its installed version is confirmed to use this generation. |

The upstream README and runtime evolve. Recheck the current upstream source and
the actual installed package whenever behavior matters; this snapshot is not a
compatibility guarantee.

## Verified deployment for this project

Verified over SSH to `cadrephoto` on 2026-10-15:

- SSH target: `picadre@cadrephoto` (`ssh picadre@cadrephoto`).
- Raspberry Pi 2 Model B Rev 1.1, revision `a01041`.
- Raspbian GNU/Linux 12 (bookworm).
- Installed distribution `picframe` version `2026.4.22`, loaded from
  `/home/picadre/venv_picframe/lib/python3.11/site-packages/picframe`.
- Active process uses `/home/picadre/venv_picframe/bin/python3`.
- Legacy config at `/home/picadre/picframe_data/config/configuration.yaml`
  points `model.pic_dir` to `/home/picadre/Pictures` and `model.db_file` to
  `/home/picadre/picframe_data/data/pictureframe.db3`.
- That config currently has both `mqtt.use_mqtt: False` and `http.use_http:
  False`. No Mosquitto broker, `mosquitto_pub`, or `mosquitto_sub` is installed.

The upstream repository did not resolve refs named `2026.4.22` or
`v2026.4.22` when checked. For version-specific behavior, prefer the installed
source on the Pi over guessed upstream tags.

Use the SSH target above for future checks when reachable. Keep commands
read-only by default; only modify the Raspberry Pi when the user explicitly
asks for the specific operation. Never store SSH passwords, private keys, or
other credentials in this repository.

### Installed legacy cache cleanup behavior (verified)

In the installed `picframe/image_cache.py`, missing files are only deleted
from the `file` table when the internal `purge_files` flag is set. The
`purge_files()` action sets that flag; the cache loop then removes records for
paths that no longer exist. A regular restart / scan does **not** delete
missing file rows; model playback can warn on a missing path and skip it.
The installed legacy MQTT adapter is the route that exposes this action, and
it subscribes to `<device_id>/purge_files`. With MQTT disabled and no broker
installed, this is not currently a usable cleanup route. HTTP is also disabled
in the active config, and no purge/reload route was found in the legacy HTTP
interface.

The on-device cache database was inspected read-only on 2026-10-15: the
`file` table had 912 rows, 107 of whose paths were absent from disk at that
time. The installed schema has a delete trigger from `file` to `meta`, so a
careful offline cleanup of only nonexistent paths can remove associated
metadata too. Before any database cleanup, stop Picframe, back up the database,
and scope deletion strictly to rows whose `fname` path is absent. Never edit
the live SQLite database or delete/rebuild it as a shortcut.

## Media ingestion and filesystem boundary

Picframe's normal media flow is filesystem-based: photos/videos live in the
configured media directory, and Picframe discovers and indexes files there.
The next-generation README documents `~/Pictures` as the default directory.
Its composition root (`src/picframe/main.py`) reads `model.pic_dir`, combines
configured image/video extensions, and constructs a watchdog media monitor.
Its default image extensions include `.heic` and `.heif`; extension acceptance
does not by itself guarantee that a particular machine's installed decoder can
decode every file.

The legacy configuration used by this `picadre` repository points
`model.pic_dir` at `/home/picadre/Pictures`; the upload service writes photos
to that same directory. Confirm both paths on the running host before changing
either. No direct file-upload API should be assumed: inspect the matching
version's API routes and docs before designing around one.

For HEIC/HEIF, distinguish these independent steps:

1. browser selection and client-side decode/conversion;
2. server upload and filename/extension;
3. media watcher/indexing of the saved file;
4. image decoder availability in the installed Picframe environment.

Success at one step does not prove the others. Test real device files and the
target browser/decoder when possible.

## Configuration, runtime, and APIs

### Legacy `main` snapshot

- Runtime settings are in `configuration.yaml`, including `model.pic_dir`,
  `model.db_file`, `mqtt.*`, and `http.*`.
- `src/picframe/interface_mqtt.py` provides Home Assistant discovery and
  publishes the current image and its attributes.
- This is the model used by the current picadre YAML and MQTT integration.

### Next-generation `dev` snapshot

- Public startup commands are `picframe init` and `picframe run`.
- Default runtime data is under `~/.picframe/data/`, including `config.db3`
  and `media_cache.db3`; the Vue app is under `~/.picframe/html/`.
- Settings are persisted to SQLite, with legacy YAML import performed
  explicitly through the Settings UI.
- The web control plane defaults to port `9000`; REST/OpenAPI docs are at
  `/docs`, and live playback state uses `/ws/state`.
- The README describes copying media into `~/Pictures` (or changing
  `model.pic_dir`) and having the media monitor/indexer discover it.
- In this branch, `src/picframe/main.py` is the composition root. The main
  components include the `core` services/event bus, `api`, and
  `infrastructure` adapters. Check implementation and current docs before
  extending any of these contracts.
- The manual notes that `config.db3` stores settings and `media_cache.db3`
  is rebuildable media metadata/playback state; never delete either as a
  speculative fix. Back up and follow the version-matched maintenance path.

## MQTT / Home Assistant compatibility

The topics below are **not interchangeable**.

### Legacy `main` topic observed

The legacy adapter builds the image-attributes topic as:

```text
homeassistant/sensor/<device_id>_image/attributes
```

and the current-image state topic as:

```text
homeassistant/sensor/<device_id>_image/state
```

The attributes payload is JSON. The image-state payload is also JSON and
contains the image filename. The configured `model.image_attr` list controls
the requested attributes; the legacy example includes EXIF/IPTC keys and the
special `PICFRAME GPS` and `PICFRAME LOCATION` entries.

The current picadre `upload_server.py` MQTT reader targets the first of these
topics, and the repository's README example uses the default `device_id` of
`picframe`. Preserve this legacy contract unless the installed Picframe source
proves otherwise.

### Next-generation `dev` topics observed

The next-generation adapter (`src/picframe/infrastructure/mqtt/home_assistant.py`)
uses a base topic `picframe/<device_id>`, with current-media JSON attributes on:

```text
picframe/<device_id>/media/attributes
```

and a compact current-media state on:

```text
picframe/<device_id>/media/state
```

The dev manual says the current-media sensor state is compact (including
`filename` and `layout`) while normalized media metadata is on
`media/attributes`. This is a different contract from the legacy
`homeassistant/sensor/<device_id>_image/attributes` topic. Check the precise
adapter code before consuming additional fields.

## Repository-specific places to inspect

- `upload_server.py`: filesystem destination, MQTT reader, and web/API boundary.
- `configuration.yaml`: legacy `model.pic_dir`, database path, MQTT
  configuration, and image metadata fields.
- `upload_server.service`: Python environment and process used by the uploader.
- `README.md`: existing operational commands and broker/topic examples.
- On the Pi, inspect the active Picframe unit as well; the uploader's service
  does not prove which Picframe package or service is running.

## Version-matching checklist for the Pi

On the device, start with the active service and actual interpreter; adapt
paths to the unit file rather than assuming them:

```sh
systemctl --user cat upload_server.service
systemctl status picframe.service
```

Use the Python interpreter from Picframe's `ExecStart`/virtual environment:

```sh
/path/to/picframe-venv/bin/python -c \
  'import picframe; print(picframe.__file__); print(getattr(picframe, "__version__", "unknown"))'
/path/to/picframe-venv/bin/python -m pip show picframe
```

Then compare the installed source paths and version with the pinned upstream
generation above. A service may use a different virtual environment than the
uploader, and an import/version check from the wrong interpreter is not
evidence about the running Picframe process.

## Upstream source map

Pinned links for the inspected `dev` generation:

- [README: runtime, media directory, API, and MQTT overview](https://github.com/helgeerbe/picframe/blob/ccb7d36b231a5f2936bd93d8580277955d329507/README.md)
- [Composition root and media monitor wiring](https://github.com/helgeerbe/picframe/blob/ccb7d36b231a5f2936bd93d8580277955d329507/src/picframe/main.py)
- [Home Assistant MQTT adapter](https://github.com/helgeerbe/picframe/blob/ccb7d36b231a5f2936bd93d8580277955d329507/src/picframe/infrastructure/mqtt/home_assistant.py)
- [Default config seed](https://github.com/helgeerbe/picframe/blob/ccb7d36b231a5f2936bd93d8580277955d329507/src/picframe/config/default_config.yaml)
- [User manual](https://github.com/helgeerbe/picframe/blob/ccb7d36b231a5f2936bd93d8580277955d329507/docs/user/manual.md)
- [Architecture overview](https://github.com/helgeerbe/picframe/blob/ccb7d36b231a5f2936bd93d8580277955d329507/docs/dev/architecture/overview.md)

Pinned links for the inspected legacy `main` generation:

- [Legacy MQTT adapter](https://github.com/helgeerbe/picframe/blob/180368c9fb1d8b28fd6a3e548043177b009694ff/src/picframe/interface_mqtt.py)
- [Legacy example configuration](https://github.com/helgeerbe/picframe/blob/180368c9fb1d8b28fd6a3e548043177b009694ff/src/picframe/config/configuration_example.yaml)
