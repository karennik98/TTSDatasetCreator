# Audio Splitter with Text Association and Intelligent Marking

A Python application for splitting audio files with intelligent silence detection and text association.

## Features

### Core Features
- Load and split MP3/WAV audio files
- Load and parse DOCX files by sentences (split by ":")
- Mark split points with intelligent silence detection
- Automatic text-to-audio segment association
- Save/resume work progress via config file

### Intelligent Marking System
- Automatically finds optimal split points
- Analyzes ±1 second around marked position
- Detects silence regions
- Places split points in middle of silence
- Falls back to manual position if no silence found

### Audio Processing
- Converts segments to WAV (22050Hz, 16-bit, mono)
- Configurable silence detection threshold
- Maintains continuous segment numbering
- Tracks split positions between sessions

### Hotkeys
- Space: Play/Pause
- Enter: Mark Point (with intelligent positioning)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/audio-splitter.git
cd audio-splitter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Initial Setup
1. Launch the application
2. Click "Create New Config"
3. Select required files:
   - Input audio (MP3/WAV)
   - Output directory
   - Metadata CSV location
   - Word document (.docx)
4. Enter starting segment number

### Working Process
1. Document is split by ":" into sentences
2. Play audio (Space)
3. When ready to split:
   - Press Enter or click "Mark Point"
   - System analyzes audio around marked position
   - Finds optimal split point in silence region
   - Automatically associates with next sentence
4. Continue playing (Space)
5. Repeat mark/associate process

### Intelligent Marking
The system:
1. Checks marked point for silence
2. If not silent:
   - Analyzes ±1 second window
   - Finds silence regions
   - Uses middle of longest silence
3. If no silence found:
   - Uses original marked point
4. Continues playback from adjusted position

### Output Files
1. Audio Segments:
   - WAV format
   - 22050 Hz sample rate
   - 16-bit depth
   - Mono channel
   - Named: segment_1.wav, segment_2.wav, etc.

2. Metadata File:
```
filename|text
segment_1.wav|First sentence text
segment_2.wav|Second sentence text
```

## Configuration

### Config File Structure
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

## Technical Notes

### Silence Detection Parameters
- Window Size: ±1 second around marked point
- Chunk Size: 50ms for analysis
- Default Silence Threshold: -50dB
- Adjustable through code configuration

### Performance Considerations
- Real-time analysis of audio segments
- Efficient chunk-based processing
- Fallback mechanism for non-silent sections