# Planning

This document captures the proposed architectural direction for migrating the
project from Python to Go.

## Direction

The Go version should be built around goroutines and channels instead of the
current Python callback/thread/asyncio mix. The preferred first version should
be a single Go binary with multiple goroutines, not multiple OS processes,
unless deployment later proves that separate binaries are needed.

The current preferred audio input direction is to use JACK Audio Connection Kit.
The Go service would run as a JACK client, receive raw audio buffers from JACK,
extract audio features, and pass those features through the rest of the system.

## Proposed Runtime Shape

```text
JACK audio input
      |
      v
Audio Capture / DSP goroutine
raw samples -> FFT/Mel bands -> AudioFrame
      |
      v
Render Engine goroutine
owns effects, state, brightness, packet id
      |
      +------------------> UDP output channel -> ESP32 sender goroutine
      |
      +------------------> WebSocket channel -> browser broadcaster goroutine
      |
      +------------------> band/metrics channel -> browser bands broadcaster

HTTP API handlers
      |
      v
Control channel -> Render Engine
```

## Components

### 1. Config Loader

Loads runtime configuration, validates values, and provides typed config to the
rest of the system.

Recommended first approach:

- file-based config, likely YAML or TOML
- environment variable overrides for deployment
- explicit validation at startup

Example config areas:

- server host/port
- JACK client name and connection behavior
- audio/DSP parameters
- UDP ESP32 target
- effect persistence file
- default effect list

### 2. JACK Audio Client

Connects to JACK and receives raw audio buffers.

Responsibilities:

- register Go service as a JACK client
- receive mono or selected input audio
- handle JACK buffer callbacks
- publish raw samples or pass them directly to DSP
- expose connection errors through the supervisor/error channel

Open decisions:

- exact Go JACK library
- mono vs stereo handling
- auto-connect behavior
- whether sample rate should be read from JACK or enforced by config

### 3. DSP / Feature Extractor

Converts raw audio into audio features useful for effects.

Responsibilities:

- FFT
- Mel band calculation
- adaptive gain/smoothing
- volume/silence detection inputs
- beat and BPM detection, if practical

Suggested output:

```go
type AudioFrame struct {
    Bands        []uint8
    BeatDetected bool
    BPM          float64
    Volume       float64
    Timestamp    time.Time
}
```

Beat detection should probably live here rather than inside effects. Effects
should receive prepared audio features, not raw audio.

### 4. Render Engine

The render engine should be the only owner of mutable runtime state.

It should own:

- current power state
- brightness
- no-sound handling
- current effect list/index
- current primary and secondary effect
- active effect instances
- packet id
- pyramid buffers

Inputs:

- `AudioFrame` channel
- `ControlCommand` channel from the API

Outputs:

- `LEDFrame` channel for UDP
- `LEDFrame` channel for WebSocket visualization
- band/metrics channel for browser charts

Suggested control command shape:

```go
type ControlCommand struct {
    Type  string
    Value any
    Reply chan ControlResult
}
```

The API should send commands to the render engine instead of mutating shared
state directly. This keeps the hot path free from scattered locks and avoids
race conditions.

### 5. UDP Sender

Waits for LED frames and sends them to the ESP32 over UDP.

Responsibilities:

- serialize section frames in the current ESP32 wire protocol
- send three section datagrams per frame
- drop stale frames when overloaded
- report send errors without crashing the whole application

The active wire protocol should remain compatible at first:

```text
byte 0      packet_id
byte 1      section_id: A=0, B=1, C=2
byte 2..N   RGB pixel bytes
```

### 6. WebSocket Broadcaster

Waits for LED frames and band data, then broadcasts to connected browser
clients.

Responsibilities:

- stream LED section frames to the 3D pyramid viewer
- stream band data to the band chart
- isolate slow clients
- drop stale frames rather than building backlog

The webpage should be kept compatible during the first migration step.

### 7. HTTP API

Serves the static webpage and accepts control commands.

Responsibilities:

- serve existing static UI
- expose compatible REST endpoints where practical
- send effect/state commands to the render engine
- return command results to clients
- expose health/status endpoints

The API should not own effect state directly.

### 8. Persistence

Loads and saves effect lists and possibly last selected runtime state.

First migration target:

- keep `memory.json` compatibility if possible
- preserve built-in `static` and `dynamic` lists
- preserve custom user lists

### 9. Supervisor / Lifecycle

Coordinates startup, shutdown, and component failures.

Responsibilities:

- root `context.Context`
- graceful shutdown on interrupt
- error channel from components
- health status
- restart or fail-fast policy for JACK/UDP/API errors

## Channel Design

Use bounded channels. This is important because the system is real-time; recent
frames are more valuable than old frames.

Suggested channel behavior:

- audio frame channel: size `1` or `2`, keep latest
- LED output channel: size `1` or `2`, keep latest
- API control channel: size around `32`
- WebSocket per-client channel: small, drop old frames or disconnect very slow
  clients

Avoid unbounded queues. If the renderer or browser falls behind, stale visual
frames should be dropped instead of accumulating latency.

## Suggested Data Models

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

type SectionFrame struct {
    SectionID uint8
    Payload   []byte
}

type LEDFrame struct {
    PacketID  uint8
    Sections  [3]SectionFrame
    CreatedAt time.Time
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

## Effect Interface

Suggested starting interface:

```go
type Effect interface {
    Name() string
    IsDynamic() bool
    Update(info AudioInfo)
    Commands() PyramidSimpleCommands
    Clear()
}
```

Prefer a registry/factory for effects instead of global singleton instances.
Effect state should belong to the active effect instance.

## Configuration Sketch

Example YAML shape:

```yaml
server:
  host: "0.0.0.0"
  port: 9876

jack:
  client_name: "pyledaudio-go"
  input_ports: 1
  auto_connect: true

audio:
  sample_rate: 48000
  display_frequency: 30
  min_frequency: 60
  max_frequency: 18000
  fft_bins: 8
  rolling_history: 2
  min_volume: 0.002

udp:
  host: "192.168.60.150"
  port: 12345

effects:
  memory_file: "memory.json"
  default_list: "static"
```

## Main Architectural Choices

- Use one Go binary with goroutines first.
- Use JACK instead of PyAudio for Linux audio input.
- Use channels between components.
- Make the render engine the owner of mutable runtime state.
- Keep API handlers thin; they send control commands.
- Use bounded channels and drop stale visual frames.
- Keep the existing UDP, REST, and WebSocket protocols compatible at first.
- Add lifecycle/error handling from the beginning.
- Keep the static webpage usable during the migration.

## Open Questions

- Which Go JACK binding should be used?
- Should beat detection be ported from aubio, replaced with another library, or
  implemented in-house?
- Should audio DSP and rendering run at separate rates?
- Should the Go version preserve every current REST endpoint exactly, or only
  the endpoints used by the webpage?
- Should effect list persistence remain `memory.json` permanently or only
  during transition?
- Should LED byte order remain named RGB, or should it be verified against ESP32
  firmware before locking the protocol?
