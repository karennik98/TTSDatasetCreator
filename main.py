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
from docx import Document

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
        self.text_selections = {}  # Add this to store text selections for each point
        self.current_mark_time = None  # To track which point we're selecting text for
        self.sentences = []  # Store split sentences
        self.current_sentence_index = 0  # Track current sentence index
        self.text_selections = {}  # Initialize text selections dictionary

        # Bind hotkeys
        self.root.bind('<space>', lambda e: self.toggle_playback())
        self.root.bind('<Return>', lambda e: self.mark_point())

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

        tk.Button(self.controls_frame, text="Play/Pause (Space)",
                  command=self.toggle_playback).pack(side=tk.LEFT, padx=5)
        tk.Button(self.controls_frame, text="Mark Point (Enter)",
                  command=self.mark_point).pack(side=tk.LEFT, padx=5)

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

        self.status_label = tk.Label(self.root, text="", wraplength=400)
        self.status_label.pack(pady=5)

        # Buttons frame
        self.buttons_frame = tk.Frame(self.root)
        self.buttons_frame.pack(pady=5)

        tk.Button(self.buttons_frame, text="Remove Selected Point",
                  command=self.remove_point).pack(side=tk.LEFT, padx=5)
        tk.Button(self.buttons_frame, text="Split Audio",
                  command=self.split_audio).pack(side=tk.LEFT, padx=5)

        # Text content frame
        self.text_frame = tk.Frame(self.root)
        self.text_frame.pack(pady=5, padx=10, fill=tk.BOTH, expand=True)

        # Text content label
        tk.Label(self.text_frame, text="Document Text:").pack(anchor=tk.W)

        # Text widget with scrollbar
        self.text_scroll = tk.Scrollbar(self.text_frame)
        self.text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(self.text_frame, height=10,
                                   yscrollcommand=self.text_scroll.set)
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.text_scroll.config(command=self.text_widget.yview)

        # Store selected text for current point
        self.current_text_selection = None

        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)


    def update_status(self, message):
        self.status_label.config(text=message)
        self.root.update()

    def load_document(self, doc_file=None):
        """Load text from doc/docx file and split by ':'"""
        if doc_file is None:
            doc_file = filedialog.askopenfilename(
                title="Select Document File",
                filetypes=[("Word Documents", "*.doc *.docx")])
            if not doc_file:
                return

        try:
            # Get starting number from config
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            start_number = config.get('start_segment_number', 1)  # Get start number, default to 1

            doc = Document(doc_file)
            # Extract and concatenate all text
            full_text = ' '.join([paragraph.text for paragraph in doc.paragraphs])

            # Split by ':' and clean sentences
            self.sentences = [sent.strip() for sent in full_text.split('։') if sent.strip()]

            # Clear and update text widget
            self.text_widget.delete('1.0', tk.END)

            # Display sentences starting from config number
            for i, sentence in enumerate(self.sentences, start=start_number):
                self.text_widget.insert(tk.END, f"{i}. {sentence}\n\n")

            print(f"Loaded {len(self.sentences)} sentences starting from {start_number}")

        except Exception as e:
            messagebox.showerror("Error", f"Failed to load document: {str(e)}")

    def get_selected_text(self):
        """Get selected text from text widget"""
        try:
            return self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:  # No selection
            return None


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

        # Get document file
        document_file = filedialog.askopenfilename(
            title="Select Document File",
            filetypes=[("Word Documents", "*.doc *.docx")])
        if not document_file:
            return

        # Create initial config with document file
        config = {
            "input_audio_file": audio_file,
            "output_directory": output_dir,
            "metadata_file": metadata_file,
            "document_file": document_file,
            "split_points": [],
            "last_position": 0,
            "start_segment_number": 1,
            "current_sentence_index": 0,
            "text_selections": {}
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
            self.highlight_current_sentence()

    def load_config_file(self, config_file):
        """Load settings from config file and initialize audio"""
        with open(config_file, 'r') as f:
            config = json.load(f)

        self.audio_file = config["input_audio_file"]
        self.output_dir = config["output_directory"]
        self.metadata_file = config["metadata_file"]
        self.document_file = config["document_file"]
        self.split_points = config["split_points"]

        # Set initial position
        if self.split_points:
            self.current_position = max(self.split_points)
        else:
            self.current_position = config.get("last_position", 0)

        self.last_position = self.current_position

        # Load the sentence index from config
        self.current_sentence_index = config.get("current_sentence_index", 0)

        print("current_sentence_index: ", self.current_sentence_index)


        # Update file label
        self.file_label.config(text=f"Current file: {os.path.basename(self.audio_file)}")

        # Load audio file
        if os.path.exists(self.audio_file):
            self.load_audio_file()
            self.update_points_display()

            # Set position without starting playback
            self.progress_var.set(self.current_position)
            self.playing = False
        else:
            messagebox.showerror("Error", "Audio file not found!")

        # Load document file
        if os.path.exists(self.document_file):
            self.load_document(self.document_file)
        else:
            messagebox.showerror("Error", "Document file not found!")

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

    def find_silence_point(self, marked_time, window_size=0.5, silence_threshold=-50):
        """
        Find closest silence point within window around marked time.
        window_size: Size of window to check on each side (in seconds)
        silence_threshold: dB threshold for silence detection
        """
        try:
            # Convert time to milliseconds
            mark_ms = int(marked_time * 1000)
            window_ms = int(window_size * 1000)

            # Extract window of audio around marked point
            start_ms = max(0, mark_ms - window_ms)
            end_ms = min(len(self.audio), mark_ms + window_ms)

            audio_segment = self.audio[start_ms:end_ms]

            # Split into small chunks for analysis
            chunk_size = 50  # 50ms chunks
            chunks = [audio_segment[i:i + chunk_size] for i in range(0, len(audio_segment), chunk_size)]

            # Find chunks with silence
            silent_chunks = []
            for i, chunk in enumerate(chunks):
                if chunk.dBFS < silence_threshold:
                    chunk_time = start_ms + (i * chunk_size)
                    silent_chunks.append((chunk_time, chunk.dBFS))

            if silent_chunks:
                # Find longest sequence of silent chunks
                silent_regions = []
                current_region = [silent_chunks[0]]

                for i in range(1, len(silent_chunks)):
                    if silent_chunks[i][0] - silent_chunks[i - 1][0] <= chunk_size:
                        current_region.append(silent_chunks[i])
                    else:
                        if len(current_region) > 1:
                            silent_regions.append(current_region)
                        current_region = [silent_chunks[i]]

                if len(current_region) > 1:
                    silent_regions.append(current_region)

                if silent_regions:
                    # Get the longest silent region
                    longest_region = max(silent_regions, key=len)
                    # Use middle of the longest silent region
                    start_time = longest_region[0][0]
                    end_time = longest_region[-1][0]
                    middle_time = (start_time + end_time) / 2000  # Convert back to seconds

                    print(f"Found silence: original={marked_time:.3f}s, adjusted={middle_time:.3f}s")
                    return middle_time

            print(f"No suitable silence found, using original time: {marked_time:.3f}s")
            return marked_time

        except Exception as e:
            print(f"Error in silence detection: {str(e)}")
            return marked_time

    def mark_point(self, event=None):
        if not self.audio_file:
            return

        # Get exact current time from slider
        current_time = self.progress_var.get()
        current_time = round(current_time, 3)

        # Don't add duplicate points
        if self.split_points and abs(current_time - self.split_points[-1]) < 0.1:
            return

        # First pause audio
        if self.playing:
            self.toggle_playback()

        # Find best split point
        adjusted_time = self.find_silence_point(current_time)

        # Add adjusted point to list and display
        self.split_points.append(adjusted_time)
        self.split_points.sort()
        self.update_points_display()

        # Update current position to the adjusted time
        self.current_position = adjusted_time
        self.progress_var.set(adjusted_time)

        # Associate with current sentence
        if self.current_sentence_index < len(self.sentences):
            self.text_selections[adjusted_time] = self.sentences[self.current_sentence_index]
            self.current_sentence_index += 1

            # Highlight current sentence in text widget
            self.highlight_current_sentence()

            messagebox.showinfo("Marked",
                                f"Point marked at {self.format_time(adjusted_time)} and associated with sentence {self.current_sentence_index}")
        else:
            messagebox.showwarning("Warning", "No more sentences to associate!")

        self.save_current_state()

    def highlight_current_sentence(self):
        """Highlight the current sentence in text widget"""
        self.text_widget.tag_remove('highlight', '1.0', tk.END)

        if self.current_sentence_index < len(self.sentences):
            # Get starting number from config
            with open(self.config_file, 'r') as f:
                config = json.load(f)
            start_number = config.get('start_segment_number', 1)

            # Calculate actual sentence number
            display_number = start_number + self.current_sentence_index

            # Search for the sentence in text widget
            start = '1.0'
            while True:
                pos = self.text_widget.search(f"{display_number}. ", start, tk.END)
                if not pos:
                    break
                line_end = self.text_widget.index(f"{pos} lineend")
                self.text_widget.tag_add('highlight', pos, line_end)
                break

            # Configure highlight tag
            self.text_widget.tag_config('highlight', background='yellow')

    def save_current_state(self):
        """Save current state to config file"""
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)

            config["split_points"] = self.split_points
            config["last_position"] = max(self.split_points) if self.split_points else self.current_position
            config["current_sentence_index"] = self.current_sentence_index  # Save just the index

            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)

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
            config["current_sentence_index"] = self.current_sentence_index  # Save just the index

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
            start_number = self.get_next_segment_number()
            print("start_number: ", start_number)

            metadata = []
            # Get all points including 0 as start
            all_points = [0] + self.split_points

            # Find the index of the last processed position
            if self.last_position in all_points:
                start_idx = all_points.index(self.last_position)
            else:
                # If last_position isn't in points, find the nearest lower point
                valid_points = [p for p in all_points if p <= self.last_position]
                if valid_points:
                    start_idx = all_points.index(max(valid_points))
                else:
                    start_idx = 0

            # Get only the unprocessed points
            points = all_points[start_idx:]
            print(f"Processing points from index {start_idx}: {points}")

            # Split audio file into segments
            for i in range(len(points) - 1):
                start_time = int(points[i] * 1000)
                end_time = int(points[i + 1] * 1000)

                print(f"Splitting segment {i + 1}: {start_time}ms to {end_time}ms")

                segment = self.audio[start_time:end_time]

                if segment.channels > 1:
                    segment = segment.set_channels(1)

                segment = segment.set_frame_rate(22050)
                segment = segment.set_sample_width(2)

                segment_number = start_number + i
                output_filename = f"segment_{segment_number}.wav"
                output_path = os.path.join(self.output_dir, output_filename)

                segment.export(
                    output_path,
                    format="wav",
                    parameters=[
                        "-ar", "22050",
                        "-ac", "1",
                        "-acodec", "pcm_s16le"
                    ]
                )

                print(f"Exported: {output_filename}")

                # Get the text for this segment - using end point to get text
                end_point = points[i + 1]
                selected_text = self.text_selections.get(end_point, "")

                # Clean the text
                if selected_text:
                    selected_text = selected_text.strip()
                    selected_text = selected_text.replace('|', ' ')

                metadata.append([output_filename, selected_text])

            # Write metadata with proper formatting
            file_exists = os.path.exists(self.metadata_file)
            with open(self.metadata_file, 'a', newline='', encoding='utf-8') as f:
                csv.register_dialect('custom',
                                     delimiter='|',
                                     quoting=csv.QUOTE_MINIMAL,
                                     escapechar='\\',
                                     quotechar='"'
                                     )

                writer = csv.writer(f, dialect='custom')
                if not file_exists:
                    writer.writerow(['filename', 'text'])

                for row in metadata:
                    writer.writerow(row)

            # Update last_position to the last processed point
            self.last_position = points[-1]
            self.save_current_state()  # Save the updated last_position

            num_segments = len(metadata)
            messagebox.showinfo("Success", f"Audio file has been split into {num_segments} segments successfully!")

        except Exception as e:
            print(f"Error during splitting: {str(e)}")
            messagebox.showerror("Error", f"An error occurred while splitting: {str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = AudioSplitter(root)
    root.mainloop()