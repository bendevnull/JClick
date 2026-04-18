#!/usr/bin/python3

import time
import threading
import random
import json
import os
import tkinter as tk
from tkinter import ttk
from pynput.mouse import Button, Controller
from pynput.keyboard import Listener, Key

CONFIG_FILE = "jclick_config.json"
APP_VERSION = "1.0.0"

class AutoClicker:
    def __init__(self):
        self.mouse = Controller()
        self.running = False
        self.holding = False
        self.program_running = True
        
        # Defaults
        self.delay_sec = 0.1 
        self.jitter_sec = 0.02
        self.button = Button.left

    def toggle_clicking(self):
        self.running = not self.running
        if self.running and self.holding: # Safety: stop holding if we start clicking
            self.toggle_hold(force_stop=True)
        return self.running

    def toggle_hold(self, force_stop=False):
        if self.holding or force_stop:
            self.mouse.release(self.button)
            self.holding = False
        else:
            if self.running: self.toggle_clicking() # Safety: stop clicking if we start holding
            self.mouse.press(self.button)
            self.holding = True
        return self.holding

    def exit(self):
        if self.holding: self.mouse.release(self.button)
        self.running = False
        self.program_running = False

    def clicker_loop(self):
        while self.program_running:
            if self.running:
                self.mouse.click(self.button)
                low = max(0.001, self.delay_sec - self.jitter_sec)
                high = self.delay_sec + self.jitter_sec
                time.sleep(random.uniform(low, high))
            else:
                time.sleep(0.1)

# --- Persistence Logic ---
def save_config():
    config = {
        "delay": delay_entry.get(),
        "jitter": jitter_entry.get(),
        "button": mouse_var.get()
    }
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except:
            return None
    return None

# Initialize Backend
clicker = AutoClicker()
threading.Thread(target=clicker.clicker_loop, daemon=True).start()

# --- GUI Setup ---
root = tk.Tk()
root.title(f"JClick v{APP_VERSION}")
root.geometry("320x450")
root.attributes("-topmost", True)

# Variables
mouse_var = tk.StringVar(value="left")
saved_data = load_config()

# --- GUI Functions ---
def apply_settings():
    try:
        clicker.delay_sec = float(delay_entry.get()) / 1000.0
        clicker.jitter_sec = float(jitter_entry.get()) / 1000.0
        clicker.button = Button.left if mouse_var.get() == "left" else Button.right
    except ValueError:
        pass

def handle_toggle_click():
    apply_settings()
    is_on = clicker.toggle_clicking()
    update_ui()

def handle_toggle_hold():
    apply_settings()
    is_holding = clicker.toggle_hold()
    update_ui()

def update_ui():
    if clicker.running:
        status_label.config(text="STATUS: CLICKING", foreground="#2ecc71")
    elif clicker.holding:
        status_label.config(text="STATUS: HOLDING DOWN", foreground="#3498db")
    else:
        status_label.config(text="STATUS: IDLE", foreground="#e74c3c")

# --- UI Layout ---
frame = ttk.Frame(root, padding="20")
frame.pack(expand=True, fill="both")

ttk.Label(frame, text="Click Interval (ms):").pack()
delay_entry = ttk.Entry(frame, justify="center")
delay_entry.insert(0, saved_data["delay"] if saved_data else "100")
delay_entry.pack(fill="x", pady=5)

ttk.Label(frame, text="Jitter +/- (ms):").pack()
jitter_entry = ttk.Entry(frame, justify="center")
jitter_entry.insert(0, saved_data["jitter"] if saved_data else "20")
jitter_entry.pack(fill="x", pady=5)

# Mouse Button Selection
ttk.Label(frame, text="Mouse Button:").pack(pady=(10, 0))
radio_frame = ttk.Frame(frame)
radio_frame.pack()
if saved_data: mouse_var.set(saved_data["button"])
ttk.Radiobutton(radio_frame, text="Left Click", variable=mouse_var, value="left").pack(side="left", padx=10)
ttk.Radiobutton(radio_frame, text="Right Click", variable=mouse_var, value="right").pack(side="left", padx=10)

status_label = ttk.Label(frame, text="STATUS: IDLE", font=("Arial", 12, "bold"), foreground="#e74c3c")
status_label.pack(pady=20)

ttk.Button(frame, text="Toggle Click (F8)", command=handle_toggle_click).pack(fill="x", ipady=5)
ttk.Button(frame, text="Toggle Hold (F9)", command=handle_toggle_hold).pack(fill="x", pady=5, ipady=5)

ttk.Label(frame, text="F8: Rapid Click | F9: Constant Hold", font=("Arial", 8, "italic")).pack(pady=10)

# --- Listeners ---
def on_press(key):
    if key == Key.f8:
        root.after(0, handle_toggle_click)
    if key == Key.f9:
        root.after(0, handle_toggle_hold)

listener = Listener(on_press=on_press)
listener.start()

def on_close():
    save_config()
    clicker.exit()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
