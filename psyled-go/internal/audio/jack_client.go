//go:build jack

package audio

import (
	"context"
	"errors"
	"fmt"
	"math"
	"sync"
	"sync/atomic"
	"time"

	jack "github.com/xthexder/go-jack"
	"gonum.org/v1/gonum/dsp/fourier"
)

// JackClient receives JACK input buffers and publishes FFT band intensities.
type JackClient struct {
	cfg Config

	client *jack.Client
	input  *jack.Port

	samples chan []float64
	bands   chan BandFrame

	closeOnce sync.Once
	wg        sync.WaitGroup

	droppedSampleFrames atomic.Uint64
}

func NewJackClient(cfg Config) (*JackClient, error) {
	cfg = applyDefaults(cfg)
	if err := validateConfig(cfg); err != nil {
		return nil, err
	}

	return &JackClient{
		cfg:     cfg,
		samples: make(chan []float64, cfg.SampleBuffer),
		bands:   make(chan BandFrame, cfg.OutputBuffer),
	}, nil
}

func (c *JackClient) Bands() <-chan BandFrame {
	return c.bands
}

func (c *JackClient) DroppedSampleFrames() uint64 {
	return c.droppedSampleFrames.Load()
}

func (c *JackClient) Start(ctx context.Context) error {
	if c.client != nil {
		return errors.New("jack client already started")
	}

	options := jack.NoStartServer
	if c.cfg.StartServer {
		options = jack.NullOption
	}

	client, status := jack.ClientOpen(c.cfg.ClientName, options)
	if client == nil {
		return fmt.Errorf("open jack client: %w", jack.StrError(status))
	}

	input := client.PortRegister(c.cfg.InputPortName, jack.DEFAULT_AUDIO_TYPE, jack.PortIsInput, 0)
	if input == nil {
		client.Close()
		return fmt.Errorf("register jack input port %q", c.cfg.InputPortName)
	}

	c.client = client
	c.input = input

	sampleRate := int(client.GetSampleRate())

	c.wg.Add(1)
	go c.runDSP(ctx, sampleRate)

	if code := client.SetProcessCallback(c.process); code != 0 {
		c.Close()
		return fmt.Errorf("set jack process callback: code %d", code)
	}

	client.OnShutdown(func() {
		c.Close()
	})

	if code := client.Activate(); code != 0 {
		c.Close()
		return fmt.Errorf("activate jack client: code %d", code)
	}

	if c.cfg.AutoConnect {
		if err := c.connectSources(); err != nil {
			c.Close()
			return err
		}
	}

	go func() {
		<-ctx.Done()
		c.Close()
	}()

	return nil
}

func (c *JackClient) Close() {
	c.closeOnce.Do(func() {
		if c.client != nil {
			c.client.Close()
			c.client = nil
		}
		close(c.samples)
		c.wg.Wait()
		close(c.bands)
	})
}

func (c *JackClient) process(nframes uint32) int {
	buffer := c.input.GetBuffer(nframes)
	samples := make([]float64, len(buffer))
	for i, sample := range buffer {
		samples[i] = float64(sample)
	}

	select {
	case c.samples <- samples:
	default:
		c.droppedSampleFrames.Add(1)
	}

	return 0
}

func (c *JackClient) connectSources() error {
	sourcePorts := c.cfg.SourcePorts
	if len(sourcePorts) == 0 {
		sourcePorts = c.client.GetPorts("", jack.DEFAULT_AUDIO_TYPE, jack.PortIsOutput|jack.PortIsPhysical)
	}
	if len(sourcePorts) == 0 {
		return errors.New("auto-connect requested, but no JACK source ports were found")
	}

	dst := c.input.GetName()
	for _, src := range sourcePorts {
		if code := c.client.Connect(src, dst); code != 0 {
			return fmt.Errorf("connect JACK source %q to %q: code %d", src, dst, code)
		}
	}
	return nil
}

func (c *JackClient) runDSP(ctx context.Context, sampleRate int) {
	defer c.wg.Done()

	fftSize := c.cfg.FFTSize
	accumulator := make([]float64, 0, fftSize*2)
	analyzer := newBandAnalyzer(c.cfg, sampleRate)

	for {
		select {
		case <-ctx.Done():
			return
		case chunk, ok := <-c.samples:
			if !ok {
				return
			}

			accumulator = append(accumulator, chunk...)
			if len(accumulator) < fftSize {
				continue
			}
			if len(accumulator) > fftSize {
				accumulator = append(accumulator[:0], accumulator[len(accumulator)-fftSize:]...)
			}

			frame := BandFrame{
				Bands:      analyzer.calculate(accumulator),
				SampleRate: sampleRate,
				FFTSize:    fftSize,
				Timestamp:  time.Now(),
			}

			select {
			case c.bands <- frame:
			default:
				<-c.bands
				c.bands <- frame
			}
		}
	}
}

type bandAnalyzer struct {
	cfg        Config
	sampleRate int
	fft        *fourier.FFT
	window     []float64
	previous   []float64
}

func newBandAnalyzer(cfg Config, sampleRate int) *bandAnalyzer {
	window := make([]float64, cfg.FFTSize)
	for i := range window {
		window[i] = 0.54 - 0.46*math.Cos(2*math.Pi*float64(i)/float64(cfg.FFTSize-1))
	}

	return &bandAnalyzer{
		cfg:        cfg,
		sampleRate: sampleRate,
		fft:        fourier.NewFFT(cfg.FFTSize),
		window:     window,
		previous:   make([]float64, cfg.BandCount),
	}
}

func (a *bandAnalyzer) calculate(samples []float64) []uint8 {
	windowed := make([]float64, len(samples))
	for i, sample := range samples {
		windowed[i] = sample * a.window[i]
	}

	coeffs := a.fft.Coefficients(nil, windowed)
	bandValues := make([]float64, a.cfg.BandCount)
	bandCounts := make([]int, a.cfg.BandCount)

	binHz := float64(a.sampleRate) / float64(a.cfg.FFTSize)
	maxFFTBin := len(coeffs)
	if maxFFTBin > a.cfg.FFTSize/2+1 {
		maxFFTBin = a.cfg.FFTSize/2 + 1
	}

	for bin := 1; bin < maxFFTBin; bin++ {
		frequency := float64(bin) * binHz
		if frequency < a.cfg.MinFrequency || frequency > a.cfg.MaxFrequency {
			continue
		}

		band := int((frequency - a.cfg.MinFrequency) / (a.cfg.MaxFrequency - a.cfg.MinFrequency) * float64(a.cfg.BandCount))
		if band < 0 {
			continue
		}
		if band >= a.cfg.BandCount {
			band = a.cfg.BandCount - 1
		}

		magnitude := cmplxAbs(coeffs[bin])
		bandValues[band] += magnitude
		bandCounts[band]++
	}

	peak := 0.0
	for i := range bandValues {
		if bandCounts[i] > 0 {
			bandValues[i] /= float64(bandCounts[i])
		}
		if bandValues[i] > peak {
			peak = bandValues[i]
		}
	}

	alpha := a.cfg.SmoothingAlpha
	out := make([]uint8, len(bandValues))
	for i, value := range bandValues {
		if a.cfg.Gain > 0 {
			value *= a.cfg.Gain
		} else if peak > 0 {
			value /= peak
		}

		value = a.previous[i]*(1-alpha) + value*alpha
		a.previous[i] = value

		out[i] = uint8(math.Round(clamp(value, 0, 1) * 255))
	}

	return out
}

func cmplxAbs(v complex128) float64 {
	return math.Hypot(real(v), imag(v))
}

func applyDefaults(cfg Config) Config {
	defaults := DefaultConfig()
	if cfg.ClientName == "" {
		cfg.ClientName = defaults.ClientName
	}
	if cfg.InputPortName == "" {
		cfg.InputPortName = defaults.InputPortName
	}
	if cfg.FFTSize == 0 {
		cfg.FFTSize = defaults.FFTSize
	}
	if cfg.BandCount == 0 {
		cfg.BandCount = defaults.BandCount
	}
	if cfg.MinFrequency == 0 {
		cfg.MinFrequency = defaults.MinFrequency
	}
	if cfg.MaxFrequency == 0 {
		cfg.MaxFrequency = defaults.MaxFrequency
	}
	if cfg.SmoothingAlpha == 0 {
		cfg.SmoothingAlpha = defaults.SmoothingAlpha
	}
	if cfg.SampleBuffer == 0 {
		cfg.SampleBuffer = defaults.SampleBuffer
	}
	if cfg.OutputBuffer == 0 {
		cfg.OutputBuffer = defaults.OutputBuffer
	}
	return cfg
}

func validateConfig(cfg Config) error {
	if cfg.FFTSize < 2 {
		return errors.New("audio fft_size must be at least 2")
	}
	if cfg.BandCount < 1 {
		return errors.New("audio band_count must be at least 1")
	}
	if cfg.MinFrequency < 0 {
		return errors.New("audio min_frequency must be non-negative")
	}
	if cfg.MaxFrequency <= cfg.MinFrequency {
		return errors.New("audio max_frequency must be greater than min_frequency")
	}
	if cfg.SmoothingAlpha < 0 || cfg.SmoothingAlpha > 1 {
		return errors.New("audio smoothing_alpha must be between 0 and 1")
	}
	return nil
}

func clamp(v, min, max float64) float64 {
	if v < min {
		return min
	}
	if v > max {
		return max
	}
	return v
}
