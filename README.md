# Real-time Audio Reactive LED Controller

This project provides a dynamic visualization system using real-time audio input to drive WS2812LED strip animations. It processes audio signals using Fast Fourier Transform (FFT), Mel-scale filter banks, and adaptive gain smoothing to visualize audio frequencies on RGB LED strips. Additionally, a web-based user interface allows easy interaction, monitoring, and control.

Thanks to scottlawsonbc and for his project: https://github.com/scottlawsonbc/audio-reactive-led-strip  
I took out a lot from his work :)

## 🎯 Features

Real-time audio processing: Captures audio input, applies FFT and Mel-scale filters.
Dynamic LED visualization: Real-time mapping of audio frequency bands onto RGB LEDs.
Adaptive smoothing: Provides responsive yet smooth transitions between audio peaks and quiet periods.
Flexible configuration: Dynamically adjustable frequency bands, color palettes, and more.
Interactive web interface: Monitor audio bands, check system health, and control visualization parameters easily from a browser.

## 🛠 Technology Stack

Backend: Python, FastAPI, PyAudio, NumPy, SciPy, Uvicorn
Frontend: HTML/CSS, JavaScript, Chart.js, WebSockets
Hardware: Compatible with Raspberry Pi and WS2812 (NeoPixel) LED strips

