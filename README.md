# Audio Splitter

A Python application for splitting audio files into segments with precise control and session persistence.

## Features
- Load and split MP3/WAV audio files
- Mark split points during playback
- Save work progress and resume later
- Convert segments to WAV format (22050Hz, 16-bit, mono)
- Track split points and positions between sessions
- Configurable starting segment number
- Continuous segment numbering across sessions

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/audio-splitter.git
cd audio-splitter
```

2. Install required dependencies:
```bash
pip install pygame pydub tk
```

## Usage

### First Time Setup

1. Launch the application:
```bash
python audio_splitter.py
```

2. Click "Create New Config" and follow the prompts:
   - Select input audio file (MP3 or WAV)
   - Choose output directory for segments
   - Select location for metadata CSV file
   - Enter starting segment number (this will be used for first batch of segments)
   - Save your config file (.json)

### Regular Operation

1. Launch the application
2. Click "Load Config" and select your saved config file
3. Use the playback controls:
   - Play/Pause - Start or pause audio playback
   - ← 5s / 5s → - Jump backward or forward
   - Progress slider - Seek to any position
4. Mark split points:
   - Play the audio
   - Click "Mark Point" at desired positions
   - Split points are automatically saved
5. Review split points:
   - All marked points are shown in the list
   - Remove unwanted points using "Remove Selected Point"
6. Split the audio:
   - Click "Split Audio" to create segments
   - Segments are saved as WAV files in your output directory
   - Metadata is updated in the CSV file

### Resuming Work

1. Load your previous config file
2. The application will:
   - Remember all previous split points
   - Resume from last position
   - Continue segment numbering from last segment
   - Maintain your output directory and metadata file

## Output Format

### Audio Segments
- Format: WAV
- Sample Rate: 22050 Hz
- Bit Depth: 16-bit
- Channels: Mono
- Naming: segment_1.wav, segment_2.wav, etc.

### Metadata File
- Format: CSV
- Columns: filename
- Records all segment filenames in order

### Config File
- Format: JSON
- Stores:
  - Input audio file path
  - Output directory path
  - Metadata file path
  - Split points
  - Last position
  - Starting segment number (used only on first run)

## Important Notes

1. First Run:
   - The starting segment number from config is only used when the output directory is empty
   - After first use, segment numbering continues from the last existing segment

2. Split Points:
   - Split points are saved in seconds
   - Displayed in MM:SS format
   - Automatically sorted in chronological order

3. Session Persistence:
   - All marked points are saved automatically
   - Work can be resumed at any time
   - Split operation continues from last position

4. Audio Controls:
   - Audio doesn't start automatically when loading
   - Must use Play button to start playback
   - Can mark points only during playback

## Common Workflows

### Complete Audio File in Multiple Sessions

1. First Session:
   - Create new config
   - Mark first batch of points
   - Split audio
   - Close program

2. Later Sessions:
   - Load same config
   - Continue marking points
   - Split audio again
   - Segments continue numbering from last session

### Correcting Mistakes

1. Remove Wrong Points:
   - Select point in list
   - Click "Remove Selected Point"
   - Points are automatically re-saved

2. Change Split Position:
   - Remove incorrect point
   - Navigate to correct position
   - Mark new point
   - Split audio when ready

## Troubleshooting

1. Audio Not Playing
   - Check if audio file exists at path in config
   - Ensure audio file is MP3 or WAV format
   - Click Play button to start playback

2. Segment Numbers Wrong
   - Check output directory for existing segments
   - Verify start_segment_number in config (first run only)
   - Clear output directory for fresh start

3. Split Points Not Saved
   - Ensure config file is writable
   - Check if split points appear in list
   - Verify config file shows updated points

## Contributing

Feel free to submit issues, fork the repository, and create pull requests for any improvements.