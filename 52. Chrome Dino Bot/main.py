"""
Chrome Dinosaur Game bot  (works on https://elgoog.im/t-rex/ or chrome://dino)

Install:   pip install pillow pyautogui
Run:       python dino_bot.py

How it works
------------
1. Calibration: you hover the mouse on the dino's feet level, just in front of
   its face, and press Enter. That point is the "anchor" the bot measures from.
2. Every frame the bot grabs a thin screenshot strip in front of the dino.
   Any pixel that differs from the background colour is an obstacle.
   (Comparing to the background, not a fixed colour, makes it work in night mode too.)
3. A low strip detects cacti -> jump (space).
   A higher strip detects mid-height birds -> duck (down arrow).
4. The look-ahead distance grows with time because the game speeds up.

Stop: move the mouse to a screen corner (pyautogui failsafe) or press Ctrl+C.
"""

import time
import pyautogui
from PIL import ImageGrab

pyautogui.PAUSE = 0          # no artificial delay between pyautogui calls
pyautogui.FAILSAFE = True    # slam the mouse into a corner to abort

# ----------------------------- tunables ---------------------------------
START_LOOKAHEAD = 95      # px in front of the dino to scan at the start
MAX_LOOKAHEAD = 230       # never scan further than this
LOOKAHEAD_GROWTH = 0.9    # extra px of look-ahead per second of play
SCAN_WIDTH_MIN = 60       # width of the scanned box (px)
CACTUS_Y_OFFSET = 8       # px ABOVE the anchor for the cactus strip
BIRD_Y_OFFSET = 48        # px ABOVE the anchor for the bird strip
COLOR_TOLERANCE = 40      # how different from background counts as "obstacle"
DUCK_TIME = 0.35          # seconds to hold duck when a bird is detected
# -------------------------------------------------------------------------


def screen_scale():
    """Ratio between screenshot pixels and pyautogui coordinates (Retina/HiDPI)."""
    shot = ImageGrab.grab()
    return shot.width / pyautogui.size().width


def is_obstacle(img, x0, x1, y, bg):
    """True if any pixel on row y between x0..x1 differs from the background."""
    for x in range(x0, x1, 2):          # step 2 = faster, still catches cacti
        p = img.getpixel((x, y))[:3]
        if sum(abs(p[i] - bg[i]) for i in range(3)) > COLOR_TOLERANCE:
            return True
    return False


def calibrate():
    input("Open the game, then put the mouse on the ground line just in FRONT of "
          "the dino's face (feet level) and press Enter here... ")
    x, y = pyautogui.position()
    scale = screen_scale()
    print(f"Anchor set at ({x}, {y}), screen scale = {scale:.2f}")
    return int(x * scale), int(y * scale), scale


def main():
    ax, ay, scale = calibrate()
    print("Starting in 3 seconds - click the game window so it has focus!")
    time.sleep(3)

    pyautogui.press("space")            # start the game
    start = time.time()
    ducking_until = 0.0
    jumps = 0

    while True:
        now = time.time()
        elapsed = now - start

        look = min(START_LOOKAHEAD + LOOKAHEAD_GROWTH * elapsed, MAX_LOOKAHEAD)
        look = int(look * scale)
        width = int(SCAN_WIDTH_MIN * scale)
        x0, x1 = ax + 4, ax + look + width

        # grab only the small region we care about (much faster than full screen)
        top = ay - int(BIRD_Y_OFFSET * scale) - 4
        bottom = ay + 4
        shot = ImageGrab.grab(bbox=(x0, top, x1, bottom))

        cactus_row = bottom - top - 4 - int(CACTUS_Y_OFFSET * scale)
        bird_row = 4
        bg = shot.getpixel((shot.width - 1, 0))[:3]   # top-right corner = sky

        # scan only up to `look` px for the trigger point
        trigger_x1 = min(shot.width - 1, look)

        if is_obstacle(shot, 0, trigger_x1, cactus_row, bg):
            pyautogui.keyUp("down")
            pyautogui.press("space")
            jumps += 1
            time.sleep(0.12)                 # don't spam jumps while airborne
        elif is_obstacle(shot, 0, trigger_x1, bird_row, bg) and now > ducking_until:
            pyautogui.keyDown("down")
            ducking_until = now + DUCK_TIME
        elif now > ducking_until:
            pyautogui.keyUp("down")

        if jumps and jumps % 10 == 0 and int(elapsed) % 5 == 0:
            print(f"t={elapsed:5.1f}s  jumps={jumps}  look-ahead={look/scale:.0f}px")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pyautogui.keyUp("down")
        print("\nStopped.")