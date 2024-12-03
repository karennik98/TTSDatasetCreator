import pandas as pd
from pathlib import Path


def clean_metadata_text(file_path):
    """
    Read metadata.csv file, remove specific punctuation from text column and save to a new file
    with '_nopunct.csv' suffix. Maintains the pipe separator and original structure.

    Args:
        file_path (str): Path to the metadata.csv file
    """
    try:
        # Convert to Path object
        input_path = Path(file_path)

        # Create output path with _nopunct suffix
        output_path = input_path.parent / f"{input_path.stem}_nopunct.csv"

        # Read the metadata file with pipe separator
        df = pd.read_csv(input_path, sep='|')

        # Define specific punctuation marks to remove
        # Including both English and Armenian punctuation
        punctuations = '''․―,.!?՜՞։:;՝»«()[]{}՛՚""''"-—‒…'''

        def remove_specific_punct(text):
            text = str(text)
            for punct in punctuations:
                text = text.replace(punct, '')
            return text

        # Apply punctuation removal
        df['text'] = df['text'].astype(str).apply(remove_specific_punct)

        # Remove multiple spaces and strip
        df['text'] = df['text'].apply(lambda x: ' '.join(x.split()))

        # Save to new file with pipe separator
        df.to_csv(output_path, sep='|', index=False)
        print(f"Successfully created cleaned file: {output_path}")

    except Exception as e:
        print(f"Error processing file: {e}")
        print("Full error info:")
        import traceback
        traceback.print_exc()
if __name__ == "__main__":
    source_file = "/home/karen/PhD/TTSDatasetCreator/data/hy_speech/metadata.csv"

    clean_metadata_text(source_file)