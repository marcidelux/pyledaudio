package config

import (
	"fmt"
	"os"

	"gopkg.in/yaml.v3"
	"psyled-go/internal/audio"
)

type Config struct {
	Server  ServerConfig  `yaml:"server"`
	Audio   audio.Config  `yaml:"audio"`
	UDP     UDPConfig     `yaml:"udp"`
	Effects EffectsConfig `yaml:"effects"`
}

type ServerConfig struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

type UDPConfig struct {
	Host string `yaml:"host"`
	Port int    `yaml:"port"`
}

type EffectsConfig struct {
	MemoryFile  string `yaml:"memory_file"`
	DefaultList string `yaml:"default_list"`
}

func Default() Config {
	return Config{
		Server: ServerConfig{
			Host: "0.0.0.0",
			Port: 9876,
		},
		Audio: audio.DefaultConfig(),
		UDP: UDPConfig{
			Host: "192.168.60.150",
			Port: 12345,
		},
		Effects: EffectsConfig{
			MemoryFile:  "../memory.json",
			DefaultList: "static",
		},
	}
}

func Load(path string) (Config, error) {
	cfg := Default()

	data, err := os.ReadFile(path)
	if err != nil {
		return Config{}, fmt.Errorf("read config file %q: %w", path, err)
	}

	if err := yaml.Unmarshal(data, &cfg); err != nil {
		return Config{}, fmt.Errorf("parse config file %q: %w", path, err)
	}

	if err := validate(cfg); err != nil {
		return Config{}, err
	}

	return cfg, nil
}

func validate(cfg Config) error {
	if cfg.Server.Port <= 0 || cfg.Server.Port > 65535 {
		return fmt.Errorf("server.port must be between 1 and 65535")
	}
	if cfg.UDP.Port <= 0 || cfg.UDP.Port > 65535 {
		return fmt.Errorf("udp.port must be between 1 and 65535")
	}
	if cfg.Effects.MemoryFile == "" {
		return fmt.Errorf("effects.memory_file is required")
	}
	return nil
}
