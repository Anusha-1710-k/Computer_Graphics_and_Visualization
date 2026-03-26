# Real-Time HD Weather Simulation

A high-definition, real-time 3D weather simulation built entirely from scratch using Python and OpenGL. This project demonstrates advanced computer graphics techniques, including dynamic particle physics, procedural scenery generation, and mathematical audio synthesis, all running efficiently on the GPU.


* **4 Dynamic Weather States:** Instantly hot-swap between Rain, Snow, Fog, and a Lightning Storm.
* **High-Performance Particle System:** Simulates 15,000+ active particles in real-time. Each weather state features unique physics (e.g., vertical motion blur for rain, sine-wave wind sway for snow).
* **Procedural Scenery & Lighting:** Features mathematically generated mountains, pine trees, and ground planes. The environment's color palette and vertex gradients dynamically react to the current weather (e.g., snow accumulation, lightning flash illumination).
* **Procedural Audio Synthesis:** Generates immersive ambient soundscapes (white noise rain, low-pass filtered wind, exponential decay thunder) purely through `numpy` math—**zero external audio files required.**
* **Custom Vector HUD:** A lightweight, custom-built 2D Orthographic font engine that renders the UI directly on the GPU without relying on external font libraries.
* **Instant Screenshot Engine:** Captures and saves timestamped PNGs of the OpenGL frame buffer with a single keystroke.

## Technologies Used

* **Python 3.x:** Core application logic.
* **PyOpenGL / GLFW:** 3D rendering pipeline, window management, and hardware-accelerated graphics.
* **NumPy:** High-speed mathematical array calculations for particle physics and procedural audio waveforms.
* **Pygame:** Multi-channel, asynchronous audio playback.
