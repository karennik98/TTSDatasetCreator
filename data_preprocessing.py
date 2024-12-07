import os
from pydub import AudioSegment
from pathlib import Path
import argparse
import wave
import numpy as np
import librosa
import soundfile as sf
from pathlib import Path

def convert_wav_framerate(input_file, output_file, target_sr=22050):
    # Load the audio file
    audio, sr = librosa.load(input_file, sr=None)

    # Resample the audio to the target sample rate
    audio_resampled = librosa.resample(audio, orig_sr=sr, target_sr=target_sr)

    # Write the resampled audio to the output file
    sf.write(output_file, audio_resampled, target_sr)
def stereo_to_mono(input_file, output_file):
    try:
        with wave.open(input_file, 'rb') as wav_file:
            # Check if it's actually a stereo file
            if wav_file.getnchannels() != 2:
                print(f"Skipping {input_file}: Not a stereo file.")
                return False

            # Read the parameters
            params = wav_file.getparams()
            sample_width = wav_file.getsampwidth()
            frames = wav_file.readframes(params.nframes)

        # Convert the byte string to a numpy array
        stereo_array = np.frombuffer(frames, dtype=f'int{sample_width * 8}')

        # Reshape the array to separate left and right channels
        stereo_array = stereo_array.reshape(-1, 2)

        # Convert to mono by averaging the two channels
        mono_array = stereo_array.mean(axis=1).astype(stereo_array.dtype)

        # Write the mono audio to a new WAV file
        with wave.open(output_file, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(params.framerate)
            wav_file.writeframes(mono_array.tobytes())

        print(f"Converted: {input_file} -> {output_file}")
        return True

    except Exception as e:
        print(f"Error processing {input_file}: {str(e)}")
        return False
def convert_mp3_to_wav(input_file, output_file):
    audio = AudioSegment.from_mp3(input_file)
    audio.export(output_file, format="wav")


def split_audio(input_file, start_second, output_file):
    # Load the audio file using pydub
    audio = AudioSegment.from_file(input_file)

    # Convert start_second to milliseconds
    start_ms = start_second * 1000

    # Split the audio from the specified start time to the end
    split_audio = audio[start_ms:]

    # Export the split audio to the output file
    split_audio.export(output_file, format=os.path.splitext(output_file)[1][1:])

def main():
    input_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\tmp\\The_Hobbit_06.mp3"
    wav_output_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\tmp\\hobbit_13.wav"
    mono_output_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\tmp\\hobbit_13_mono.wav"
    output_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\tmp\\hobbit_13_last.wav"

    convert_mp3_to_wav(input_path, wav_output_path)
    stereo_to_mono(wav_output_path, mono_output_path)
    convert_wav_framerate(mono_output_path, output_path)

    # splited_output_path = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\tmp\\hobbit_splited_9.wav"
    # start_second = 5
    # split_audio(output_path, start_second, splited_output_path)


if __name__ == "__main__":
    main()