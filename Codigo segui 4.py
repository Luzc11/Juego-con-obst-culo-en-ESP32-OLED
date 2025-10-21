
from machine import Pin, I2C, PWM
import ssd1306, framebuf, time, urandom

# --- CONFIGURACIÓN GENERAL ---
SDA, SCL = 21, 22
OLED_W, OLED_H = 128, 64
BTN_UP, BTN_DOWN, BTN_START = 12, 13, 14
BUZZ = 15

# --- OLED ---
i2c = I2C(0, scl=Pin(SCL), sda=Pin(SDA)) # crea
oled = ssd1306.SSD1306_I2C(OLED_W, OLED_H, i2c) # incia

# --- BOTONES y BUZZER ---
up = Pin(BTN_UP, Pin.IN, Pin.PULL_UP)
down = Pin(BTN_DOWN, Pin.IN, Pin.PULL_UP) # configura
start = Pin(BTN_START, Pin.IN, Pin.PULL_UP)
buzzer = PWM(Pin(BUZZ)) # diferents
buzzer.duty(0)

def beep(f=1000, t=80):
    buzzer.freq(f) # vibra
    buzzer.duty(512) # energia
    time.sleep_ms(t)
    buzzer.duty(0)

# --- ❤️ SPRITE DEL JUGADOR (corazón # datos
SPR_PLAYER = bytearray([
    0x00,0x36,0x7F,0xFF,0xFF,0xFF,0x7E,0x3C,
    0x3C,0x7E,0xFF,0xFF,0xFF,0x7F,0x36,0x00,
    0x00,0x36,0x7F,0xFF,0xFF,0xFF,0x7E,0x3C,
    0x3C,0x7E,0xFF,0xFF,0xFF,0x7F,0x36,0x00
])
fb_player = framebuf.FrameBuffer(SPR_PLAYER, 16, 16, framebuf.MONO_VLSB) # convierte 

# --- ⭐ SPRITE DEL OBSTÁCULO (estrella 8x16, figura,estrella) ---
SPR_STAR = bytearray([
    0x10,0x38,0x7C,0x10,0x7C,0x38,0x10,0x00,
    0x10,0x38,0x7C,0x10,0x7C,0x38,0x10,0x00
])
fb_star = framebuf.FrameBuffer(SPR_STAR, 8, 16, framebuf.MONO_VLSB)

# --- VARIABLES ---
player_x, player_y = 10, 24
obstacles = []
mode = 0
state = 0
score = 0
start_time = 0

# --- FUNCIONES ---
def spawn_obstacle():
    y = urandom.getrandbits(6) % (OLED_H - 16) # posicion 
    speed = 80 if mode == 0 else (100 if mode == 1 else 130)
    obstacles.append({'x': OLED_W, 'y': y, 'speed': speed})

def draw():
    oled.fill(0)
    if state == 0:
        oled.text("DODGER - MENU", 0, 0)
        opciones = ["Clasico", "Contra-t", "Hardcore"]
        for i, m in enumerate(opciones):
            mark = ">" if i == mode else " "
            oled.text(f"{mark}{m}", 0, 16 + i * 10)
        oled.text("Start=Jugar", 0, 56)
    elif state == 1:
        oled.text(f"P:{score}", 0, 0)
        oled.text(f"T:{(time.ticks_ms()-start_time)//1000}s", 64, 0)
        oled.blit(fb_player, player_x, player_y)
        for o in obstacles:
            oled.blit(fb_star, int(o['x']), int(o['y']))
    elif state == 2:
        oled.text("PAUSA", 44, 20)
        oled.text("Start para seguir", 0, 40)
    elif state == 3:
        oled.text("GAME OVER", 20, 20)
        oled.text(f"Puntos:{score}", 0, 40)
    oled.show()

def choque(x1, y1, w1, h1, x2, y2, w2, h2):
    return not (x1+w1 <= x2 or x2+w2 <= x1 or y1+h1 <= y2 or y2+h2 <= y1)

# --- INICIO ---
draw()
last = time.ticks_ms()

# --- BUCLE PRINCIPAL ---
while True:
    # MENÚ
    if state == 0:
        if not up.value(): mode = (mode - 1) % 3; beep(); draw() # detecta
        if not down.value(): mode = (mode + 1) % 3; beep(); draw()
        if not start.value():
            state = 1; beep(1500)
            obstacles, score = [], 0
            start_time = time.ticks_ms()
            draw()
            time.sleep_ms(300)

    # JUEGO
    elif state == 1:
        if not up.value(): player_y = max(0, player_y - 8)
        if not down.value(): player_y = min(OLED_H - 16, player_y + 8)
        if not start.value(): state = 2; beep(800)
        now = time.ticks_ms()
        if time.ticks_diff(now, last) > 700:
            spawn_obstacle()
            last = now
        new_obs = []
        for o in obstacles:
            o['x'] -= o['speed'] * 0.03
            if o['x'] + 8 > 0:
                new_obs.append(o)
            else:
                score += 1
        obstacles = new_obs
        for o in obstacles:
            if choque(player_x, player_y, 16, 16, o['x'], o['y'], 8, 16):
                beep(200, 400)
                state = 3
        draw()
        if mode == 1 and (time.ticks_ms() - start_time) > 60000:
            state = 3

    # PAUSA
    elif state == 2:
        draw()
        if not start.value():
            state = 1
            beep(1000)
            time.sleep_ms(300)

    # GAME OVER
    elif state == 3:
        draw()
        if not start.value():
            state = 0
            beep(1000)
            draw()
            time.sleep_ms(300)

    time.sleep_ms(30)
