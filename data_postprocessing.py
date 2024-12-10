import os
import pandas as pd
from pydub import AudioSegment
from pydub.silence import detect_silence
import shutil
import csv
from datetime import datetime


def process_audio_files(wav_dir, metadata_path, durations_path):
    """
    Process audio files according to duration requirements and update metadata

    Parameters:
    wav_dir (str): Directory containing WAV files
    metadata_path (str): Path to metadata CSV file
    durations_path (str): Path to file_durations.csv
    """
    # Read duration information
    durations_df = pd.read_csv(durations_path)
    durations_dict = dict(zip(durations_df['file'], durations_df['duration']))

    # Read metadata
    metadata_df = pd.read_csv(metadata_path, sep='|')

    # Initialize changes log
    changes = []
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Step 1: Remove files shorter than 1 second
    short_files = {file: duration for file, duration in durations_dict.items()
                   if duration < 1.0}

    for file in short_files:
        file_path = os.path.join(wav_dir, file)
        if os.path.exists(file_path):
            # Remove wav file
            os.remove(file_path)
            # Log the change
            changes.append({
                'timestamp': current_time,
                'action': 'deleted_short',
                'file': file,
                'duration': short_files[file]
            })

    # Update metadata by removing entries for deleted files
    metadata_df = metadata_df[~metadata_df['filename'].isin(short_files.keys())]

    # Step 2: Process files longer than 16 seconds
    long_files = {file: duration for file, duration in durations_dict.items()
                  if duration >= 16.0}

    for file in long_files:
        file_path = os.path.join(wav_dir, file)
        if os.path.exists(file_path):
            # Load audio file
            audio = AudioSegment.from_wav(file_path)

            # Detect silence regions (min_silence_len=500ms, silence_thresh=-40dBFS)
            silence_ranges = detect_silence(audio, min_silence_len=500, silence_thresh=-40)

            if silence_ranges:
                # Find the longest silence region
                longest_silence = max(silence_ranges, key=lambda x: x[1] - x[0])
                split_point = (longest_silence[0] + longest_silence[1]) // 2

                # Split audio
                first_part = audio[:split_point]
                second_part = audio[split_point:]

                # Generate new filenames
                filename_without_ext = os.path.splitext(file)[0]
                new_file1 = f"{filename_without_ext}_1.wav"
                new_file2 = f"{filename_without_ext}_2.wav"

                # Save new files
                first_part.export(os.path.join(wav_dir, new_file1), format="wav")
                second_part.export(os.path.join(wav_dir, new_file2), format="wav")

                # Remove original file
                os.remove(file_path)

                # Update metadata for split files
                original_metadata = metadata_df[metadata_df['filename'] == file].iloc[0].to_dict()

                # Create two new rows for split files
                new_row1 = original_metadata.copy()
                new_row2 = original_metadata.copy()
                new_row1['filename'] = new_file1
                new_row2['filename'] = new_file2

                # Remove original row and add new rows
                metadata_df = metadata_df[metadata_df['filename'] != file]
                metadata_df = pd.concat([
                    metadata_df,
                    pd.DataFrame([new_row1, new_row2])
                ], ignore_index=True)

                # Log the changes
                changes.append({
                    'timestamp': current_time,
                    'action': 'split_long',
                    'file': file,
                    'new_file1': new_file1,
                    'new_file2': new_file2,
                    'split_point_ms': split_point
                })

    # Save updated metadata
    metadata_df.to_csv(metadata_path, sep='|', index=False)

    # Save changes log
    changes_df = pd.DataFrame(changes)
    changes_df.to_csv('changes.csv', index=False)

if __name__ == "__main__":
    # import argparse
    #
    # parser = argparse.ArgumentParser(description='Process audio files based on duration.')
    # parser.add_argument('wav_dir', help='Directory containing WAV files')
    # parser.add_argument('metadata_path', help='Path to metadata CSV file')
    # parser.add_argument('durations_path', help='Path to file_durations.csv')
    #
    # args = parser.parse_args()

    wav_dir = "/home/karen/PhD/TTSDatasetCreator/data/hy_speech/wav"
    metadata_path = "/home/karen/PhD/TTSDatasetCreator/data/hy_speech/metadata.csv"
    durations_path = "/home/karen/PhD/TTSDatasetCreator/data/hy_speech/characteristics/file_durations.csv"

    process_audio_files(wav_dir, metadata_path, durations_path)