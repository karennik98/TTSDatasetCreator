import yt_dlp
import os


def download_video(url, output_path="tmp"):
    """
    Downloads a YouTube video and extracts its audio
    """
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',  # Get best quality
            'outtmpl': os.path.join(output_path, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'verbose': True
        }

        print(f"Starting download from: {url}")

        # Download the video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            video_title = info['title']

        print(f"\nDownload completed successfully!")
        print(f"Title: {video_title}")
        print(f"Saved to: {output_path}")

        return True

    except Exception as e:
        print(f"\nAn error occurred: {str(e)}")
        return False


if __name__ == "__main__":
    print("YouTube Video Downloader")
    print("-" * 20)
    video_url = input("\nEnter YouTube URL: ")
    download_video(video_url)
    input("\nPress Enter to exit...")