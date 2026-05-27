//go:build !jack

package audio

import (
	"context"
	"errors"
)

type JackClient struct {
	bands chan BandFrame
}

func NewJackClient(Config) (*JackClient, error) {
	return &JackClient{bands: make(chan BandFrame)}, nil
}

func (c *JackClient) Bands() <-chan BandFrame {
	return c.bands
}

func (c *JackClient) DroppedSampleFrames() uint64 {
	return 0
}

func (c *JackClient) Start(context.Context) error {
	return errors.New("audio JACK support is disabled; rebuild with -tags jack")
}

func (c *JackClient) Close() {
	close(c.bands)
}
