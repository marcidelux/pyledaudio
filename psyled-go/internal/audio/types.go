package audio

import "time"

// Config contains the audio/JACK settings normally loaded from the root YAML
// configuration.
type Config struct {
	ClientName     string   `yaml:"client_name"`
	InputPortName  string   `yaml:"input_port_name"`
	SourcePorts    []string `yaml:"source_ports"`
	AutoConnect    bool     `yaml:"auto_connect"`
	StartServer    bool     `yaml:"start_server"`
	FFTSize        int      `yaml:"fft_size"`
	BandCount      int      `yaml:"band_count"`
	MinFrequency   float64  `yaml:"min_frequency"`
	MaxFrequency   float64  `yaml:"max_frequency"`
	Gain           float64  `yaml:"gain"`
	SmoothingAlpha float64  `yaml:"smoothing_alpha"`
	SampleBuffer   int      `yaml:"sample_buffer"`
	OutputBuffer   int      `yaml:"output_buffer"`
}

// DefaultConfig returns conservative defaults for the audio module.
func DefaultConfig() Config {
	return Config{
		ClientName:     "psyled-go",
		InputPortName:  "audio_in",
		FFTSize:        2048,
		BandCount:      8,
		MinFrequency:   60,
		MaxFrequency:   18000,
		SmoothingAlpha: 0.35,
		SampleBuffer:   4,
		OutputBuffer:   2,
	}
}

// BandFrame is the audio feature message consumed by future renderer goroutines.
type BandFrame struct {
	Bands      []uint8
	SampleRate int
	FFTSize    int
	Timestamp  time.Time
}
