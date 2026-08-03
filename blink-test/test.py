import time
import sys

LED = "/sys/class/leds/ACT"

# ==========================================================
# USER SETTINGS
# ==========================================================
REPEATS = 75             # Number of blink cycles
FASTEST_BLINK = 0.01     # Seconds (ON and OFF)
SLOWEST_BLINK = 0.25     # Seconds (ON and OFF)
# ==========================================================


def led(state):
    with open(f"{LED}/brightness", "w") as f:
        f.write(str(state))


def ease_in_out(t):
    """
    Smooth interpolation.
    Input: 0 -> 1
    Output: 0 -> 1
    """
    return 3 * t**2 - 2 * t**3


# Give manual control over the ACT LED
with open(f"{LED}/trigger", "w") as f:
    f.write("none")

# Calculate all blink durations first
blink_times = []

for i in range(REPEATS):
    t = i / max(REPEATS - 1, 1)
    eased = ease_in_out(t)

    blink = FASTEST_BLINK + (SLOWEST_BLINK - FASTEST_BLINK) * eased
    blink_times.append(blink)

TOTAL_DURATION = sum(b * 2 for b in blink_times)

print("=" * 60)
print(" Raspberry Pi ACT LED Blink Demo")
print("=" * 60)
print(f"Blink cycles      : {REPEATS}")
print(f"Fastest blink     : {FASTEST_BLINK:.3f} s")
print(f"Slowest blink     : {SLOWEST_BLINK:.3f} s")
print(f"Estimated runtime : {TOTAL_DURATION:.2f} seconds")
print()
print("Press Ctrl+C at any time to stop.")
print("=" * 60)

input("\nPress ENTER to begin...")

start = time.time()

try:
    for blink in blink_times:

        led(1)
        time.sleep(blink)

        led(0)
        time.sleep(blink)

        elapsed = time.time() - start
        progress = elapsed / TOTAL_DURATION

        width = 40
        filled = int(progress * width)

        bar = "█" * filled + "░" * (width - filled)

        sys.stdout.write(
            f"\r[{bar}] "
            f"{progress*100:6.2f}% "
            f"| {elapsed:6.2f}s / {TOTAL_DURATION:.2f}s"
        )
        sys.stdout.flush()

except KeyboardInterrupt:
    print("\n\nInterrupted by user.")

finally:
    led(0)

    # Restore SD-card activity LED
    with open(f"{LED}/trigger", "w") as f:
        f.write("mmc0")

    print("\nFinished.")