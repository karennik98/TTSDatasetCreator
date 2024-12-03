import os
import shutil
import pandas as pd
from pathlib import Path
import re


def natural_sort_key(s):
    """
    Extract number from directory name for sorting
    Example: 'chapter_1' -> 1, 'chapter_15' -> 15
    """
    numbers = re.findall(r'\d+$', str(s))
    return int(numbers[0]) if numbers else 0


def merge_audio_and_metadata(data_dir):
    """
    Merge all WAV files and metadata.csv files from subdirectories into a single directory.
    Process directories in numerical order and keep original filenames.

    Args:
        data_dir (str): Path to the root data directory
    """
    # Convert input path to Path object
    data_path = Path(data_dir)

    # Create hy_speech directory and its subdirectories
    hy_speech_path = data_path / "hy_speech"
    wav_output_path = hy_speech_path / "wav"
    os.makedirs(wav_output_path, exist_ok=True)

    # Initialize an empty list to store all metadata DataFrames
    metadata_dfs = []

    # Get all immediate subdirectories and sort them by their ending number
    subdirs = [d for d in data_path.iterdir() if d.is_dir() and d.name != 'hy_speech' and d.name != "archive"]
    subdirs.sort(key=natural_sort_key)

    # Process each subdirectory in order
    for subdir in subdirs:
        print(f"Processing directory: {subdir}")

        # Process WAV files
        wav_dir = subdir / "wav"
        if wav_dir.exists():
            wav_files = sorted(wav_dir.glob("*.wav"), key=lambda x: natural_sort_key(x.stem))
            for wav_file in wav_files:
                # Keep the original filename
                target_file = wav_output_path / wav_file.name

                try:
                    shutil.copy2(wav_file, target_file)
                    print(f"Copied {wav_file} to {target_file}")
                except Exception as e:
                    print(f"Error copying {wav_file}: {e}")

        # Process metadata.csv file
        metadata_file = subdir / "metadata.csv"
        if metadata_file.exists():
            try:
                df = pd.read_csv(metadata_file, sep='|')
                metadata_dfs.append(df)
            except Exception as e:
                print(f"Error reading metadata from {metadata_file}: {e}")

    # Merge all metadata DataFrames and save
    if metadata_dfs:
        try:
            merged_metadata = pd.concat(metadata_dfs, ignore_index=True)

            # Add speaker and source columns
            merged_metadata['speaker'] = 'narek_barseghyan'
            merged_metadata['source'] = 'hobbit'

            # Reorder columns to match desired format
            merged_metadata = merged_metadata[['speaker', 'source', 'filename', 'text']]

            # Save with pipe separator, maintaining format
            metadata_output_path = hy_speech_path / "metadata.csv"
            merged_metadata.to_csv(metadata_output_path, sep='|', index=False)
            print(f"Merged metadata saved to {metadata_output_path}")
        except Exception as e:
            print(f"Error merging metadata: {e}")
    else:
        print("No metadata files found")

if __name__ == "__main__":
    source_dir = "/home/karen/PhD/TTSDatasetCreator/data"
    merge_audio_and_metadata(source_dir)