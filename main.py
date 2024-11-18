import tkinter as tk
from tkinter import simpledialog
from tkinter import filedialog, messagebox
import pygame
import wave
import os
from pydub import AudioSegment
import threading
import csv
import glob
import json
import time


def has_files(directory_path):
    for item in os.listdir(directory_path):
        if os.path.isfile(os.path.join(directory_path, item)):
            return True
    return False

class AudioSplitter:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Splitter")

        # Initialize variables
        self.audio_file = None
        self.output_dir = None
        self.metadata_file = None
        self.split_points = []
        self.playing = False
        self.current_position = 0
        self.is_seeking = False
        self.config_file = None
        self.last_position = 0

        # Initialize pygame mixer
        pygame.mixer.init()

        # Create GUI elements
        self.create_gui()

        # Start slider update thread
        self.slider_update_thread = threading.Thread(target=self.update_slider, daemon=True)
        self.slider_update_thread.start()

    def create_gui(self):
        # Config file buttons frame
        self.config_frame = tk.Frame(self.root)
        self.config_frame.pack(pady=5)

        tk.Button(self.config_frame, text="Create New Config",
                  command=self.create_new_config).pack(side=tk.LEFT, padx=5)
        tk.Button(self.config_frame, text="Load Config",
                  command=self.load_config).pack(side=tk.LEFT, padx=5)

        # Current file label
        self.file_label = tk.Label(self.root, text="No file loaded", wraplength=400)
        self.file_label.pack(pady=5)

        # Playback controls
        self.controls_frame = tk.Frame(self.root)
        self.controls_frame.pack(pady=5)

        tk.Button(self.controls_frame, text="Play/Pause", command=self.toggle_playback).pack(side=tk.LEFT, padx=5)
        tk.Button(self.controls_frame, text="Mark Point", command=self.mark_point).pack(side=tk.LEFT, padx=5)

        # Add backward/forward buttons
        tk.Button(self.controls_frame, text="← 5s", command=lambda: self.seek_relative(-5)).pack(side=tk.LEFT, padx=5)
        tk.Button(self.controls_frame, text="5s →", command=lambda: self.seek_relative(5)).pack(side=tk.LEFT, padx=5)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = tk.Scale(self.root, variable=self.progress_var, from_=0, to=100,
                                     orient=tk.HORIZONTAL, length=400, command=self.seek)
        self.progress_bar.pack(pady=5, padx=10, fill=tk.X)

        # Current time label
        self.time_label = tk.Label(self.root, text="00:00 / 00:00")
        self.time_label.pack(pady=5)

        # Bind mouse events for better seeking control
        self.progress_bar.bind("<Button-1>", lambda e: setattr(self, 'is_seeking', True))
        self.progress_bar.bind("<ButtonRelease-1>", self.on_seek_release)

        # Split points frame
        self.points_frame = tk.Frame(self.root)
        self.points_frame.pack(pady=5, padx=10, fill=tk.X)

        # Split points label
        tk.Label(self.points_frame, text="Split Points:").pack(anchor=tk.W)

        # Split points listbox
        self.points_listbox = tk.Listbox(self.points_frame, height=6)
        self.points_listbox.pack(fill=tk.X)

        # Buttons frame
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=5)

        tk.Button(self.buttons_frame, text="Remove Selected Point",
                  command=self.remove_point).pack(side=tk.LEFT, padx=5)
        tk.Button(self.buttons_frame, text="Split Audio",
                  command=self.split_audio).pack(side=tk.LEFT, padx=5)

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_new_config(self):
        """Create a new configuration file with all necessary paths"""
        # Get audio file
        audio_file = filedialog.askopenfilename(
            title="Select Input Audio File",
            filetypes=[("Audio Files", "*.mp3 *.wav")])
        if not audio_file:
            return

        # Get output directory
        output_dir = filedialog.askdirectory(title="Select Output Directory for WAV Segments")
        if not output_dir:
            return

        # Get metadata file location
        metadata_file = filedialog.asksaveasfilename(
            title="Select Metadata CSV File Location",
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")])
        if not metadata_file:
            return

        # Create initial config with default start_segment_number
        config = {
            "input_audio_file": audio_file,
            "output_directory": output_dir,
            "metadata_file": metadata_file,
            "split_points": [],
            "last_position": 0,
            "start_segment_number": 1  # Default value
        }

        # Get starting segment number from user
        start_number = tk.simpledialog.askinteger("Starting Segment Number",
                                                  "Enter the starting segment number:", initialvalue=1, minvalue=1)
        if start_number:
            config["start_segment_number"] = start_number

        # Get config save location
        config_file = filedialog.asksaveasfilename(
            title="Save Config File",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")])
        if not config_file:
            return

        # Save config
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=4)

        self.config_file = config_file
        self.load_config_file(config_file)

    def load_config(self):
        """Load an existing configuration file"""
        config_file = filedialog.askopenfilename(
            title="Select Config File",
            filetypes=[("JSON Files", "*.json")])
        if config_file:
            self.config_file = config_file
            self.load_config_file(config_file)

    def load_config_file(self, config_file):
        """Load settings from config file and initialize audio"""
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.audio_file = config["input_audio_file"]
        self.output_dir = config["output_directory"]
        self.metadata_file = config["metadata_file"]
        self.split_points = config["split_points"]

        # Set initial position
        if self.split_points:
            self.current_position = max(self.split_points)
        else:
            self.current_position = config.get("last_position", 0)

        self.last_position = self.current_position

        # Update file label
        self.file_label.config(text=f"Current file: {os.path.basename(self.audio_file)}")

        # Load audio file
        if os.path.exists(self.audio_file):
            self.load_audio_file()
            self.update_points_display()

            # Set position without starting playback
            self.progress_var.set(self.current_position)
            self.playing = False  # Ensure playback is off
        else:
            messagebox.showerror("Error", "Audio file not found!")

    def format_time(self, seconds):
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def update_time_label(self):
        """Update the time label with current/total duration"""
        if hasattr(self, 'duration'):
            current = self.progress_var.get()
            self.time_label.config(text=f"{self.format_time(current)} / {self.format_time(self.duration)}")

    def update_slider(self):
        """Continuously update slider position"""
        while True:
            if self.playing and not self.is_seeking and pygame.mixer.music.get_busy():
                # Get the actual current time from pygame
                current_time = pygame.mixer.music.get_pos() / 1000
                if current_time > 0:  # Only update if we have a valid position
                    real_position = self.current_position + current_time
                    self.progress_var.set(real_position)
                    self.update_time_label()
            time.sleep(0.1)  # Update every 100ms

    def seek_relative(self, seconds):
        if not self.audio_file:
            return

        current_pos = self.progress_var.get()
        new_pos = max(0, min(self.duration, current_pos + seconds))
        self.progress_var.set(new_pos)
        self.seek(new_pos)

    def on_seek_release(self, event):
        self.is_seeking = False
        self.seek(self.progress_var.get())

    def load_audio_file(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.music.load(self.audio_file)
        self.audio = AudioSegment.from_file(self.audio_file)
        self.duration = len(self.audio) / 1000  # Duration in seconds
        self.progress_bar.config(to=self.duration)
        self.update_time_label()

    def toggle_playback(self):
        if not self.audio_file:
            return

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.playing = False
            # Store current position when pausing
            current_time = pygame.mixer.music.get_pos() / 1000
            if current_time > 0:
                self.current_position = self.current_position + current_time
        else:
            pygame.mixer.music.play(start=self.current_position)
            self.playing = True

    def mark_point(self):
        if not self.audio_file:
            return

        # Get exact current time from slider
        current_time = self.progress_var.get()
        current_time = round(current_time, 3)  # Round to 3 decimal places

        # Don't add duplicate points
        if self.split_points and abs(current_time - self.split_points[-1]) < 0.1:
            return

        # Add point to list and display
        self.split_points.append(current_time)
        self.split_points.sort()
        self.update_points_display()

        print(f"Marked point at: {current_time} seconds")  # Debug info

        # Save state
        self.save_current_state()

    def update_points_display(self):
        self.points_listbox.delete(0, tk.END)
        for point in self.split_points:
            self.points_listbox.insert(tk.END, self.format_time(point))

    def remove_point(self):
        selection = self.points_listbox.curselection()
        if selection:
            index = selection[0]
            self.split_points.pop(index)
            self.update_points_display()

            # Update current position
            if self.split_points:
                self.current_position = max(self.split_points)

            self.save_current_state()

    def seek(self, value):
        if not self.audio_file or (not self.playing and not self.is_seeking):
            return

        position = float(value)
        pygame.mixer.music.stop()
        self.current_position = position  # Update current_position
        pygame.mixer.music.play(start=position)
        self.update_time_label()
        self.save_current_state()

    def save_current_state(self):
        """Save current state to config file"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            config["split_points"] = self.split_points
            config["last_position"] = max(self.split_points) if self.split_points else self.current_position

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)

    def on_closing(self):
        """Handle window closing"""
        self.save_current_state()
        self.root.destroy()

    def get_next_segment_number(self):
        with open(self.config_file, 'r') as f:
            config = json.load(f)

        # First time use the config's start number if available
        if not has_files(self.output_dir):
            if 'start_segment_number' in config:
                self.first_run = True
                return config['start_segment_number']

        # Otherwise use existing file detection logic
        existing_files = glob.glob(os.path.join(self.output_dir, "segment_*.wav"))
        if not existing_files:
            return 1

        numbers = []
        for file in existing_files:
            try:
                num = int(os.path.basename(file).split('_')[1].split('.')[0])
                numbers.append(num)
            except (ValueError, IndexError):
                continue

        return max(numbers) + 1 if numbers else 1

    def split_audio(self):
        if not self.audio_file or not self.split_points:
            messagebox.showerror("Error", "Please load an audio file and mark split points first")
            return

        try:
            # Get starting segment number
            start_number = self.get_next_segment_number()
            print("start_number: ", start_number)

            # Prepare metadata list
            metadata = []

            # Add 0 as the starting point and get all segments
            points_t = [0] + self.split_points
            print("Split points_t:", points_t)  # Debug info

            points = points_t[points_t.index(self.last_position):]

            print("Split points:", points)  # Debug info

            # Split audio file into segments
            for i in range(len(points) - 1):
                start_time = int(points[i] * 1000)  # Convert to milliseconds
                end_time = int(points[i + 1] * 1000)

                print(f"Splitting segment {i + 1}: {start_time}ms to {end_time}ms")  # Debug info

                # Extract segment
                segment = self.audio[start_time:end_time]

                # Convert to mono if stereo
                if segment.channels > 1:
                    segment = segment.set_channels(1)

                # Set sample rate and bit depth
                segment = segment.set_frame_rate(22050)
                segment = segment.set_sample_width(2)  # 16-bit

                # Generate output filename
                segment_number = start_number + i
                output_filename = f"segment_{segment_number}.wav"
                output_path = os.path.join(self.output_dir, output_filename)

                # Export segment
                segment.export(
                    output_path,
                    format="wav",
                    parameters=[
                        "-ar", "22050",  # Sample rate
                        "-ac", "1",  # Mono
                        "-acodec", "pcm_s16le"  # 16-bit PCM
                    ]
                )

                print(f"Exported: {output_filename}")  # Debug info

                # Add to metadata
                metadata.append([output_filename])

            # Append to metadata file
            file_exists = os.path.exists(self.metadata_file)
            with open(self.metadata_file, 'a', newline='') as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(['filename'])  # Add header if it's a new file
                writer.writerows(metadata)

            num_segments = len(metadata)
            messagebox.showinfo("Success", f"Audio file has been split into {num_segments} segments successfully!")

        except Exception as e:
            print(f"Error during splitting: {str(e)}")  # Debug info
            messagebox.showerror("Error", f"An error occurred while splitting: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSplitter(root)
    root.mainloop()