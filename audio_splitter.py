from pydub import AudioSegment
import os


def split_audio(input_file, split_point_seconds, output_dir="split_audio"):
    """
    Split an audio file into two parts at the specified time point.

    Parameters:
    input_file (str): Path to the input audio file
    split_point_seconds (int): Point at which to split the audio (in seconds)
    output_dir (str): Directory to save the output files (default: 'split_audio')

    Returns:
    tuple: Paths to the two output files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Get file extension from input file
    file_extension = os.path.splitext(input_file)[1]

    # Load the audio file
    try:
        audio = AudioSegment.from_file(input_file)
    except Exception as e:
        raise Exception(f"Error loading audio file: {str(e)}")

    # Convert seconds to milliseconds
    split_point_ms = split_point_seconds * 1000

    # Check if split point is valid
    if split_point_ms > len(audio):
        raise ValueError("Split point exceeds audio duration")

    # Split the audio
    first_part = audio[:split_point_ms]
    second_part = audio[split_point_ms:]

    # Generate output filenames
    base_filename = os.path.splitext(os.path.basename(input_file))[0]
    first_output = os.path.join(output_dir, f"{base_filename}_part1{file_extension}")
    second_output = os.path.join(output_dir, f"{base_filename}_part2{file_extension}")

    # Export the parts
    first_part.export(first_output, format=file_extension.replace('.', ''))
    second_part.export(second_output, format=file_extension.replace('.', ''))

    return first_output, second_output


# Example usage
if __name__ == "__main__":
    try:
        # Replace these with your actual file path and split point
        input_audio = "C:\\Users\\karenn\\PhD\\TTSDatasetCreator\\split_audio\\hobbit_13_last_part2.wav"
        split_at_seconds = 7

        part1, part2 = split_audio(input_audio, split_at_seconds)
        print(f"Successfully split audio file into:")
        print(f"Part 1: {part1}")
        print(f"Part 2: {part2}")
    except Exception as e:
        print(f"Error: {str(e)}")