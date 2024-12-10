import os
import shutil
import pandas as pd
from pathlib import Path
import re
import logging
import sys
import json
from datetime import datetime


# Set up logging with UTF-8 encoding
def setup_logging():
    log_filename = f'merge_process_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    # Configure logging to file with UTF-8 encoding
    file_handler = logging.FileHandler(log_filename, 'w', encoding='utf-8')
    file_handler.setLevel(logging.INFO)

    # Configure console output with UTF-8 encoding
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)

    # Set format for both handlers
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def natural_sort_key(s):
    """
    Extract number from directory name for sorting
    Example: 'chapter_1' -> 1, 'chapter_15' -> 15
    """
    numbers = re.findall(r'\d+$', str(s))
    return int(numbers[0]) if numbers else 0


def analyze_duplicates(metadata_dfs):
    """
    Analyze duplicate entries across all metadata files and save detailed report
    """
    all_files = pd.concat(metadata_dfs, ignore_index=True)
    duplicates = all_files[all_files.duplicated(subset=['filename'], keep=False)]

    if not duplicates.empty:
        duplicate_report = []

        # Group duplicates by filename
        for filename in duplicates.filename.unique():
            dupes = duplicates[duplicates.filename == filename]

            duplicate_info = {
                'filename': filename,
                'occurrences': len(dupes),
                'locations': dupes['source_dir'].tolist(),
                'texts': dupes['text'].tolist(),
                'identical_text': len(dupes['text'].unique()) == 1
            }

            duplicate_report.append(duplicate_info)

            # Log detailed information
            logging.info(f"\nDuplicate file: {filename}")
            if duplicate_info['identical_text']:
                logging.info("  All versions have identical text")
            else:
                logging.info("  Different text versions found:")
                for i, text in enumerate(duplicate_info['texts'], 1):
                    logging.info(f"  Version {i}: {text}")
            logging.info(f"  Found in directories: {duplicate_info['locations']}")

        # Save detailed report to JSON
        report_file = 'duplicate_analysis.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(duplicate_report, f, ensure_ascii=False, indent=2)
        logging.info(f"\nDetailed duplicate analysis saved to {report_file}")

        return duplicate_report
    return []


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
    file_origins = {}  # Track where each file comes from

    # Get and sort subdirectories
    subdirs = [d for d in data_path.iterdir() if d.is_dir() and d.name != 'hy_speech' and d.name != "archive"]
    subdirs.sort(key=natural_sort_key)

    for subdir in subdirs:
        logging.info(f"Processing directory: {subdir}")

        metadata_file = subdir / "metadata.csv"
        if metadata_file.exists():
            try:
                df = pd.read_csv(metadata_file, sep='|')
                df['source_dir'] = str(subdir)  # Add source directory information
                metadata_dfs.append(df)

                # Process WAV files
                wav_dir = subdir / "wav"
                if wav_dir.exists():
                    for wav_file in wav_dir.glob("*.wav"):
                        if wav_file.name in processed_files:
                            if wav_file.name in file_origins:
                                logging.warning(f"Duplicate audio file {wav_file.name} found in {subdir}. "
                                                f"Previously seen in {file_origins[wav_file.name]}")
                            continue

                        target_file = wav_output_path / wav_file.name
                        try:
                            shutil.copy2(wav_file, target_file)
                            processed_files.add(wav_file.name)
                            file_origins[wav_file.name] = str(subdir)
                            logging.info(f"Copied {wav_file.name}")
                        except Exception as e:
                            logging.error(f"Error copying {wav_file}: {e}")

            except Exception as e:
                logging.error(f"Error processing directory {subdir}: {e}")
        else:
            logging.warning(f"No metadata.csv found in {subdir}")

    if metadata_dfs:
        try:
            # Analyze duplicates before merging
            duplicate_report = analyze_duplicates(metadata_dfs)

            # Merge metadata, keeping first occurrence of duplicates
            merged_metadata = pd.concat(metadata_dfs, ignore_index=True)
            merged_metadata = merged_metadata.drop_duplicates(subset=['filename'], keep='first')

            # Ensure required columns and values
            if 'speaker' not in merged_metadata.columns:
                merged_metadata['speaker'] = 'narek_barseghyan'
            if 'source' not in merged_metadata.columns:
                merged_metadata['source'] = 'hobbit'

            # Final metadata cleanup
            merged_metadata = merged_metadata[['speaker', 'source', 'filename', 'text']]

            # Save final metadata
            metadata_output_path = hy_speech_path / "metadata.csv"
            merged_metadata.to_csv(metadata_output_path, sep='|', index=False, encoding='utf-8')
            logging.info(f"\nMerged metadata saved to {metadata_output_path}")
            logging.info(f"Total audio files processed: {len(processed_files)}")
            logging.info(f"Total metadata entries: {len(merged_metadata)}")

        except Exception as e:
            logging.error(f"Error merging metadata: {e}")
    else:
        logging.error("No metadata files found")


if __name__ == "__main__":
    source_dir = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\data"
    setup_logging()  # Initialize logging with UTF-8 support
    merge_audio_and_metadata(source_dir)