import board
import digitalio
import rotaryio
import busio
import time
import json
import displayio
import terminalio
import usb_hid

from adafruit_display_text import label
from adafruit_displayio_ssd1306 import SSD1306
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from adafruit_hid.consumer_control import ConsumerControl
from adafruit_hid.consumer_control_code import ConsumerControlCode

# --- 1. SETUP USB & CONFIG ---
kbd = Keyboard(usb_hid.devices)
cc = ConsumerControl(usb_hid.devices)

# Mapping für Tasten-Namen zu Keycodes
KEY_MAP = {
    "A": Keycode.A, "B": Keycode.B, "C": Keycode.C, "D": Keycode.D, "E": Keycode.E, 
    "F": Keycode.F, "G": Keycode.G, "H": Keycode.H, "I": Keycode.I, "J": Keycode.J, 
    "K": Keycode.K, "L": Keycode.L, "M": Keycode.M, "N": Keycode.N, "O": Keycode.O, 
    "P": Keycode.P, "Q": Keycode.Q, "R": Keycode.R, "S": Keycode.S, "T": Keycode.T, 
    "U": Keycode.U, "V": Keycode.V, "W": Keycode.W, "X": Keycode.X, "Y": Keycode.Y, "Z": Keycode.Z,
    "CTRL": Keycode.CONTROL, "SHIFT": Keycode.SHIFT, "ALT": Keycode.ALT, "WIN": Keycode.GUI,
    "ENTER": Keycode.ENTER, "SPACE": Keycode.SPACE, "TAB": Keycode.TAB, "ESC": Keycode.ESCAPE,
    "F13": Keycode.F13, "F14": Keycode.F14, "F15": Keycode.F15
}

MEDIA_MAP = {
    "VOL_UP": ConsumerControlCode.VOLUME_INCREMENT,
    "VOL_DOWN": ConsumerControlCode.VOLUME_DECREMENT,
    "MUTE": ConsumerControlCode.MUTE,
    "MEDIA_PLAY_PAUSE": ConsumerControlCode.PLAY_PAUSE,
    "MEDIA_NEXT": ConsumerControlCode.SCAN_NEXT_TRACK,
    "MEDIA_PREV": ConsumerControlCode.SCAN_PREVIOUS_TRACK
}

# --- 2. SETUP DISPLAYS ---
displayio.release_displays()

def setup_oled(sda, scl):
    i2c = busio.I2C(scl, sda)
    display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
    display = SSD1306(display_bus, width=128, height=64)
    
    # Erstelle Text-Gruppe
    group = displayio.Group()
    # Titel (oben klein)
    lbl_title = label.Label(terminalio.FONT, text="Ready", color=0xFFFFFF, x=0, y=10)
    # Haupttext (mitte groß - simuliert durch Skalierung)
    lbl_main = label.Label(terminalio.FONT, text="--", color=0xFFFFFF, x=0, y=35, scale=2)
    
    group.append(lbl_title)
    group.append(lbl_main)
    display.root_group = group
    return display, lbl_title, lbl_main

# Display Links (I2C0) & Rechts (I2C1)
oled_L, title_L, main_L = setup_oled(board.GP20, board.GP21)
oled_R, title_R, main_R = setup_oled(board.GP26, board.GP27)

title_L.text = "Encoder Status"
title_R.text = "Switch Status"

# --- 3. SETUP HARDWARE (INPUTS) ---
# Pins definieren (Encoder A, B, Switch)
enc_pins = [
    (board.GP0, board.GP1, board.GP2),
    (board.GP3, board.GP4, board.GP5),
    (board.GP6, board.GP7, board.GP8),
    (board.GP9, board.GP10, board.GP11)
]

encoders = []
enc_switches = []
last_positions = []

for pin_a, pin_b, pin_sw in enc_pins:
    enc = rotaryio.IncrementalEncoder(pin_a, pin_b)
    encoders.append(enc)
    last_positions.append(0)
    
    sw = digitalio.DigitalInOut(pin_sw)
    sw.direction = digitalio.Direction.INPUT
    sw.pull = digitalio.Pull.UP
    enc_switches.append(sw)

# Switches (6 Stück)
switch_pins = [board.GP12, board.GP13, board.GP14, board.GP15, board.GP16, board.GP17]
switches = []
for pin in switch_pins:
    sw = digitalio.DigitalInOut(pin)
    sw.direction = digitalio.Direction.INPUT
    sw.pull = digitalio.Pull.UP
    switches.append(sw)

# --- 4. FUNKTIONEN ---
def load_config():
    try:
        with open("keymap.json", "r") as f:
            return json.load(f)
    except:
        print("Fehler: keymap.json nicht gefunden!")
        return None

config = load_config()

def send_command(cmd_str):
    if cmd_str in MEDIA_MAP:
        cc.send(MEDIA_MAP[cmd_str])
        return
    
    # Spezialfälle für Zoom/Scroll Simulation
    if cmd_str == "SCROLL_UP": cc.send(0x0200) # Pseudo code, HID library abhängig
    
    keys = []
    parts = cmd_str.split("+")
    for part in parts:
        if part in KEY_MAP:
            keys.append(KEY_MAP[part])
    
    if keys:
        kbd.send(*keys)

def update_display(side, text_top, text_big):
    if side == "L":
        if text_top: title_L.text = text_top
        if text_big: main_L.text = text_big
    else:
        if text_top: title_R.text = text_top
        if text_big: main_R.text = text_big

# --- 5. HAUPTSCHLEIFE ---
print("Makropad Startklar!")

while True:
    if not config: break # Stop wenn Config fehlt

    # --- A. Encoder Logik ---
    for i, enc in enumerate(encoders):
        position = enc.position
        if position != last_positions[i]:
            direction = "cw" if position > last_positions[i] else "ccw"
            cmd_key = config["encoders"][i][direction]
            name = config["encoders"][i]["name"]
            
            # Aktion ausführen
            # Simpler Hack für Scroll/Zoom, da ConsumerControl begrenzt ist
            if "VOL" in cmd_key: send_command(cmd_key)
            elif "SCROLL" in cmd_key: kbd.send(Keycode.MW_DOWN) if "DOWN" in cmd_key else kbd.send(Keycode.MW_UP)
            elif "ZOOM" in cmd_key: 
                kbd.press(Keycode.CONTROL)
                if "IN" in cmd_key: kbd.send(Keycode.MW_UP) # Mausrad simulieren ist tricky, hier Workaround
                else: kbd.send(Keycode.MW_DOWN)
                kbd.release_all()
            else:
                send_command(cmd_key)

            # Display Update (Links für Encoder)
            update_display("L", f"{name}", f"{direction.upper()}")
            last_positions[i] = position

        # Encoder Button
        if not enc_switches[i].value:
            cmd = config["encoders"][i]["push"]
            send_command(cmd)
            update_display("L", f"{config['encoders'][i]['name']}", "PUSH")
            time.sleep(0.2) # Entprellen

    # --- B. Switches Logik ---
    for i, sw in enumerate(switches):
        if not sw.value:
            cmd = config["switches"][i]["cmd"]
            name = config["switches"][i]["name"]
            
            send_command(cmd)
            # Display Update (Rechts für Tasten)
            update_display("R", "Taste gedrückt:", name)
            
            while not sw.value: pass # Warten bis losgelassen
            time.sleep(0.05)

    time.sleep(0.002) # Sehr kurze Pause für Stabilität