import board
import busio
import displayio
import digitalio
import rotaryio
import time
import json
import usb_hid
import adafruit_ssd1306
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# --- CONFIG ---
TEXT_PAD = 4        # Padding x-pixels to fix SH1106 edge artifacts
IDLE_SEC = 3.0      # Seconds before resetting to default screen

# --- DISPLAY DRIVER ---
displayio.release_displays()

class SH1106_Driver(adafruit_ssd1306.SSD1306_I2C):
    def show(self):
        for page in range(8):
            self.write_cmd(0xB0 + page)
            self.write_cmd(0x02 & 0x0F) 
            self.write_cmd(0x10 | (0x02 >> 4))
            start = page * 128
            with self.i2c_device as i2c:
                i2c.write(b'\x40' + self.buffer[start:start+128])

# --- SETUP HARDWARE ---
disp1, disp2 = None, None

# I2C & Displays
try:
    i2c1 = busio.I2C(board.GP21, board.GP20, frequency=400000)
    disp1 = SH1106_Driver(128, 64, i2c1, addr=0x3C)
    disp1.rotation = 2
except: pass

try:
    i2c2 = busio.I2C(board.GP27, board.GP26, frequency=400000)
    disp2 = SH1106_Driver(128, 64, i2c2, addr=0x3C)
    disp2.rotation = 2
except: pass

# Input Devices
sw_pins = [board.GP15, board.GP14, board.GP13, board.GP12, board.GP16, board.GP17, board.GP18, board.GP19]
switches = [digitalio.DigitalInOut(p) for p in sw_pins]
for sw in switches: sw.direction, sw.pull = digitalio.Direction.INPUT, digitalio.Pull.UP

btn_pins = [board.GP3, board.GP2, board.GP1, board.GP0]
enc_btns = [digitalio.DigitalInOut(p) for p in btn_pins]
for btn in enc_btns: btn.direction, btn.pull = digitalio.Direction.INPUT, digitalio.Pull.UP

enc_pins = [(board.GP7, board.GP6), (board.GP10, board.GP11), (board.GP8, board.GP9), (board.GP4, board.GP5)]
encoders = [rotaryio.IncrementalEncoder(a, b) for a, b in enc_pins]
last_pos = [e.position for e in encoders]

# HID
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# --- MAPPINGS ---
KEY_MAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D, "E": Keycode.E,
    "F": Keycode.F, "G": Keycode.G, "H": Keycode.H, "I": Keycode.I, "J": Keycode.J,
    "K": Keycode.K, "L": Keycode.L, "M": Keycode.M, "N": Keycode.N, "O": Keycode.O,
    "P": Keycode.P, "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T,
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X, "Y": Keycode.Y, "Z": Keycode.Z,
    "0": Keycode.ZERO, "1": Keycode.ONE, "2": Keycode.TWO, "3": Keycode.THREE, "4": Keycode.FOUR,
    "5": Keycode.FIVE, "6": Keycode.SIX, "7": Keycode.SEVEN, "8": Keycode.EIGHT, "9": Keycode.NINE,
    "CTRL": Keycode.CONTROL, "SHIFT": Keycode.SHIFT, "WIN": Keycode.GUI, "ALT": Keycode.ALT,
    "SPACE": Keycode.SPACE, "ENTER": Keycode.ENTER, "ESC": Keycode.ESCAPE, "TAB": Keycode.TAB,
    "DELETE": Keycode.DELETE, "BACKSPACE": Keycode.BACKSPACE,
    "UP": Keycode.UP_ARROW, "DOWN": Keycode.DOWN_ARROW, "LEFT": Keycode.LEFT_ARROW, "RIGHT": Keycode.RIGHT_ARROW,
    "F1": Keycode.F1, "F2": Keycode.F2, "F3": Keycode.F3, "F4": Keycode.F4, "F5": Keycode.F5,
    "F6": Keycode.F6, "F7": Keycode.F7, "F8": Keycode.F8, "F9": Keycode.F9, "F10": Keycode.F10,
    "F11": Keycode.F11, "F12": Keycode.F12, "F13": Keycode.F13, "F14": Keycode.F14, "F15": Keycode.F15
}

MEDIA_MAP = {
    "VOL_UP": ConsumerControlCode.VOLUME_INCREMENT, "VOL_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "MUTE": ConsumerControlCode.MUTE, "PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
    "NEXT": ConsumerControlCode.SCAN_NEXT_TRACK, "PREV": ConsumerControlCode.SCAN_PREVIOUS_TRACK
}

# --- HELPERS ---
def load_conf():
    try:
        with open("keymap.json", "r") as f: return json.load(f)
    except: return None

def draw(disp, title, msg):
    if disp:
        disp.fill(0)
        disp.text(title, TEXT_PAD, 15, 1)
        disp.text(msg, TEXT_PAD, 35, 1)
        disp.show()

def run_cmd(cmd):
    if not cmd: return
    if cmd in MEDIA_MAP:
        cc.send(MEDIA_MAP[cmd])
    else:
        keys = [KEY_MAP[k] for k in cmd.split("+") if k in KEY_MAP]
        if keys: kbd.send(*keys)

def reset_screens():
    draw(disp1, "C-Panel", "")
    draw(disp2, "XXX", "")

# --- MAIN LOOP ---
cfg = load_conf()
last_act = time.monotonic()
idle = False

if cfg: reset_screens()

while True:
    if not cfg: time.sleep(1); continue
    
    now = time.monotonic()
    act = False

    # 1. Switches
    for i, sw in enumerate(switches):
        if not sw.value:
            act = True
            entry = cfg["switches"][i] if i < len(cfg["switches"]) else {}
            draw(disp1, f"SW{i+1}:", entry.get("label", ""))
            run_cmd(entry.get("cmd"))
            while not sw.value: pass
            time.sleep(0.05)

    # 2. Encoder Buttons
    for i, btn in enumerate(enc_btns):
        if not btn.value:
            act = True
            entry = cfg["encoder_buttons"][i] if i < len(cfg["encoder_buttons"]) else {}
            draw(disp1, f"BTN {i+1}:", entry.get("label", ""))
            run_cmd(entry.get("cmd"))
            while not btn.value: pass
            time.sleep(0.05)

    # 3. Encoders
    for i, enc in enumerate(encoders):
        pos = enc.position
        if pos != last_pos[i]:
            act = True
            direction = "cw" if pos > last_pos[i] else "ccw"
            entry = cfg["encoders"][i] if i < len(cfg["encoders"]) else {}
            cmd = entry.get(direction)
            if cmd:
                draw(disp2, f"E{i+1} {direction.upper()}", entry.get("label", ""))
                run_cmd(cmd)
            last_pos[i] = pos

    # Idle Logic
    if act:
        last_act = now
        idle = False
    elif not idle and (now - last_act > IDLE_SEC):
        reset_screens()
        idle = True

    time.sleep(0.005)
