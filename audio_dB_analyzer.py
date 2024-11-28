import numpy as np
from scipy.io import wavfile


def analyze_noise_silence_db(wav_file_path, silence_threshold_db=-40, window_size_ms=100):
    """
    Analyze average dB levels separately for noise and silence portions of audio.

    Parameters:
    wav_file_path (str): Path to the WAV file
    silence_threshold_db (float): dB threshold below which is considered silence
    window_size_ms (int): Size of analysis window in milliseconds

    Returns:
    dict: Statistics about noise and silence sections
    """
    # Load the audio file
    sample_rate, audio_data = wavfile.read(wav_file_path)

    # Convert to mono if stereo
    if len(audio_data.shape) > 1:
        audio_data = np.mean(audio_data, axis=1)

    # Convert to float32 and normalize
    audio_data = audio_data.astype(np.float32)
    audio_data = audio_data / np.max(np.abs(audio_data))

    # Calculate window size in samples
    window_size = int(sample_rate * (window_size_ms / 1000))

    # Lists to store dB values for noise and silence
    noise_db_values = []
    silence_db_values = []

    # Process audio in windows
    for i in range(0, len(audio_data), window_size):
        segment = audio_data[i:i + window_size]
        if len(segment) > 0:  # Ensure we have data
            rms = np.sqrt(np.mean(np.square(segment)))
            db = 20 * np.log10(rms) if rms > 0 else -100

            # Categorize as noise or silence
            if db > silence_threshold_db:
                noise_db_values.append(db)
            else:
                silence_db_values.append(db)

    # Calculate statistics
    stats = {
        'noise': {
            'average_db': np.mean(noise_db_values) if noise_db_values else None,
            'peak_db': np.max(noise_db_values) if noise_db_values else None,
            'min_db': np.min(noise_db_values) if noise_db_values else None,
            'duration_seconds': len(noise_db_values) * (window_size_ms / 1000),
            'percent_of_total': len(noise_db_values) / (len(noise_db_values) + len(silence_db_values)) * 100
        },
        'silence': {
            'average_db': np.mean(silence_db_values) if silence_db_values else None,
            'peak_db': np.max(silence_db_values) if silence_db_values else None,
            'min_db': np.min(silence_db_values) if silence_db_values else None,
            'duration_seconds': len(silence_db_values) * (window_size_ms / 1000),
            'percent_of_total': len(silence_db_values) / (len(noise_db_values) + len(silence_db_values)) * 100
        },
        'total_duration_seconds': (len(noise_db_values) + len(silence_db_values)) * (window_size_ms / 1000)
    }

    return stats


def main():
    wav_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\data\\hobbit_3\\hobbit_3.wav"

    # Analyze audio with default settings
    stats = analyze_noise_silence_db(
        wav_path,
        silence_threshold_db=-40,  # Adjust this threshold to change what's considered silence
        window_size_ms=100
    )

    print("\nAudio Analysis Results:")
    print("-" * 50)

    print("\nNoise Sections:")
    print(f"Average dB: {stats['noise']['average_db']:.2f}")
    print(f"Peak dB: {stats['noise']['peak_db']:.2f}")
    print(f"Duration: {stats['noise']['duration_seconds']:.2f} seconds")
    print(f"Percentage of total: {stats['noise']['percent_of_total']:.1f}%")

    print("\nSilence Sections:")
    print(f"Average dB: {stats['silence']['average_db']:.2f}")
    print(f"Peak dB: {stats['silence']['peak_db']:.2f}")
    print(f"Duration: {stats['silence']['duration_seconds']:.2f} seconds")
    print(f"Percentage of total: {stats['silence']['percent_of_total']:.1f}%")

    print(f"\nTotal Duration: {stats['total_duration_seconds']:.2f} seconds")


if __name__ == "__main__":
    main()
