import wave
import numpy as np
import sys


def get_db_at_second(wav_file_path, target_second):
    """
    Get the dB value at a specific second in a WAV file.

    Parameters:
    wav_file_path (str): Path to the WAV file
    target_second (float): The second at which to measure dB

    Returns:
    float: The dB value at the specified second
    """
    try:
        # Open the WAV file
        with wave.open(wav_file_path, 'rb') as wav_file:
            # Get file properties
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            # Calculate position in frames
            target_frame = int(target_second * frame_rate)

            # Check if target second exists in file
            duration = n_frames / frame_rate
            if target_second > duration:
                raise ValueError(f"Specified second {target_second} exceeds audio duration of {duration:.2f} seconds")

            # Move to the target position
            wav_file.setpos(target_frame)

            # Read one second worth of frames
            frame_count = min(frame_rate, n_frames - target_frame)
            frames = wav_file.readframes(frame_count)

            # Convert frames to numpy array
            if sample_width == 1:
                dtype = np.uint8
            elif sample_width == 2:
                dtype = np.int16
            elif sample_width == 4:
                dtype = np.int32
            else:
                raise ValueError("Unsupported sample width")

            audio_data = np.frombuffer(frames, dtype=dtype)

            # If stereo, take average of channels
            if n_channels == 2:
                audio_data = audio_data.reshape(-1, 2).mean(axis=1)

            # Calculate RMS value
            rms = np.sqrt(np.mean(np.square(audio_data)))

            # Convert to dB
            # Reference value depends on sample width
            if sample_width == 1:
                ref = 128
            elif sample_width == 2:
                ref = 32768
            else:
                ref = 2147483648

            db = 20 * np.log10(rms / ref)

            return db

    except wave.Error as e:
        print(f"Error reading WAV file: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


import numpy as np
from scipy.io import wavfile


def get_db_at_point(wav_file_path, target_second, window_size_ms=100):
    """
    Get the dB value at a specific point in time in an audio file.

    Parameters:
    wav_file_path (str): Path to the WAV file
    target_second (float): The specific second to analyze
    window_size_ms (int): Size of analysis window in milliseconds

    Returns:
    float: dB value at the specified point
    """
    try:
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

        # Calculate start and end sample positions for the target second
        start_sample = int(target_second * sample_rate)

        # Check if target second exists in file
        if start_sample >= len(audio_data):
            raise ValueError(
                f"Specified second {target_second} exceeds audio duration of {len(audio_data) / sample_rate:.2f} seconds")

        # Get the window of samples centered on the target point
        half_window = window_size // 2
        start_sample = max(0, start_sample - half_window)
        end_sample = min(len(audio_data), start_sample + window_size)

        # Extract the audio segment
        segment = audio_data[start_sample:end_sample]

        # Calculate dB value
        rms = np.sqrt(np.mean(np.square(segment)))
        db = 20 * np.log10(rms) if rms > 0 else -100

        return {
            'db': db,
            'time': target_second,
            'window_start': start_sample / sample_rate,
            'window_end': end_sample / sample_rate,
            'is_silence': db <= -40  # Using -40dB as silence threshold
        }

    except Exception as e:
        print(f"Error analyzing audio: {str(e)}")
        return None

def main():
    wav_file_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\data\\hobbit_3\\hobbit_3.wav"
    target_seconds1 = [  91.148,
                        88.380,
                        74.428,
                        62.026,
                        59.348,
                        53.958,
                        44.328,
                        40.046,
                        29.481,
                        21.727,
                        14.106
                     ]
    for target_second in target_seconds1:
        db_value = get_db_at_second(wav_file_path, target_second)
        if db_value is not None:
            print(f"dB value at {target_second} seconds: {db_value:.2f} dB")

    target_seconds2 = [ 14.366,
                        21.307,
                        29.021,
                        40.076,
                        44.058,
                        53.758,
                        58.778,
                        62.386,
                        74.178,
                        87.830,
                        91.608,
                        93.0,
                        94.0,
                        95.0
                      ]

    print("-------------------------------------------")
    for target_second in target_seconds2:
        db_value = get_db_at_second(wav_file_path, target_second)
        if db_value is not None:
            print(f"dB value at {target_second} seconds: {db_value:.2f} dB")

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    for target_second in target_seconds2:
        db_value = get_db_at_point(wav_file_path, target_second, window_size_ms=1000)
        if db_value is not None:
            print(f"dB value at {target_second} seconds: {db_value['db']:.2f} dB")


    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    for target_second in target_seconds1:
        db_value = get_db_at_point(wav_file_path, target_second, window_size_ms=500)
        if db_value is not None:
            print(f"dB value at {target_second} seconds: {db_value['db']:.2f} dB")

if __name__ == "__main__":
    main()