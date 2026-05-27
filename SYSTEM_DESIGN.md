# System Design

This document describes the current Python system starting from `main.py`.
It is written as a technical baseline for a later migration from Python to Go.

## Purpose

`pyledaudio` is a real-time audio-reactive LED controller for a three-section
digital pyramid. It captures microphone audio, converts it into frequency band
levels and beat metadata, renders LED effects into section pixel buffers, sends
the buffers to an ESP32 over UDP, and exposes a FastAPI web UI for control and
visual monitoring.

## Runtime Entry Point

The application starts in `main.py`.

Startup sequence:

1. Print available PyAudio input devices.
2. Read uppercase values from root `config.py`.
3. Push the root configuration into `audio.config`, `api.config`, and
   `effects.config`.
4. Initialize the audio processor with `display_effects` as the render callback.
5. Register an effect-change callback on the global effect manager.
6. Start the FastAPI/Uvicorn server in a daemon thread.
7. Start the PyAudio input stream.
8. Keep the main thread alive until `KeyboardInterrupt`.

Shutdown sequence:

1. Stop the PyAudio stream.
2. Terminate the PyAudio instance.

The main process depends heavily on module-level singletons:

- `audio.process.audioProcessor`
- `effects.effects_manager.effect_manager`
- `state.state_manager`
- queues in `api.broadcasters`
- `effects.utils.cmd_off`

## Top-Level Architecture

```text
                 HTTP/WS clients
                      |
                      v
              FastAPI / static UI
                      |
      REST mutates state/effects, WS streams telemetry
                      |
                      v
Microphone -> AudioProcessor -> main.display_effects -> EffectManager
   |              |                    |                    |
   |              v                    v                    v
   |        band levels + beat    app state checks     DigitalPyramid
   |                                  brightness          pixel buffers
   |                                      |                    |
   +--------------------------------------+--------------------+
                                          |
                                          v
                                broadcaster queues
                                          |
                   +----------------------+----------------+
                   v                                       v
             WebSocket viewers                         UDP ESP32
```

## Configuration

Root `config.py` is the source of runtime configuration. `get_config_dict()`
collects uppercase globals and passes them to submodule config setters.

Important values:

- `UDP_IP`, `UDP_PORT`: ESP32 destination.
- `SERVER_IP`, `SERVER_PORT`: FastAPI/Uvicorn bind address.
- `MIC_RATE`, `MIC_DEVICE_INDEX`: microphone stream configuration.
- `MIN_FREQUENCY`, `MAX_FREQUENCY`: audio band frequency range.
- `SAMPLING_FREQUENCY`: audio callback sampling cadence.
- `DISPLAY_FREQUENCY`: LED/UI output cadence.
- `MAX_VOLUME`: current silence threshold. Audio below this returns no bands.
- `N_FFT_BINS`: number of visualization bands.
- `N_ROLLING_HISTORY`: number of audio chunks in the rolling FFT window.

Submodule defaults exist in `audio/config.py`, `api/config.py`,
`effects/config.py`, and `udp/config.py`, but the active application uses the
root config values for audio, API, and effects. The standalone `udp/client.py`
has its own config path and is not used by `main.py`.

## Audio Pipeline

Main files:

- `audio/process.py`
- `audio/dsp.py`
- `audio/melbank.py`
- `audio/config.py`

`AudioProcessor.setup(callback)` initializes:

- the Mel filter bank via `dsp.create_mel_bank()`
- exponential filters for gain and smoothing
- PyAudio `frames_per_buffer`
- a rolling audio history buffer
- a Hamming FFT window
- aubio beat/tempo detection
- the display callback divider

PyAudio calls `_pyaudio_callback(in_data, frame_count, time_info, status)`.
That callback:

1. Converts int16 microphone bytes into NumPy arrays.
2. Converts audio to float samples for aubio.
3. Updates beat detection and BPM.
4. Runs LED rendering only every `SAMPLING_FREQUENCY / DISPLAY_FREQUENCY`
   audio callbacks.
5. Calls `create_band_levels`.
6. Calls the registered callback, currently `main.display_effects`, with
   `AudioInfo`.

`create_band_levels`:

1. Normalizes int16 audio to float.
2. Rolls the latest chunk into `y_roll`.
3. Computes RMS volume.
4. Returns `None` when volume is below `MAX_VOLUME`.
5. Applies the Hamming window.
6. Pads the signal to the next power-of-two length.
7. Runs real FFT.
8. Multiplies the spectrum by the Mel filter bank.
9. Squares band powers.
10. Applies adaptive gain and smoothing.
11. Clips values to `0..1`.
12. Returns one byte per band, scaled to `0..255`.

Go migration notes:

- Replace PyAudio with a Go audio input library such as PortAudio bindings or a
  platform-specific ALSA/PulseAudio input implementation.
- Replace NumPy/SciPy operations with explicit slices and a Go FFT/DSP library.
- The Mel filter bank algorithm is simple enough to port directly.
- aubio tempo detection has no direct standard-library equivalent. Decide
  whether to bind aubio, use another Go DSP package, or implement a simpler
  onset detector.

## Main Render Loop

`main.display_effects(audio_info)` is the central render function. It is called
from the PyAudio callback path.

Behavior:

1. Count frames once per second.
2. If power is off:
   - when `power_changed` is true, send black/off commands once
   - skip rendering
3. If `audio_info.bands` is `None`:
   - increment `no_sound_cntr`
   - after roughly one second of no sound, send black/off commands and stop
     rendering until sound returns
4. Send band bytes to the bands queue for the UI.
5. Update the primary effect.
6. Optionally update a secondary effect.
7. If two effects are active, combine their pyramid buffers.
8. Increment the packet id.
9. Apply global brightness by fading all pixels.
10. Serialize sections A, B, and C to bytes.
11. Send the three section frames to the LED queue.

The packet id is one byte and wraps from `254` to `0`.

## State Management

Main file:

- `state.py`

`StateManager` wraps a Pydantic `State` object. Current state fields:

- `power`
- `brightness`
- `effect`
- `power_changed`
- `no_sound_cntr`
- `no_sound`

The REST API updates `power` and `brightness`. The render loop reads those
values directly. There is no lock around this shared mutable state.

Go migration notes:

- Model this as an application state struct.
- Protect state with `sync.RWMutex`, channels, or a single owner goroutine.
- Consider replacing `power_changed` with an event/message so edge-triggered
  behavior is explicit.

## Effects System

Main files:

- `effects/effects_manager.py`
- `effects/list_manager.py`
- `effects/utils.py`
- `effects/static/*.py`
- `effects/dynamic/*.py`
- `memory.json`

### Effect Manager

`EffectManager` eagerly constructs all effects as singleton objects at import
time, stores them by name, and divides them into static and dynamic names.

Dynamic effects:

- `SpectrumOctagon`
- `SpectrumTriangles`
- `SpectrumTwoLines`
- `BeatBlast`
- `BeatOctagon`
- `VuTwoLines`
- `VuTwoLinesTop`

Static effects:

- `BottomTriangles`
- `SideTriangles`
- `BodyTriangles`
- `Snake`
- `BigSnake`

The manager tracks:

- current effect list
- current effect pair
- current index
- current primary effect
- optional current secondary effect

Effect switching clears the previously active effect pyramids.

### Effect Lists

`ListsManager` loads and saves effect lists through `MemoryManager`.
The persistence file is `memory.json`.

On startup:

1. Load existing lists from `memory.json`.
2. Ensure built-in `static` and `dynamic` lists exist.
3. Merge missing built-in effects into existing built-in lists.

Custom lists can be created, removed, and modified through the REST API.
Built-in `static` and `dynamic` lists are protected from user modification.

### Effect Interface

All effects inherit from `effects.utils.Effect`.

Expected methods:

- `update(audio_info=None)`: mutate the effect's `DigitalPyramid`.
- `get_commands()`: return `PyramidSimpleCommands`.
- `clear()`: inherited; clears the pyramid state.

Static effects ignore audio and use timers, particles, or index counters.
Dynamic effects use band intensities and/or beat metadata.

Go migration notes:

- Define an `Effect` interface:

```go
type Effect interface {
    Name() string
    IsDynamic() bool
    Update(info AudioInfo)
    Commands() PyramidSimpleCommands
    Clear()
}
```

- Prefer constructing effects through a registry/factory rather than global
  singleton instances.
- Keep effect state per instance so previews, combinations, and tests can run
  independently.

## LED Domain Model

Main file:

- `effects/utils.py`

The physical model is a digital pyramid with three sections:

| Section | Meaning | Segments | LEDs per segment | Total LEDs |
| --- | --- | ---: | ---: | ---: |
| A | radial bottom lines | 8 | 30 | 240 |
| B | octagon sides | 8 | 22 | 176 |
| C | pyramid side edges | 8 | 60 | 480 |

Core types:

- `Pixel`: RGB-like color object with blend, intensity, fade, and bytes support.
- `PixelArray`: fixed-length pixel buffer.
- `PixelArrayView`: view into a section buffer, optionally flipped.
- `PixelGroup`: logical shape made from multiple views.
- `Particle`: moving colored point with lifetime, speed, fade, and optional hue shift.
- `ParticleLine`: line containing particles plus head/tail gates.
- `ParticleLineGroup`: group of particle lines.
- `DigitalPyramid`: owns sections, segment views, particle lines, logical groups,
  and section commands.

Logical groups precomputed by `DigitalPyramid`:

- `triangle_bottom_groups`
- `triangle_side_groups`
- `triangle_body_groups`
- `two_lines_body_groups`

`DigitalPyramid.connect_all_particle_lines()` wires line gates so particles can
move across the pyramid topology.

Go migration notes:

- Use byte-backed buffers for pixel arrays to reduce allocations.
- Preserve the current RGB byte order unless the ESP32 firmware expects a
  different order. The Python code names pixels as `r,g,b` and serializes them
  in that order.
- Be careful with view semantics. Python views write through to parent buffers;
  in Go this maps naturally to slices.

## LED Wire Protocol

The active runtime uses `SimpleCommand`, not the older `Command` type.

For each frame, three UDP datagrams are produced:

```text
byte 0      packet_id, uint8
byte 1      section_id, uint8: A=0, B=1, C=2
byte 2..N   pixel bytes, three bytes per LED
```

Payload sizes:

- Section A: `2 + 240 * 3 = 722` bytes
- Section B: `2 + 176 * 3 = 530` bytes
- Section C: `2 + 480 * 3 = 1442` bytes

The legacy `Command` type supports command type, section id, payload length,
segment ids, and command merging. It is currently not used by `main.py`.

Go migration notes:

- Implement the active `SimpleCommand` protocol first.
- Keep `packet_id` wrapping behavior compatible.
- If the ESP32 firmware supports only the simple protocol, remove the legacy
  command model during migration.

## API Server and Queues

Main files:

- `api/server.py`
- `api/endpoints.py`
- `api/broadcasters.py`
- `api/models.py`
- `api/mounts.py`
- `api/config.py`

`server.start()` creates a FastAPI app, mounts static files under `/ui`,
registers REST endpoints and WebSockets, starts background broadcaster tasks,
and runs Uvicorn in a daemon thread.

### REST Endpoints

Health and config:

- `GET /health`
- `GET /config`

State:

- `GET /state`
- `POST /state/power`
- `POST /state/brightness`

Effect lists:

- `GET /effect-list`
- `POST /effect-list`
- `GET /effect-list/{list_name}`
- `POST /effect-list/{list_name}`
- `DELETE /effect-list/{list_name}`
- `POST /effect-list/{list_name}/append`
- `DELETE /effect-list/{list_name}/remove`
- `GET /effect-list-names`

Current effect list:

- `GET /effect-list-current`
- `GET /effect-list-current/name`
- `GET /effect-list-current/pair`
- `GET /effect-list-current/index`
- `POST /effect-list-current/index`
- `POST /effect-list-current/next`
- `POST /effect-list-current/previous`

Preview:

- `POST /effect-pair/preview`

### WebSockets

- `/ws/bands`: sends JSON `{ "bands": [0..255, ...] }`
- `/ws/leds`: sends binary section frames in the same format as UDP

### Queue Flow

`main.py` writes to:

- `timer_bands_queue`
- `timer_leds_queue`

`timed_display_dispatch_loop` drains those queues at `DISPLAY_FREQUENCY`,
drops stale band values, dispatches section frames to:

- `bands_queue` for band WebSocket broadcasting
- `leds_queue` for LED WebSocket broadcasting
- `udp_send_queue` for UDP output

`udp_sender_loop` owns a nonblocking UDP socket and sends frames to
`api.config.UDP_IP:UDP_PORT`.

Go migration notes:

- Use goroutines for HTTP server, audio input, render loop, broadcaster, and UDP
  sender.
- Use typed channels instead of global asyncio queues.
- Separate UI telemetry from hardware output so visualization failures cannot
  block UDP sending.

## Web UI

Main files:

- `page/index.html`
- `page/api.js`
- `page/models.js`
- `page/logic.js`
- `page/controls.js`
- `page/bands.html`
- `page/pyramid.html`
- `page/style.css`
- bundled assets: fonts, logos, `chart.js`, `three.js`

`index.html` is the control surface. It embeds:

- `pyramid.html`: 3D pyramid viewer using Three.js and `/ws/leds`
- `bands.html`: bar chart using Chart.js and `/ws/bands`

The UI can:

- toggle power
- set brightness
- select primary and secondary effects for preview
- create/delete custom effect lists
- append/remove effect pairs
- move to previous/next effect pair

The Python server mounts `page` at `/ui`, so the UI entry URL is `/ui/`.

Go migration notes:

- The existing static files can be served unchanged from Go.
- REST and WebSocket payload compatibility should be maintained during the first
  migration step so the UI does not need to move at the same time.

## Standalone Hardware Test

`testhardware.py` is independent of `main.py`. It sends a moving single-pixel
test pattern directly to the ESP32 over UDP using the active simple protocol.
It is useful as a protocol smoke test.

## Dependencies

Core runtime dependencies:

- PyAudio: microphone input
- aubio: beat and BPM detection
- NumPy: arrays, FFT, byte conversion
- SciPy: Gaussian smoothing
- FastAPI/Starlette: HTTP and WebSocket app
- Uvicorn: ASGI server
- Pydantic: request and state/list models

Frontend libraries:

- Chart.js for band visualization
- Three.js for pyramid visualization

## Concurrency Model

Current Python runtime uses:

- main thread: startup and idle sleep loop
- PyAudio callback thread: audio processing and effect rendering
- Uvicorn daemon thread: event loop, HTTP, WebSockets, queues, UDP sender
- asyncio tasks inside the Uvicorn thread:
  - bands broadcaster
  - LED broadcaster
  - UDP sender
  - timed display dispatcher

Shared mutable objects are accessed from multiple threads without explicit
locking:

- `state_manager`
- `effect_manager`
- active effect instances and their `DigitalPyramid` buffers
- asyncio queues are written from the PyAudio callback thread

This works in the current Python implementation partly because of the GIL and
the low amount of shared mutation, but the Go version must make ownership and
synchronization explicit.

Recommended Go ownership model:

- Audio goroutine publishes `AudioInfo` messages.
- Render goroutine owns `EffectManager`, active effects, packet id, no-sound
  state, and brightness application.
- API handlers send commands to the render goroutine through a control channel.
- Broadcaster goroutine receives immutable frame copies.
- UDP goroutine receives immutable section frames.

## Data Models for Go

Suggested foundational structs:

```go
type AudioInfo struct {
    Bands        []byte
    BeatDetected bool
    BPM          float64
}

type Pixel struct {
    R uint8
    G uint8
    B uint8
}

type PyramidFrame struct {
    PacketID uint8
    A []byte
    B []byte
    C []byte
}

type EffectPair struct {
    Primary   string  `json:"primary"`
    Secondary *string `json:"secondary"`
}

type EffectList struct {
    Name           string       `json:"name"`
    SwitchInterval int          `json:"switch_interval"`
    Effects        []EffectPair `json:"effects"`
}

type AppState struct {
    Power      bool
    Brightness uint8
}
```

## Migration Strategy

Recommended order:

1. Freeze the current wire protocols and REST/WebSocket payloads.
2. Port passive data models: pixels, pixel arrays, views, groups, commands.
3. Port `DigitalPyramid` topology and add tests for section lengths and group
   mappings.
4. Port static effects and verify rendered byte frames against Python snapshots.
5. Port dynamic effects using recorded `AudioInfo` fixtures.
6. Port persistence for `memory.json`.
7. Implement the Go API server with compatible endpoints.
8. Implement UDP sender and WebSocket broadcasters.
9. Port audio processing.
10. Integrate hardware audio input and beat detection.
11. Run side-by-side frame comparisons before replacing the Python runtime.

Suggested tests before migration:

- `SimpleCommand` byte payload size and header values.
- Pixel blending, intensity, and fade.
- `PixelArrayView` flipped and non-flipped writes.
- `DigitalPyramid` section lengths and group lengths.
- Effect list load/save/merge behavior.
- REST endpoint compatibility.
- UDP test frame compatibility with ESP32 firmware.

## Known Implementation Notes and Risks

- `api.models.AddEffectListRequest.effects` is typed as `Optional[EffectPair]`,
  while endpoint code treats it like a list. The UI currently sends `null`, so
  this may not surface until creating lists with initial effects.
- `udp/client.py` and `udp/config.py` are not used by the main runtime.
  Runtime UDP sending is implemented in `api/broadcasters.py`.
- `Command` in `effects/utils.py` appears to be legacy or unused by `main.py`.
- `effects.utils.Colors.name_for` is defined without `@classmethod` or `self`;
  it is called as `colors.name_for(c)`, which works because the `colors`
  instance is passed as the first argument named `cls`.
- Some effect update calls pass `self.previous_time` into
  `pyramid.update(...)` instead of the current time. This is existing behavior
  and should be verified with visual tests before porting directly.
- `timer_leds_queue` and `timer_bands_queue` are asyncio queues written from a
  non-event-loop thread. A Go migration should replace this with explicit
  channels and ownership.
- `timed_display_dispatch_loop` sleeps for
  `interval - small_time * overflow_count`; if overflow is large this can become
  negative in Python. Guard this in a Go implementation.
- The code has no automated tests in the repo. Migration should start by adding
  characterization tests around payload generation and topology.

## File Map

```text
main.py                         startup, render callback, brightness, power handling
config.py                       root runtime configuration
state.py                        global mutable app state

audio/config.py                 audio runtime config copy
audio/process.py                PyAudio callback, aubio, band generation
audio/dsp.py                    FFT helpers and Mel bank setup
audio/melbank.py                Mel filter bank math

effects/config.py               effect config copy
effects/utils.py                LED domain model, commands, pyramid topology, base Effect
effects/effects_manager.py      effect registry and current selection
effects/list_manager.py         effect list persistence and mutation
effects/static/*.py             static effects
effects/dynamic/*.py            audio-reactive effects

api/config.py                   API/UDP config copy
api/server.py                   FastAPI/Uvicorn thread and async task startup
api/endpoints.py                REST endpoints
api/broadcasters.py             WebSockets, queues, UDP sending
api/models.py                   REST request models
api/mounts.py                   static UI mount

page/index.html                 UI shell
page/api.js                     browser REST client
page/models.js                  browser data models
page/logic.js                   UI behavior
page/controls.js                browser UI widgets
page/bands.html                 Chart.js band monitor
page/pyramid.html               Three.js LED frame viewer
page/style.css                  UI styling

memory.json                     persisted effect lists
testhardware.py                 standalone UDP hardware smoke test
requirements_pip*.txt           Python dependency lists
setupguideforpi.txt             Raspberry Pi setup notes
```
