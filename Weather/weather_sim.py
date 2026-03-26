import glfw
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import pygame
import random
import math
import sys
import datetime # Added for timestamping screenshots

# ==========================================
# 1. CONFIGURATION & GLOBALS
# ==========================================
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
PARTICLE_COUNT = 15000 

current_weather = 1  
lightning_flash = 0.0
weather_names = {1: "RAIN", 2: "SNOW", 3: "FOG", 4: "STORM"}

# Particle Array: [x, y, z, speed, phase]
particles = np.zeros((PARTICLE_COUNT, 5), dtype=np.float32)

# ==========================================
# 2. PROCEDURAL AUDIO SYNTHESIZER
# ==========================================
# Initialize mixer explicitly for Stereo (2 channels)
pygame.mixer.init(frequency=44100, size=-16, channels=2)
channel_ambient = pygame.mixer.Channel(0)
channel_effects = pygame.mixer.Channel(1)
sounds = {}

def init_audio():
    print("Synthesizing procedural audio (this takes a second)...")
    sample_rate = 44100
    
    # Generate 1D Mono Noise
    rain_noise = np.random.randint(-8000, 8000, sample_rate, dtype=np.int16)
    
    # Wind (Low-Pass Filtered Noise via stretching)
    low_res_noise = np.random.randint(-12000, 12000, sample_rate // 10, dtype=np.int16)
    wind_noise = np.repeat(low_res_noise, 10) 
    
    # Thunder (Noise with Exponential Decay)
    thunder_samples = sample_rate * 3 
    base_noise = np.random.randint(-32767, 32767, thunder_samples)
    decay_envelope = np.exp(-np.linspace(0, 6, thunder_samples))
    thunder_wave = (base_noise * decay_envelope).astype(np.int16)
    
    # Convert 1D Mono to 2D Stereo (Left and Right channels)
    rain_stereo = np.column_stack((rain_noise, rain_noise))
    wind_stereo = np.column_stack((wind_noise, wind_noise))
    storm_stereo = np.column_stack(((rain_noise * 1.5).astype(np.int16), (rain_noise * 1.5).astype(np.int16)))
    thunder_stereo = np.column_stack((thunder_wave, thunder_wave))
    
    global sounds
    sounds = {
        'rain': pygame.sndarray.make_sound(rain_stereo),
        'wind': pygame.sndarray.make_sound(wind_stereo),
        'storm': pygame.sndarray.make_sound(storm_stereo),
        'thunder': pygame.sndarray.make_sound(thunder_stereo)
    }
    print("Audio ready!")

def play_weather_audio(weather_id):
    if not sounds: return
    channel_ambient.fadeout(500)
    
    if weather_id == 1:   
        channel_ambient.play(sounds['rain'], loops=-1, fade_ms=1000)
    elif weather_id == 2: 
        channel_ambient.play(sounds['wind'], loops=-1, fade_ms=1000)
        channel_ambient.set_volume(0.4) 
    elif weather_id == 3: 
        channel_ambient.play(sounds['wind'], loops=-1, fade_ms=1000)
        channel_ambient.set_volume(0.15) 
    elif weather_id == 4: 
        channel_ambient.play(sounds['storm'], loops=-1, fade_ms=1000)

# ==========================================
# 3. CUSTOM VECTOR FONT & SCREENSHOTS
# ==========================================
font_data = {
    'R': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0.5), (0.8,0.5, 0,0.5), (0.4,0.5, 0.8,0)],
    'A': [(0,0, 0,0.8), (0,0.8, 0.4,1), (0.4,1, 0.8,0.8), (0.8,0.8, 0.8,0), (0,0.5, 0.8,0.5)],
    'I': [(0.4,0, 0.4,1), (0.2,0, 0.6,0), (0.2,1, 0.6,1)],
    'N': [(0,0, 0,1), (0,1, 0.8,0), (0.8,0, 0.8,1)],
    'S': [(0.8,0.8, 0.8,1), (0.8,1, 0,1), (0,1, 0,0.5), (0,0.5, 0.8,0.5), (0.8,0.5, 0.8,0), (0.8,0, 0,0), (0,0, 0,0.2)],
    'O': [(0,0, 0,1), (0,1, 0.8,1), (0.8,1, 0.8,0), (0.8,0, 0,0)],
    'W': [(0,1, 0.2,0), (0.2,0, 0.4,0.5), (0.4,0.5, 0.6,0), (0.6,0, 0.8,1)],
    'F': [(0,0, 0,1), (0,1, 0.8,1), (0,0.5, 0.6,0.5)],
    'G': [(0.8,0.8, 0.8,1), (0.8,1, 0,1), (0,1, 0,0), (0,0, 0.8,0), (0.8,0, 0.8,0.5), (0.5,0.5, 0.8,0.5)],
    'T': [(0.4,0, 0.4,1), (0,1, 0.8,1)],
    'M': [(0,0, 0,1), (0,1, 0.4,0.5), (0.4,0.5, 0.8,1), (0.8,1, 0.8,0)]
}

def take_screenshot():
    """Reads pixels from the OpenGL buffer and saves them as a PNG."""
    # Ensure byte alignment
    glPixelStorei(GL_PACK_ALIGNMENT, 1)
    
    # Read the pixels directly from the screen
    data = glReadPixels(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT, GL_RGB, GL_UNSIGNED_BYTE)
    
    # Convert to pygame image (flipped=True because OpenGL's origin is bottom-left)
    image = pygame.image.fromstring(data, (WINDOW_WIDTH, WINDOW_HEIGHT), 'RGB', True)
    
    # Save with timestamp
    filename = f"weather_sim_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    pygame.image.save(image, filename)
    print(f"📸 Screenshot saved successfully: {filename}")

# ==========================================
# 4. ENGINE LOGIC & RENDERING
# ==========================================
def init_particles():
    for i in range(PARTICLE_COUNT):
        particles[i][0] = random.uniform(-40.0, 40.0)  
        particles[i][1] = random.uniform(-5.0, 25.0)   
        particles[i][2] = random.uniform(-30.0, 5.0)   
        particles[i][3] = random.uniform(0.1, 0.5)     
        particles[i][4] = random.uniform(0.0, 3.14)    

def key_callback(window, key, scancode, action, mods):
    global current_weather
    if action == glfw.PRESS:
        if key in [glfw.KEY_1, glfw.KEY_2, glfw.KEY_3, glfw.KEY_4]:
            current_weather = key - glfw.KEY_0 
            play_weather_audio(current_weather)
        # ADDED KEY LISTENER FOR SCREENSHOT
        elif key == glfw.KEY_S:
            take_screenshot()

def draw_hud(text):
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    glDisable(GL_DEPTH_TEST) 
    glDisable(GL_FOG)

    glColor4f(1.0, 1.0, 1.0, 0.9) 
    glLineWidth(3.0)
    
    start_x, start_y, scale, spacing = 30, 30, 25, 35
    
    glBegin(GL_LINES)
    for i, char in enumerate(text):
        if char in font_data:
            offset_x = start_x + (i * spacing)
            for line in font_data[char]:
                glVertex2f(offset_x + line[0]*scale, start_y + (1-line[1])*scale)
                glVertex2f(offset_x + line[2]*scale, start_y + (1-line[3])*scale)
    glEnd()

    glEnable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glPopMatrix()

def draw_tree(x, z):
    glColor3f(0.3, 0.2, 0.1)
    glBegin(GL_QUADS)
    glVertex3f(x-0.2, -5.0, z); glVertex3f(x+0.2, -5.0, z)
    glVertex3f(x+0.2, -3.0, z); glVertex3f(x-0.2, -3.0, z)
    glEnd()
    
    if current_weather == 2: glColor3f(0.8, 0.9, 0.9)
    else: glColor3f(0.1, 0.4, 0.15)
        
    glBegin(GL_TRIANGLES)
    glVertex3f(x-1.5, -3.0, z); glVertex3f(x+1.5, -3.0, z); glVertex3f(x, 0.0, z)
    glVertex3f(x-1.0, -1.0, z); glVertex3f(x+1.0, -1.0, z); glVertex3f(x, 2.0, z)
    glEnd()

def draw_scenery(flash_intensity):
    if current_weather == 2: 
        sky_top, sky_bot = [0.4, 0.4, 0.5], [0.8, 0.8, 0.85]
        gnd_col = [0.9, 0.9, 0.95]
        mtn_base, mtn_peak = [0.6, 0.6, 0.65], [1.0, 1.0, 1.0]
    elif current_weather == 3: 
        sky_top, sky_bot = [0.5, 0.5, 0.55], [0.4, 0.4, 0.45]
        gnd_col = [0.35, 0.35, 0.4]
        mtn_base, mtn_peak = [0.3, 0.3, 0.35], [0.4, 0.4, 0.45]
    else: 
        sky_top, sky_bot = [0.05, 0.05, 0.1], [0.2, 0.2, 0.25]
        gnd_col = [0.1, 0.15, 0.1]
        mtn_base, mtn_peak = [0.05, 0.1, 0.05], [0.2, 0.3, 0.2]

    if flash_intensity > 0:
        sky_top = sky_bot = gnd_col = [min(1.0, c + flash_intensity) for c in gnd_col]
        mtn_peak = [min(1.0, c + flash_intensity) for c in mtn_peak]

    glDisable(GL_DEPTH_TEST) 
    glBegin(GL_QUADS)
    glColor3f(*sky_top)
    glVertex3f(-40.0, 20.0, -35.0); glVertex3f( 40.0, 20.0, -35.0)
    glColor3f(*sky_bot)
    glVertex3f( 40.0, -5.0, -35.0); glVertex3f(-40.0, -5.0, -35.0)
    glEnd()
    glEnable(GL_DEPTH_TEST)

    glColor3f(*gnd_col)
    glBegin(GL_QUADS)
    glVertex3f(-40.0, -5.0,  10.0); glVertex3f( 40.0, -5.0,  10.0)
    glVertex3f( 40.0, -5.0, -30.0); glVertex3f(-40.0, -5.0, -30.0)
    glEnd()

    glBegin(GL_TRIANGLES)
    glColor3f(*mtn_base); glVertex3f(-30.0, -5.0, -28.0)
    glColor3f(*mtn_peak); glVertex3f(-12.0,  12.0, -28.0)
    glColor3f(*mtn_base); glVertex3f(  0.0, -5.0, -28.0)
    
    glColor3f(*mtn_base); glVertex3f(-8.0, -5.0, -25.0)
    glColor3f(*mtn_peak); glVertex3f(12.0, 15.0, -25.0)
    glColor3f(*mtn_base); glVertex3f(30.0, -5.0, -25.0)
    glEnd()

    draw_tree(-15.0, -10.0)
    draw_tree(8.0, -5.0)
    draw_tree(-4.0, -15.0)

def update_and_draw_particles():
    time_val = glfw.get_time()

    if current_weather == 2:
        glPointSize(3.5)
        glColor4f(1.0, 1.0, 1.0, 0.8)
        glBegin(GL_POINTS)
    else:
        glLineWidth(2.0)
        glColor4f(0.6, 0.7, 0.9, 0.5)
        glBegin(GL_LINES)

    for i in range(PARTICLE_COUNT):
        if current_weather == 2: 
            particles[i][1] -= particles[i][3] * 0.15 
            particles[i][0] += math.sin(time_val * 1.5 + particles[i][4]) * 0.04
        else: 
            particles[i][1] -= particles[i][3] * 2.5 
        
        if particles[i][1] < -5.0:
            particles[i][1] = 25.0
            particles[i][0] = random.uniform(-40.0, 40.0)

        if current_weather == 2:
            glVertex3f(particles[i][0], particles[i][1], particles[i][2])
        else:
            glVertex3f(particles[i][0], particles[i][1], particles[i][2])
            glVertex3f(particles[i][0], particles[i][1] + particles[i][3]*4.0, particles[i][2])
    glEnd()

# ==========================================
# 5. MAIN LOOP
# ==========================================
def main():
    global current_weather, lightning_flash

    init_audio()

    if not glfw.init():
        sys.exit(1)

    window = glfw.create_window(WINDOW_WIDTH, WINDOW_HEIGHT, "HD Weather Simulation", None, None)
    if not window:
        glfw.terminate()
        sys.exit(1)

    glfw.make_context_current(window)
    glfw.set_key_callback(window, key_callback)
    
    glMatrixMode(GL_PROJECTION)
    gluPerspective(60, WINDOW_WIDTH / WINDOW_HEIGHT, 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    glTranslatef(0.0, -2.0, -20.0)

    init_particles()
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_DEPTH_TEST)

    play_weather_audio(current_weather)

    while not glfw.window_should_close(window):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        if current_weather == 4 and random.random() < 0.03: 
            lightning_flash = 1.0
            if sounds and not channel_effects.get_busy():
                channel_effects.play(sounds['thunder'])

        if lightning_flash > 0:
            lightning_flash -= 0.06

        if current_weather == 3:
            glEnable(GL_FOG)
            glFogi(GL_FOG_MODE, GL_EXP2)
            glFogfv(GL_FOG_COLOR, [0.45, 0.45, 0.5, 1.0])
            glFogf(GL_FOG_DENSITY, 0.05)
        else:
            glDisable(GL_FOG)

        draw_scenery(lightning_flash)
        update_and_draw_particles()
        draw_hud(weather_names[current_weather])

        glfw.swap_buffers(window)
        glfw.poll_events()

    pygame.mixer.quit()
    glfw.terminate()

if __name__ == "__main__":
    main()