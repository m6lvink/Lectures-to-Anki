import sys
import time
import threading

def startProgressBar(totalSteps):
    stopEvent = threading.Event()
    barLen = 30
    state = {"current": 0, "total": max(1, totalSteps)}

    def animate():
        while not stopEvent.is_set():
            pct = min(100, int((state["current"] / state["total"]) * 100))
            filled = int((pct / 100) * barLen)
            bar = "=" * filled + " " * (barLen - filled)
            sys.stdout.write(f"\r[{bar}] {pct:3d}% ({state['current']}/{state['total']})")
            sys.stdout.flush()
            time.sleep(0.15)
        
        sys.stdout.write(f"\r[{'=' * barLen}] 100% ({state['total']}/{state['total']})\n")
        sys.stdout.flush()

    thread = threading.Thread(target=animate, daemon=True)
    thread.start()

    def update(count):
        state["current"] = count

    return update, stopEvent, thread

