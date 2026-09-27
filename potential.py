import time, threading
from collections import deque
import tkinter as tk
from tkinter import ttk
import serial

SERIAL_PORT = "COM3"
BAUD_RATE = 115200

# sensor's amplitude readings. These are RANGES, not dB.
OKAY_MIN, OKAY_MAX = 0, 30
MODERATE_MIN, MODERATE_MAX = 30, 70
NOT_FINE_MIN = 70

AVERAGE_WINDOW_SECONDS = 2.0
LEVEL_CONFIRM_SECONDS = 5.0

class NoiseProcessor:
    def __init__(self):
        self.samples = deque()
        self.confirmed_status = "OKAY"
        self.confirmed_since = time.monotonic()
        self.candidate_status = "OKAY"
        self.candidate_since = None
        self.current = 0.0
        self.average = 0.0

    def classify(self, value):
        if OKAY_MIN <= value < OKAY_MAX: return "OKAY"
        if MODERATE_MIN <= value < MODERATE_MAX: return "MODERATE"
        if value >= NOT_FINE_MIN: return "NOT FINE"
        return "OKAY"

    def add_sample(self, value):
        now = time.monotonic()
        self.current = float(value)
        self.samples.append((now, self.current))
        cutoff = now - AVERAGE_WINDOW_SECONDS
        while self.samples and self.samples[0][0] < cutoff:
            self.samples.popleft()
        self.average = sum(v for _, v in self.samples) / len(self.samples)
        measured = self.classify(self.average)

        if measured == self.confirmed_status:
            self.candidate_status = measured
            self.candidate_since = None
        else:
            if measured != self.candidate_status:
                self.candidate_status = measured
                self.candidate_since = now
            elif self.candidate_since is not None and now - self.candidate_since >= LEVEL_CONFIRM_SECONDS:
                self.confirmed_status = self.candidate_status
                self.confirmed_since = now
                self.candidate_since = None

    def state(self):
        now = time.monotonic()
        candidate_time = 0 if self.candidate_since is None else now - self.candidate_since
        return self.current, self.average, self.confirmed_status, now-self.confirmed_since, self.candidate_status, candidate_time

class Arduino:
    def __init__(self, callback):
        self.callback = callback
        self.ser = None
        self.running = False

    def start(self):
        self.running = True
        threading.Thread(target=self.loop, daemon=True).start()

    def loop(self):
        try:
            self.ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
            time.sleep(2)
            self.callback(None, f"Connected to {SERIAL_PORT}")
            while self.running:
                line = self.ser.readline().decode("utf-8", errors="ignore").strip()
                if line.startswith("DATA:"):
                    try: self.callback(float(line.split(":",1)[1]), None)
                    except ValueError: pass
        except Exception as e:
            self.callback(None, f"Connection error: {e}")

    def send(self, status, seconds):
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(f"STATUS:{status}:{int(seconds)}\n".encode())
            except Exception: pass

    def stop(self):
        self.running = False
        if self.ser:
            try: self.ser.close()
            except Exception: pass

class App:
    def __init__(self, root):
        self.root = root
        root.title("Noise Monitor")
        root.geometry("850x500")
        self.processor = NoiseProcessor()
        self.arduino = Arduino(self.receive)
        self.build()
        root.protocol("WM_DELETE_WINDOW", self.close)
        self.arduino.start()
        self.update()

    def build(self):
        main = ttk.Frame(self.root, padding=20); main.pack(fill="both", expand=True)
        ttk.Label(main, text="ENVIRONMENTAL NOISE MONITOR", font=("Arial",22,"bold")).pack(anchor="w")
        ttk.Label(main, text="Python rolling average + 5-second range confirmation").pack(anchor="w", pady=(0,20))
        row = ttk.Frame(main); row.pack(fill="x")
        self.current = self.card(row,"CURRENT",0); self.average=self.card(row,"AVERAGE",1); self.status=self.card(row,"STATUS",2); self.duration=self.card(row,"STATUS TIME",3)
        box=ttk.LabelFrame(main,text="Noise status",padding=20); box.pack(fill="x",pady=20)
        self.big=ttk.Label(box,text="STATUS: OKAY",font=("Arial",26,"bold")); self.big.pack()
        self.transition=ttk.Label(box,text="No pending transition"); self.transition.pack(pady=(10,0))
        self.connection=ttk.Label(main,text="Connecting..."); self.connection.pack(anchor="w")
        ttk.Label(main,text=f"Ranges: OKAY {OKAY_MIN}–<{OKAY_MAX} | MODERATE {MODERATE_MIN}–<{MODERATE_MAX} | NOT FINE {NOT_FINE_MIN}+ | confirmation: {LEVEL_CONFIRM_SECONDS:.0f}s").pack(anchor="w",pady=12)

    def card(self,parent,title,col):
        f=ttk.LabelFrame(parent,text=title,padding=12); f.grid(row=0,column=col,sticky="nsew",padx=4); parent.columnconfigure(col,weight=1)
        l=ttk.Label(f,text="0",font=("Arial",18,"bold")); l.pack(); return l

    def receive(self,value,message):
        if message: self.connection.config(text=message)
        if value is not None: self.processor.add_sample(value)

    def update(self):
        cur,avg,status,duration,candidate,candidate_time=self.processor.state()
        self.current.config(text=f"{cur:.1f}"); self.average.config(text=f"{avg:.1f}"); self.status.config(text=status); self.duration.config(text=f"{duration:.1f} s"); self.big.config(text=f"STATUS: {status}")
        if candidate != status:
            remaining=max(0,LEVEL_CONFIRM_SECONDS-candidate_time)
            self.transition.config(text=f"New range: {candidate} — confirming in {remaining:.1f}s")
        else: self.transition.config(text="No pending transition")
        self.arduino.send(status,duration)
        self.root.after(200,self.update)

    def close(self): self.arduino.stop(); self.root.destroy()

if __name__ == "__main__":
    root=tk.Tk(); App(root); root.mainloop()