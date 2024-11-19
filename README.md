# Audio Splitter with Text Association

A Python application for splitting audio files and associating segments with text from a Word document. Designed for creating paired audio-text segments, particularly useful for speech datasets or transcription projects.

## Features

- Load and split MP3/WAV audio files
- Load and parse DOCX files by sentences (split by ":")
- Mark split points during audio playback
- Automatic text-to-audio segment association
- Convert segments to WAV format (22050Hz, 16-bit, mono)
- Save/resume work progress via config file
- Track split points and positions between sessions
- Configurable starting segment number
- Hotkeys for main controls

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/audio-splitter.git
cd audio-splitter
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Hotkeys
- `Space`: Play/Pause audio
- `Enter`: Mark split point

### First Time Setup

1. Launch the application:
```bash
python audio_splitter.py
```

2. Click "Create New Config" and select:
   - Input audio file (MP3 or WAV)
   - Output directory for segments
   - Metadata CSV file location
   - Word document (.docx)
   - Enter starting segment number

### Working Process

1. **Document Processing**:
   - Document text is automatically split by ":" character
   - Sentences are displayed as numbered list
   - Current sentence is highlighted

2. **Audio Marking**:
   - Play audio (Space)
   - Navigate to split point
   - Mark point (Enter)
   - System automatically associates marked point with current sentence
   - Repeat for all sentences

3. **Creating Segments**:
   - Click "Split Audio" when done marking
   - Program creates:
     * WAV segments in output directory
     * Metadata CSV with filename|text pairs

### Resuming Work

1. Click "Load Config"
2. Select previous config file
3. Program resumes:
   - Shows document with sentences
   - Highlights next sentence
   - Positions audio at last split point
   - Maintains split point history

### Output Files

1. Audio Segments:
   - Format: WAV
   - Sample Rate: 22050 Hz
   - Bit Depth: 16-bit
   - Channels: Mono
   - Naming: segment_1.wav, segment_2.wav, etc.

2. Metadata File (CSV):
   - Format: filename|text
   - Example:
     ```
     filename|text
     segment_1.wav|First sentence text
     segment_2.wav|Second sentence text
     ```

## Config File Structure

```json
{
    "input_audio_file": "path/to/audio.mp3",
    "output_directory": "path/to/output/dir",
    "metadata_file": "path/to/metadata.csv",
    "document_file": "path/to/document.docx",
    "split_points": [],
    "last_position": 0,
    "start_segment_number": 1,
    "current_sentence_index": 0
}
```

## Requirements

See requirements.txt for detailed dependencies.
- Python 3.9+
- pygame
- pydub
- python-docx
- tkinter (usually comes with Python)

## Notes

- Input text documents should use ":" as sentence delimiter
- Program automatically tracks last position between sessions
- Split points are saved automatically
- Segments are numbered continuously across sessions