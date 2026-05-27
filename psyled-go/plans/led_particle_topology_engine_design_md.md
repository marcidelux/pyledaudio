# LED Particle Topology Engine Design

## Goals

Design a high-performance LED simulation/rendering engine in Go with the following capabilities:

- Generic topology engine, not tied to a specific physical object such as the pyramid
- Multi-device model where each device can own one or more LED strips
- Physical LED strip abstraction
- Logical segments over strips
- Particle-based animation system
- Topology graph using hubs and endpoints
- Configurable routing rules
- YAML-defined topology and behaviors
- Real-time runtime performance
- Support for HSV/HSB animation workflows
- Efficient rendering to RGB LED hardware

Target runtime scale:

- ~100–500 particles per tick
- Real-time animation
- Minimal allocations
- Cache-friendly data structures

The current pyramid is only an example topology. The engine should be able to
describe other objects/devices later by changing YAML configuration, not by
changing core engine code.

---

# Architectural Layers

The system is divided into several layers.

```text
Device Layer
  Device -> output target, for example one ESP32 UDP endpoint

Physical Layer
  Strip -> physical RGB LED memory owned by a Device

View Layer
  Segment -> logical view into Strip

Topology Layer
  Ports + Hubs + Routing

Simulation Layer
  Particle system

Render Layer
  Draw particles/effects into strips

Output Layer
  Flush RGB buffers to hardware
```

The layers must remain separated.

Segments are not owners of topology.
Hubs own routing logic.
Particles move through topology.
Output transports are separated from topology and simulation.

---

# Core Concepts

## Device

A `Device` represents an output target.

In the first real deployment, a Device will usually be one ESP32
microcontroller reachable over UDP.

A Device:

- has a stable unique ID
- has output transport configuration
- owns one or more Strips
- receives rendered strip buffers from the server

A Device does NOT:

- own particle simulation
- own topology routing
- communicate directly with other devices

The server remains the central coordinator. If a particle crosses from a segment
on one device to a segment on another device, that transfer happens in the
server simulation. The server then renders and sends final LED buffers to both
devices.

## Strip

A `Strip` represents a physical LED device.

Responsibilities:

- Own RGB pixel buffer
- Belong to one Device
- Have a stable unique StripID
- Hardware flushing/output
- Brightness control
- Low-level pixel operations

A Strip contains no animation logic.

## Segment

A `Segment` is a logical view into a Strip.

A Segment:

- references a Strip
- maps local indexes to physical indexes
- may be reversed
- behaves like an independent virtual strip

A Segment does NOT:

- own topology
- know hubs
- know routing
- manage particles

## Endpoint

Each Segment has two logical endpoints:

```text
head = local index 0 side
tail = local index Len-1 side
```

Endpoints are topology connection points.

## Port

A Port represents:

```text
(segment + endpoint)
```

Examples:

```text
segment_a.head
segment_a.tail
```

Ports are used by topology routing.

## Hub

A Hub is a routing object.

Responsibilities:

- connect ports
- route particles
- modify particles during transfer
- duplicate/drop/bounce particles

A Hub owns routing logic.
Segments do NOT own Hub references.

## Particle

A Particle is a simulation object.

A Particle:

- exists inside a Segment
- has position and velocity
- has lifetime
- has color
- may have custom behavior

Particles move through topology.

---

# Ownership Model

Recommended ownership direction:

```text
Device
  └── Strip
        └── Segment views

Topology
  └── Hubs reference Segment endpoints
```

Do NOT:

```text
Segment -> Hub pointers
```

Reasons:

- cleaner separation
- easier YAML loading
- easier topology editing
- avoids circular dependencies
- simpler testing
- more flexible routing systems

---

# Runtime IDs

Use compact numeric IDs during runtime.

Do NOT use:

- strings
- maps
- reflection
- interface dispatch

inside hot loops.

Recommended:

```go
type DeviceID uint16
type StripID uint16
type SegmentID uint16
type PortID uint16
type HubID uint16
type BehaviorID uint16
```

YAML names are only used during initialization.

---

# Strip Design

## Responsibilities

- physical RGB buffer
- output to hardware
- low-level pixel operations

## Suggested Runtime Structure

```go
type DeviceRuntime struct {
    ID DeviceID

    Transport TransportID
    StripOffset uint16
    StripCount  uint16
}
```

```go
type Strip struct {
    Device DeviceID
    Pixels []RGB
}
```

## Suggested Methods

```go
Len() int
Clear()
Fill(color RGB)
Set(index int, color RGB)
Get(index int) RGB
Blend(index int, color RGB, mode BlendMode)
Fade(amount float32)
Flush() error
```

Optional:

```go
SetBrightness(float32)
CopyPixels() []RGB
```

---

# Segment Design

## Responsibilities

- map local indexes to physical indexes
- support reversed logical direction
- provide virtual strip abstraction

## Suggested Runtime Structure

```go
type SegmentRuntime struct {
    StripID  StripID

    Start    uint16
    Length   uint16

    Reversed bool

    HeadPort PortID
    TailPort PortID
}
```

## Local Coordinate System

```text
valid coordinate range:
[0, Length)
```

Examples:

```text
Length = 10

Valid:
0.0 -> 9.999

head exit:
Pos < 0

tail exit:
Pos >= 10
```

## Reversed Segments

Example:

```yaml
segments:
  seg_a:
    strip: main
    start: 20
    length: 10
    reversed: true
```

Mapping:

```text
local 0 -> physical 29
local 9 -> physical 20
```

Topology remains logical.
Reversal only affects physical LED mapping.

## Suggested Methods

```go
Len() int
Contains(pos float32) bool

Set(localIndex int, color RGB)
Get(localIndex int) RGB
Blend(localIndex int, color RGB, mode BlendMode)

Fill(color RGB)
Clear()

PhysicalIndex(localIndex int) int
```

---

# Endpoint Semantics

Use consistent logical semantics:

```text
head = local index 0 side
tail = local index Length side
```

Physical strip orientation is irrelevant.

Particles moving:

```text
Vel > 0 -> moving toward tail
Vel < 0 -> moving toward head
```

---

# Particle Design

## Responsibilities

Particles are simulation entities.

A particle:

- belongs to a Segment
- moves over local coordinates
- owns motion state
- owns color state
- owns lifetime state
- may own custom user data

## Suggested Runtime Structure

```go
type Particle struct {
    Segment SegmentID

    Pos float32
    Vel float32

    LifeRemaining float32
    LifeInitial   float32

    Color HSV

    Behavior BehaviorID

    User0 float32
    User1 float32
}
```

## Lifetime

Each tick:

```text
LifeRemaining -= dt
```

Particle dies when:

```text
LifeRemaining <= 0
```

Useful normalized lifetime:

```text
normalizedAge = 1.0 - LifeRemaining / LifeInitial
```

Useful for:

- fade-out
- easing
- pulsing
- color transitions

## Position Rules

Example:

```text
segment length = 10

Pos = 3.5
```

Particle is located between LED 3 and LED 4.

Exits:

```text
Pos < 0      -> exited through head
Pos >= Len   -> exited through tail
```

## Velocity

Velocity direction defines orientation.

Do NOT store separate orientation fields.

```text
Vel > 0 -> tail direction
Vel < 0 -> head direction
```

---

# Color Model

Use HSV/HSB internally for animation.

Advantages:

- hue cycling
- rainbow effects
- saturation modulation
- brightness control
- easier procedural animation

## Suggested HSV Structure

```go
type HSV struct {
    H float32
    S float32
    V float32
    A float32
}
```

Ranges:

```text
H = 0..360 or 0..1
S = 0..1
V = 0..1
A = 0..1
```

## Rendering Pipeline

Recommended:

```text
Particles/effects use HSV
        ↓
Renderer converts HSV -> RGB
        ↓
RGB buffer blended into Strip.Pixels
        ↓
Hardware output
```

## Blending

Blend in RGB space.

Avoid blending directly in HSV.

---

# Topology Design

## Ports

A Port is:

```text
Segment + Endpoint
```

Runtime:

```go
type PortRuntime struct {
    Segment  SegmentID
    Endpoint Endpoint
}
```

---

# Hub Routing

## Core Principle

Do NOT perform runtime graph traversal using strings/maps.

Compile YAML topology into flat routing tables.

## Runtime Routing Model

```text
Particle exits Segment
        ↓
Determine exit PortID
        ↓
Lookup routes for PortID
        ↓
Generate zero/one/many output particles
```

## Compiled Topology

```go
type CompiledTopology struct {
    Segments []SegmentRuntime
    Ports    []PortRuntime

    RoutesOffset []uint16
    RoutesCount  []uint8

    RouteOutputs []RouteOutput
}
```

Runtime route lookup:

```text
outputs = RouteOutputs[
    RoutesOffset[port] :
    RoutesOffset[port] + RoutesCount[port]
]
```

Advantages:

- cache-friendly
- allocation-free
- branch-light
- fast lookup

---

# Route Outputs

## Suggested Runtime Structure

```go
type RouteOutput struct {
    ToPort PortID

    Mode RouteMode

    SpeedScale float32
    LifeScale  float32

    HueAdd  float32
    SatScale float32
    ValScale float32
}
```

---

# Particle Transfer Rules

## Overflow Preservation

Example:

```text
Segment length = 10
Particle Pos = 10.25
```

Overflow:

```text
overflow = 0.25
```

## Entering Head

```text
new Pos = overflow
new Vel = +abs(old Vel)
```

## Entering Tail

```text
new Pos = Length - overflow
new Vel = -abs(old Vel)
```

This preserves continuous motion.

---

# Hub Behaviors

Recommended initial route modes:

```text
pass
split
bounce
random
drop
```

## pass

One input -> one output.

## split

One input -> multiple outputs.

Duplicates particles.

## random

Choose output based on weights.

## bounce

Reverse velocity.

## drop

Destroy particle.

Possible future additions:

```text
transform
gate
mix
mirror
switch
```

For v1, hubs are fixed/stateless routing definitions. A hub name is mainly a
YAML grouping and readability tool; runtime simulation can compile routes down
to `from PortID -> RouteOutput list`.

Avoid in v1:

- round-robin hubs
- cooldown hubs
- beat-gated hubs
- API-controlled switch hubs
- hub-local counters/state

Future versions may add stateful hub behavior by introducing `HubID` and
compiled hub state tables, but the first engine should keep hubs as fixed route
containers.

---

# Random Routing

Precompute weight thresholds.

Example:

```text
0.7
1.0
```

Runtime:

```text
r = random(0..1)
pick first threshold >= r
```

Avoid runtime normalization.

---

# Simulation Pipeline

Recommended tick order:

```text
1. Clear render buffers
2. Update particles
3. Remove dead particles
4. Route exited particles
5. Render particles into strips
6. Flush strips to hardware
```

---

# Particle Buffer Strategy

Avoid heap allocations.

Use double-buffered particle arrays.

## Suggested Structure

```go
currentParticles []Particle
nextParticles    []Particle
```

## Tick Flow

```text
nextParticles = nextParticles[:0]

for each particle:
    update

    if dead:
        continue

    if still inside segment:
        append to nextParticles

    else:
        route particle
        append resulting particles

swap(currentParticles, nextParticles)
```

Advantages:

- allocation-free
- predictable memory
- cache-friendly
- easy particle splitting

---

# Behavior System

Avoid interface dispatch inside hot loops.

Do NOT:

```go
type Behavior interface {
    Update(...)
}
```

inside the particle update loop.

Preferred:

```go
switch particle.Behavior {
case BehaviorSpark:
case BehaviorWave:
case BehaviorFire:
}
```

or:

- precompiled behavior tables
- function arrays indexed by BehaviorID

Interfaces are acceptable during initialization/config loading.

---

# YAML Design

## Goals

YAML should:

- be human-editable
- describe physical layout
- describe logical segments
- describe topology routing
- avoid redundant information

---

# YAML Example

```yaml
devices:
  esp32_a:
    type: esp32_udp
    address: "192.168.60.151"
    port: 12345

  esp32_b:
    type: esp32_udp
    address: "192.168.60.152"
    port: 12345

strips:
  main:
    device: esp32_a
    length: 60
    driver: ws2812
    color_order: grb

  secondary:
    device: esp32_b
    length: 60
    driver: ws2812
    color_order: grb

segments:
  a:
    strip: main
    start: 0
    length: 10
    reversed: false

  b:
    strip: main
    start: 10
    length: 10
    reversed: false

  c:
    strip: main
    start: 20
    length: 10
    reversed: true

  remote_a:
    strip: secondary
    start: 0
    length: 10
    reversed: false

hubs:
  hub_1:
    routes:
      - from: a.tail
        mode: pass
        outputs:
          - to: b.head

      - from: b.tail
        mode: split
        outputs:
          - to: c.head
          - to: a.head

      - from: c.tail
        mode: random
        outputs:
          - to: a.head
            weight: 0.7

          - to: b.head
            weight: 0.3

      - from: a.head
        mode: bounce

      # Cross-device routing is allowed because topology connects ports, not
      # physical transports. The server simulates the particle transfer and
      # later sends final strip buffers to each ESP32.
      - from: c.head
        mode: pass
        outputs:
          - to: remote_a.tail
```

---

# Route Transformations

Routes may modify particles.

Example:

```yaml
      - from: a.tail
        mode: pass
        outputs:
          - to: b.head
            speed_scale: 1.0
            life_scale: 0.9
            hue_add: 30
            sat_scale: 1.0
            val_scale: 0.8
```

---

# YAML Compilation Process

Recommended startup pipeline:

```text
1. Parse YAML
2. Validate names/references
3. Assign numeric IDs
4. Build ports
5. Build routing tables
6. Precompute route offsets
7. Create runtime arrays
```

After compilation:

- no strings in runtime hot paths
- no maps in simulation loops
- no reflection

---

# Rendering

Rendering is separate from simulation.

Simulation updates particles.
Rendering converts particles into RGB pixels.

## Recommended Rendering Flow

```text
Particle
    ↓
HSV -> RGB conversion
    ↓
Blend into Strip RGB buffer
    ↓
Flush to hardware
```

Possible blending modes:

```text
additive
alpha
max
replace
multiply
```

## Particle Render Modes

Particles use float positions. The renderer decides how to convert a float
position into LED pixels.

Initial render modes:

```text
nearest
linear
```

## nearest

Discrete LED rendering.

Example:

```text
Pos 3.2 -> LED 3
Pos 3.7 -> LED 4
```

## linear

Smooth sub-pixel rendering.

Example:

```text
Pos 3.2 -> LED 3 receives 80%, LED 4 receives 20%
Pos 3.7 -> LED 3 receives 30%, LED 4 receives 70%
```

Recommended default:

```text
linear
```

But the mode must be configurable. This keeps crisp/discrete effects possible.

Example:

```yaml
render:
  particle_mode: linear
  blend_mode: additive
  global_brightness: 1.0
```

Segment reversal does not change particle coordinates. Rendering works in local
segment coordinates first, then Segment mapping converts local indexes to
physical strip indexes.

---

# Performance Recommendations

Avoid during runtime:

```text
map lookups
string comparisons
reflection
YAML access
heap allocations
runtime interface dispatch
```

Prefer:

```text
flat arrays
numeric IDs
float32
precompiled routing
double-buffered particles
contiguous memory
```

Main performance costs will likely be:

```text
HSV -> RGB conversion
pixel blending
hardware flush timing
```

NOT routing.

---

# Recommended Final Runtime Model

```text
Device:
    output target, usually one ESP32

Strip:
    physical RGB memory owned by a Device

Segment:
    logical view into Strip

Port:
    Segment + Endpoint

Hub:
    routing logic between ports

Particle:
    simulation object moving over segment coordinates

Renderer:
    converts particles/effects into strip RGB buffers

Topology:
    precompiled routing tables
```

---

# Recommended Design Decisions

## Keep

- Generic engine, not pyramid-specific
- Device -> Strip ownership in the YAML/data model
- Cross-device segment routing as a natural topology feature
- Server as the central simulation/output coordinator
- Segments as logical views
- Hubs owning fixed/stateless routing for v1
- HSV animation workflow
- Float-based particle positions
- Velocity-driven direction
- YAML topology definition
- Double-buffered particles
- Precompiled runtime routing
- Configurable particle render mode: nearest or linear
- Smooth sub-pixel rendering through linear mode

## Avoid

- Pyramid-specific logic in the core engine
- ESP32-to-ESP32 direct coordination
- Segment -> Hub ownership
- String-based runtime routing
- Runtime graph traversal
- Dynamic allocations per tick
- RGB-only animation workflow
- Particle orientation fields separate from velocity
- Reflection/interface-heavy simulation loops
- Stateful/switching hubs in v1
