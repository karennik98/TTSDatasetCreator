import tkinter as tk
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


class AudioSplitter:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Splitter")

        # Initialize variables
        self.audio_file = None
        self.split_points = []
        self.playing = False
        self.current_position = 0
        self.is_seeking = False

        # State file for saving positions
        self.state_file = 'audio_state.json'
        self.load_state()

        # Initialize pygame mixer
        pygame.mixer.init()

        # Create GUI elements
        self.create_gui()

        # Start slider update thread
        self.slider_update_thread = threading.Thread(target=self.update_slider, daemon=True)
        self.slider_update_thread.start()

    def load_state(self):
        """Load saved state from JSON file"""
        self.state = {}
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    self.state = json.load(f)
            except:
                self.state = {}

    def save_state(self):
        """Save current state to JSON file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f)
        except:
            pass

    def create_gui(self):
        # File selection
        tk.Button(self.root, text="Select Audio File", command=self.load_audio).pack(pady=5)

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

        # Split points listbox
        self.points_listbox = tk.Listbox(self.root, height=6)
        self.points_listbox.pack(pady=5, fill=tk.X, padx=10)

        # Buttons frame
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=5)

        tk.Button(self.buttons_frame, text="Remove Selected Point",
                  command=self.remove_point).pack(side=tk.LEFT, padx=5)
        tk.Button(self.buttons_frame, text="Split Audio",
                  command=self.split_audio).pack(side=tk.LEFT, padx=5)

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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
                current_time = pygame.mixer.music.get_pos() / 1000 + self.current_position
                self.progress_var.set(current_time)
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

    def load_audio(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav")])
        if file_path:
            self.audio_file = file_path
            self.load_audio_file()

    def load_audio_file(self):
        if pygame.mixer.music.get_busy():
            pygame.mixer.music.stop()

        pygame.mixer.music.load(self.audio_file)
        self.audio = AudioSegment.from_file(self.audio_file)
        self.duration = len(self.audio) / 1000  # Duration in seconds
        self.progress_bar.config(to=self.duration)

        # Load saved state for this file
        file_key = os.path.basename(self.audio_file)
        if file_key in self.state:
            saved_state = self.state[file_key]
            self.current_position = saved_state.get('position', 0)
            self.split_points = saved_state.get('split_points', [])
            self.progress_var.set(self.current_position)
            self.update_points_display()

            # Start playback from saved position
            pygame.mixer.music.play(start=self.current_position)
            self.playing = True
        else:
            self.current_position = 0
            self.split_points = []

        self.update_time_label()

    def toggle_playback(self):
        if not self.audio_file:
            return

        if pygame.mixer.music.get_busy():
            pygame.mixer.music.pause()
            self.playing = False
        else:
            pygame.mixer.music.unpause() if pygame.mixer.music.get_pos() > 0 else pygame.mixer.music.play(
                start=self.current_position)
            self.playing = True

    def mark_point(self):
        if not self.audio_file:
            return

        current_time = self.progress_var.get()

        # Add point to list and display
        self.split_points.append(current_time)
        self.split_points.sort()
        self.update_points_display()

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
            self.save_current_state()

    def seek(self, value):
        if not self.audio_file or (not self.playing and not self.is_seeking):
            return

        position = float(value)
        pygame.mixer.music.stop()
        pygame.mixer.music.play(start=position)
        self.current_position = position
        self.update_time_label()

        # Save state
        self.save_current_state()

    def save_current_state(self):
        """Save current position and split points for this file"""
        if self.audio_file:
            file_key = os.path.basename(self.audio_file)
            self.state[file_key] = {
                'position': self.current_position,
                'split_points': self.split_points
            }
            self.save_state()

    def on_closing(self):
        """Handle window closing"""
        self.save_current_state()
        self.root.destroy()

    def get_next_segment_number(self, output_dir):
        # Find existing segment files
        existing_files = glob.glob(os.path.join(output_dir, "segment_*.wav"))
        if not existing_files:
            return 1

        # Extract numbers from existing files
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

        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return

        # Add start and end points
        points = [0] + self.split_points + [self.duration]

        # Get base filename for metadata
        base_audio_name = os.path.splitext(os.path.basename(self.audio_file))[0]
        metadata_file = os.path.join(output_dir, f"metadata_{base_audio_name}.csv")

        # Get starting segment number
        start_number = self.get_next_segment_number(output_dir)

        # Prepare metadata list
        metadata = []

        # Split audio file
        for i in range(len(points) - 1):
            start_time = int(points[i] * 1000)  # Convert to milliseconds
            end_time = int(points[i + 1] * 1000)

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
            output_path = os.path.join(output_dir, output_filename)

            # Export segment
            segment.export(output_path, format="wav")

            # Add to metadata
            metadata.append([output_filename])

        # Append to metadata file
        file_exists = os.path.exists(metadata_file)
        with open(metadata_file, 'a', newline='') as f:
            writer = csv.writer(f)
            # If file doesn't exist, we might want to add a header
            if not file_exists:
                writer.writerow(['filename'])  # Add header if it's a new file
            writer.writerows(metadata)

        messagebox.showinfo("Success", "Audio file has been split successfully!")


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSplitter(root)
    root.mainloop()