import tkinter as tk
from tkinter import ttk
import random
from gg import GG
import sounddevice as sd
import numpy as np

gg:GG=GG()
device_name = gg.read_sonar_device_friendlyname("game")

def find_device_by_wasapi_id(wasapi_id):
    """Find sounddevice device index and channel count from WASAPI ID"""
    try:
        devices = sd.query_devices()
        for device in devices:
            if device['name'] and wasapi_id in device['name']:
                return device["index"], device['max_output_channels']
    except Exception as e:
        print(f"Error querying devices: {e}")
    return None, 0

def callback(indata, frames, time, status):
    rms = np.sqrt(np.mean(indata**2))
    print(rms)

# Find device index from WASAPI ID
device_index, num_channels = find_device_by_wasapi_id(device_name)
if device_index is not None:
    print(f"Found device at index: {device_index} with {num_channels} channels")
    stream = sd.InputStream(device=25, callback=callback)
    stream.start()
else:
    print(f"Device not found. Available devices:")
    sd.query_devices()
    stream = None

slider_offset=6
slider_height=150
channel_width=100
slider_width=10

class VolumeSliderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Volume Control")
        self.root.geometry(f"{str(6*channel_width)}x300")

        self.create_widgets()
        self.update_meter()

    def update_meter(self,):
        for channel, (frame,slider, label, meter, bar) in self.sliders.items():
            level =random.randint(0, 100)  # replace with real audio later
            y = (slider_height - (level * int(label.cget("text"))/100 / 100 * slider_height)) 

            meter.coords(bar, (channel_width-slider_width)/2, y+slider_offset, (channel_width+slider_width)/2, slider_height+slider_offset)

        self.root.after(100, self.update_meter)

    def create_widgets(self):
        title = ttk.Label(self.root, text="Volume Mixer", font=("Arial", 14))
        title.pack(pady=10)

        container = ttk.Frame(self.root)
        container.pack(expand=True, fill='both')

        self.sliders = {}

        channels = gg.channels

        for i, channel in enumerate(channels):
            self.sliders[channel] = self.create_slider(container, channel,75)
            self.sliders[channel][0].grid(row=0, column=i)

    def create_slider(self, parent, channel, val):
        frame = ttk.Frame(parent,width=channel_width)
        value_label = ttk.Label(frame, text=str(val))
        value_label.pack(pady=5)

        slider_frame = tk.Frame(frame, width=channel_width, height=slider_height+2*slider_offset)
        slider_frame.pack()
        slider_frame.pack_propagate(False)

        # Canvas for everything
        meter = tk.Canvas(slider_frame, width=channel_width, height=slider_height, highlightthickness=0)
        meter.pack(fill='both', expand=True)
        meter.create_rectangle((channel_width-slider_width)/2, 0+slider_offset, (channel_width+slider_width)/2, slider_height+slider_offset,fill="")
        bar_bg = meter.create_rectangle((channel_width-slider_width)/2, 0 + slider_offset, (channel_width+slider_width)/2, slider_height+slider_offset, fill="gray")
        bar_fill = meter.create_rectangle((channel_width-slider_width)/2, (slider_height+slider_offset - (val / 100 * slider_height)), (channel_width+slider_width)/2, slider_height+slider_offset, fill="green")
        knob = meter.create_oval((channel_width-slider_width*2)/2, slider_height+slider_offset - val*1.5 - 5, (channel_width+slider_width*2)/2, slider_height+slider_offset - val*1.5 + 5, fill="white", outline="black")

        def update_slider(event:tk.Event|None=None, new_val=None):
            # Calculate value from mouse or argument
            if event:
                y = event.y
                val_float = max(0, min(100, 100 - (y / slider_height * 100)))
            elif new_val:
                val_float = float(new_val)
            else:
                return

            meter.coords(knob, (channel_width-slider_width*2)/2, slider_height+slider_offset - val_float*1.5 - 5, (channel_width+slider_width*2)/2, slider_height+slider_offset - val_float*1.5 + 5)
            value_label.config(text=str(int(val_float)))
            self.update_volume(channel, val_float)

        meter.bind("<B1-Motion>", update_slider)
        meter.bind("<Button-1>", update_slider)

        label = ttk.Label(frame, text=channel)
        label.pack(pady=5)

        update_slider(new_val=val)
        return frame, None, value_label, meter, bar_fill

    def update_volume(self, channel, value):
        if channel in self.sliders:
            frame, slider, label, meter, bar = self.sliders[channel]
            label.config(text=str(int(float(value))))
            print(f"{channel} volume: {int(float(value))}")



if __name__ == "__main__":
    root = tk.Tk()
    app = VolumeSliderApp(root)
    root.mainloop()
