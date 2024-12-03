import os
from pathlib import Path
import wave
import numpy as np
from datetime import timedelta
import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter


def get_wav_duration(wav_path):
    """Calculate the duration of a wav file in seconds."""
    with wave.open(str(wav_path), 'rb') as wav_file:
        frames = wav_file.getnframes()
        rate = wav_file.getframerate()
        duration = frames / float(rate)
        return duration


def analyze_wav_files(directory):
    """
    Analyze WAV files in the given directory and generate statistics.

    Args:
        directory (str): Path to directory containing WAV files
    """
    wav_path = Path(directory)
    durations = []
    file_stats = []

    # Collect all durations
    for wav_file in wav_path.glob('*.wav'):
        try:
            duration = get_wav_duration(wav_file)
            durations.append(duration)
            file_stats.append({
                'file': wav_file.name,
                'duration': duration
            })
        except Exception as e:
            print(f"Error processing {wav_file}: {e}")

    if not durations:
        print("No WAV files found in the directory")
        return

    # Convert to numpy array for calculations
    durations = np.array(durations)

    # Basic statistics
    stats = {
        'Total files': len(durations),
        'Min duration': f"{durations.min():.2f} seconds",
        'Max duration': f"{durations.max():.2f} seconds",
        'Average duration': f"{durations.mean():.2f} seconds",
        'Median duration': f"{np.median(durations):.2f} seconds",
        'Total duration': str(timedelta(seconds=int(durations.sum()))),
        'Files < 3 seconds': sum(durations < 3),
        'Files 3-5 seconds': sum((durations >= 3) & (durations < 5)),
        'Files 5-10 seconds': sum((durations >= 5) & (durations < 10)),
        'Files > 10 seconds': sum(durations >= 10),
    }

    # Create DataFrame for detailed analysis
    df = pd.DataFrame(file_stats)

    # Sort files by duration
    shortest_files = df.nsmallest(5, 'duration')
    longest_files = df.nlargest(5, 'duration')

    # Print statistics
    print("\n=== WAV Files Statistics ===")
    for key, value in stats.items():
        print(f"{key}: {value}")

    print("\n=== Shortest Files ===")
    for _, row in shortest_files.iterrows():
        print(f"{row['file']}: {row['duration']:.2f} seconds")

    print("\n=== Longest Files ===")
    for _, row in longest_files.iterrows():
        print(f"{row['file']}: {row['duration']:.2f} seconds")

    # Create duration distribution plot
    plt.figure(figsize=(10, 6))
    plt.hist(durations, bins=30, edgecolor='black')
    plt.title('Distribution of WAV File Durations')
    plt.xlabel('Duration (seconds)')
    plt.ylabel('Number of Files')

    # Save plot
    plot_path = wav_path / 'duration_distribution.png'
    plt.savefig(plot_path)
    plt.close()

    # Save detailed statistics to CSV
    stats_df = pd.DataFrame.from_dict(stats, orient='index', columns=['Value'])
    stats_df.to_csv(wav_path / 'audio_statistics.csv')

    # Save full file listing with durations
    df.sort_values('duration').to_csv(wav_path / 'file_durations.csv', index=False)

if __name__ == "__main__":
    source_dir = "/home/karen/PhD/TTSDatasetCreator/data/hy_speech/wav"

    analyze_wav_files(source_dir)