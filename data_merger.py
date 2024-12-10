import os
import shutil
import pandas as pd
from pathlib import Path
import re
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('merge_process.log'),
        logging.StreamHandler()
    ]
)


def natural_sort_key(s):
    """
    Extract number from directory name for sorting
    Example: 'chapter_1' -> 1, 'chapter_15' -> 15
    """
    numbers = re.findall(r'\d+$', str(s))
    return int(numbers[0]) if numbers else 0


def validate_metadata(df, subdir):
    """
    Validate metadata DataFrame and ensure all required columns are present
    """
    required_columns = ['filename', 'text']
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        logging.error(f"Missing required columns in {subdir}: {missing_columns}")
        return False

    return True


def merge_audio_and_metadata(data_dir):
    """
    Merge all WAV files and metadata.csv files from subdirectories into a single directory.
    Process directories in numerical order and keep original filenames.

    Args:
        data_dir (str): Path to the root data directory
    """
    data_path = Path(data_dir)
    hy_speech_path = data_path / "hy_speech"
    wav_output_path = hy_speech_path / "wav"
    os.makedirs(wav_output_path, exist_ok=True)

    metadata_dfs = []
    processed_files = set()
    missing_audio_files = []

    # Get and sort subdirectories
    subdirs = [d for d in data_path.iterdir() if d.is_dir() and d.name != 'hy_speech' and d.name != "archive"]
    subdirs.sort(key=natural_sort_key)

    for subdir in subdirs:
        logging.info(f"Processing directory: {subdir}")

        # Process metadata.csv first to get expected files
        metadata_file = subdir / "metadata.csv"
        if metadata_file.exists():
            try:
                df = pd.read_csv(metadata_file, sep='|')
                if not validate_metadata(df, subdir):
                    continue

                # Store original filenames before processing
                expected_files = set(df['filename'].values)

                # Add speaker and source if missing
                if 'speaker' not in df.columns:
                    df['speaker'] = 'narek_barseghyan'
                if 'source' not in df.columns:
                    df['source'] = 'hobbit'

                metadata_dfs.append(df)

                # Process WAV files
                wav_dir = subdir / "wav"
                if wav_dir.exists():
                    wav_files = set(f.name for f in wav_dir.glob("*.wav"))

                    # Check for missing audio files
                    missing = expected_files - wav_files
                    if missing:
                        missing_audio_files.extend([(subdir, f) for f in missing])

                    for wav_file in wav_dir.glob("*.wav"):
                        if wav_file.name in processed_files:
                            logging.warning(f"Duplicate audio file found: {wav_file.name}")
                            continue

                        target_file = wav_output_path / wav_file.name
                        try:
                            shutil.copy2(wav_file, target_file)
                            processed_files.add(wav_file.name)
                            logging.info(f"Copied {wav_file} to {target_file}")
                        except Exception as e:
                            logging.error(f"Error copying {wav_file}: {e}")

            except Exception as e:
                logging.error(f"Error processing directory {subdir}: {e}")
        else:
            logging.warning(f"No metadata.csv found in {subdir}")

    if metadata_dfs:
        try:
            merged_metadata = pd.concat(metadata_dfs, ignore_index=True)

            # Validate final metadata
            missing_speaker = merged_metadata['speaker'] != 'narek_barseghyan'
            missing_source = merged_metadata['source'] != 'hobbit'

            if missing_speaker.any() or missing_source.any():
                logging.warning(f"Found {missing_speaker.sum()} rows with incorrect speaker")
                logging.warning(f"Found {missing_source.sum()} rows with incorrect source")

                # Fix missing values
                merged_metadata.loc[missing_speaker, 'speaker'] = 'narek_barseghyan'
                merged_metadata.loc[missing_source, 'source'] = 'hobbit'

            # Ensure all columns are present and in correct order
            merged_metadata = merged_metadata[['speaker', 'source', 'filename', 'text']]

            # Remove duplicates
            duplicates = merged_metadata.duplicated(subset=['filename'], keep='first')
            if duplicates.any():
                logging.warning(f"Found {duplicates.sum()} duplicate entries in metadata")
                merged_metadata = merged_metadata[~duplicates]

            # Save metadata
            metadata_output_path = hy_speech_path / "metadata.csv"
            merged_metadata.to_csv(metadata_output_path, sep='|', index=False)
            logging.info(f"Merged metadata saved to {metadata_output_path}")

            # Final validation report
            logging.info(f"Total audio files processed: {len(processed_files)}")
            logging.info(f"Total metadata entries: {len(merged_metadata)}")

            if missing_audio_files:
                logging.error("Missing audio files:")
                for subdir, filename in missing_audio_files:
                    logging.error(f"  {subdir} -> {filename}")

        except Exception as e:
            logging.error(f"Error merging metadata: {e}")
    else:
        logging.error("No metadata files found")


if __name__ == "__main__":
    source_dir = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\data"
    merge_audio_and_metadata(source_dir)