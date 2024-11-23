import wave
import json
import sys


def extract_wav_info(wav_file_path):
    with wave.open(wav_file_path, 'rb') as wav_file:
        # Extract audio information
        channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        comp_type = wav_file.getcomptype()
        comp_name = wav_file.getcompname()

        # Calculate duration
        duration = n_frames / float(framerate)

        # Create a dictionary with the extracted information
        audio_info = {
            "channels": channels,
            "sample_width": sample_width,
            "framerate": framerate,
            "n_frames": n_frames,
            "compression_type": comp_type,
            "compression_name": comp_name,
            "duration": duration
        }

    return audio_info

def main():
    wav_file_path = 'C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\data\\archive\\Narek Barseghyan\\Hobbit\\hobbit_2.wav'

    try:
        audio_info = extract_wav_info(wav_file_path)

        # Write the audio info to a JSON file
        output_file = "hobbit_2_temp_wav.json"
        with open(output_file, 'w') as json_file:
            json.dump(audio_info, json_file, indent=4)

        print(f"Audio information has been written to {output_file}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")


if __name__ == "__main__":
    main()