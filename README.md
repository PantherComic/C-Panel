# 🎛️ C-Panel

A high-performance, dual-screen macro pad powered by the **Raspberry Pi Pico (RP2040)** and **CircuitPython**.

Features **8 mechanical switches** and **4 rotary encoders**, providing instant visual feedback on two independent OLED screens. It uses a custom highly-optimized display driver to bypass standard CircuitPython limitations.

*(Replace this link with a real photo of your build!)*

## ✨ Features

* **Dual OLED Feedback:** Left screen shows button/switch actions; Right screen shows encoder values.
* **Hot-Swappable Config:** Edit `keymap.json` on the fly—no coding required to change shortcuts.
* **Smart Idle Mode:** Screens automatically dim/reset after 3 seconds of inactivity.
* **Unlimited Displays:** Uses a custom `framebuf` implementation to bypass the Pico's hardware limit for `displayio`.
* **SH1106 Native Support:** Includes a custom driver fix for the 2-pixel offset and rotation artifacts common on 1.3" OLEDs.
* **Windows Ready:** Supports media keys, volume, task manager, and locking.

## 🛠️ Hardware

* **Microcontroller:** Raspberry Pi Pico (RP2040)
* **Displays:** 2x SH1106 I2C OLEDs (128x64)
* **Inputs:**
* 8x Mechanical Switches (cherry mx style)
* 4x Rotary Encoders (with push buttons)


* **Wiring:**
* *Left Screen:* I2C1 (GP20/GP21)
* *Right Screen:* I2C0 (GP26/GP27)
* *Switches & Encoders:* Mapped in `code.py`



## 🚀 Installation

1. **Install CircuitPython:** Flash the latest CircuitPython `.uf2` to your Pico.
2. **Add Libraries:** Copy the following from the [Adafruit CircuitPython Bundle](https://circuitpython.org/libraries) to the `lib` folder on your Pico:
* `adafruit_hid` (folder)
* `adafruit_ssd1306.mpy`
* `adafruit_framebuf.mpy`
* `adafruit_display_text` (folder) - *optional but recommended*


3. **Required Font:** **Crucial!** You must copy `font5x8.bin` to the root directory of the Pico.
4. **Deploy Code:** Copy `code.py` and `keymap.json` to the root directory.

## ⚙️ Configuration (`keymap.json`)

Define your shortcuts in `keymap.json`. No compile needed—just save and run.

```json
{
    "switches": [
        {"cmd": "CTRL+C", "label": "Copy"},
        {"cmd": "WIN+L", "label": "Lock PC"}
    ],
    "encoders": [
        {
            "cw": "VOL_UP",
            "ccw": "VOL_DOWN", 
            "label": "Volume"
        }
    ]
}

```

**Supported Commands:**

* **Standard:** `A`, `B`, `1`, `ENTER`, `SPACE`, `TAB`...
* **Modifiers:** `CTRL`, `SHIFT`, `ALT`, `WIN` (e.g., `CTRL+ALT+DELETE`)
* **Media:** `VOL_UP`, `VOL_DOWN`, `MUTE`, `PLAY_PAUSE`, `NEXT`, `PREV`

## 🔧 Technical Deep Dive

### The "Dual Display" Hack

Standard CircuitPython on RP2040 limits `displayio` to one active display to save RAM. This project uses a raw `framebuf` implementation combined with direct I2C commands. This allows for:

1. **Two independent displays** running simultaneously.
2. **Fast refresh rates** via optimized partial updates.

### The SH1106 Offset Fix

SH1106 displays technically have a 132x64 RAM buffer, while standard panels show 128x64. This often causes pixel garbage or shifted text when rotated.

* **Solution:** The code implements a `TEXT_PAD` offset logic and clears the frame buffer (`fill(0)`) before every draw call to eliminate edge artifacts without needing complex driver patches.

## 📂 File Structure

```text
CIRCUITPY/
├── lib/               # CircuitPython Libraries
├── code.py            # Main Logic
├── keymap.json        # User Configuration
└── font5x8.bin        # Binary font file (REQUIRED)

```

## 📄 License

This project is open-source. Feel free to fork, modify, and build your own!
