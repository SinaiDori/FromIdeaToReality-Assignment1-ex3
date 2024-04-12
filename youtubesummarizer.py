from pytube import YouTube
from googleapiclient.discovery import build
from scenedetect import detect, ContentDetector
import cv2
import os
import easyocr
from easyocr import Reader
from PIL import Image, ImageDraw, ImageFont
import re

# Replace with your actual API key
API_KEY = "AIzaSyAt3JilcWEes3RPxD-NEivF2tGi1gAgTFk"


def download_video(search_query):
    # Create a YouTube API client
    youtube = build("youtube", "v3", developerKey=API_KEY)

    # Search for videos
    search_response = youtube.search().list(
        q=search_query,
        type="video",
        part="id,snippet",
        maxResults=50,
        videoDuration="short"
    ).execute()

    # Find the first video that is less than 10 minutes
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            video_id = search_result["id"]["videoId"]
            yt = YouTube(f"https://www.youtube.com/watch?v={video_id}")
            if yt.length < 600:  # 10 minutes in seconds
                print(f"Downloading: {yt.title}")
                video_path = yt.streams.get_highest_resolution().download()
                print("Download completed!")
                return video_path

    print("No videos found matching the search criteria.")
    return None


def save_frames(scene_list, video_path):
    # Create a VideoCapture object
    cap = cv2.VideoCapture(video_path)
    frame_num = 0
    # Extract video name from the video_path
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    frames_directory = f"{video_name}_frames"
    os.makedirs(frames_directory, exist_ok=True)
    # Create an EasyOCR reader
    reader = Reader(['en'])
    # Load a font for the watermark
    font = ImageFont.truetype("./arapey-regular.ttf", 24)
    # Initialize a string to store the concatenated text
    concatenated_text = ""

    # Iterate through the scene list and save major frames
    for scene in scene_list:
        frame_num += 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, scene[0].get_frames())
        ret, frame = cap.read()
        if ret:
            frame_path = os.path.join(
                frames_directory, f"frame_{frame_num}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Saved {frame_path}")
            # Use EasyOCR to detect text in the frame
            result = reader.readtext(frame_path)
            # Process the detected text
            for text in result:
                detected_text = text[1]
                # Remove numbers and symbols, keeping only English characters
                cleaned_text = re.sub(r'[^a-zA-Z\s]+', '', detected_text)
                # Concatenate the cleaned text
                concatenated_text += cleaned_text + " "
            # Add watermark to the image
            add_watermark(frame_path, "Sinai Dori", font)

    cap.release()
    # Print the concatenated text
    print(f"Concatenated text: {concatenated_text.strip()}")


def add_watermark(image_path, watermark_text, font):
    # Open the image
    image = Image.open(image_path)

    # Create a drawing object
    draw = ImageDraw.Draw(image)

    # Get the image size
    width, height = image.size

    # Calculate the position for the watermark
    text_width = draw.textlength(watermark_text, font=font)
    text_height = int(min(image.size) / 20)
    watermark_x = width - text_width - 10  # Adjust the position as needed
    watermark_y = height - text_height - 10
    # Get the pixel value
    pixel_value = image.getpixel((10, 10))
    # Calculate brightness (average of RGB values)
    brightness = sum(pixel_value[:3]) / 3
    # Compare brightness to a threshold
    text_color = (255, 255, 255) if brightness < 128 else (0, 0, 0)

    # Add the watermark text
    draw.text((watermark_x, watermark_y), watermark_text,
              font=font, fill=text_color)

    # Save the watermarked image
    image.save(image_path)


if __name__ == "__main__":
    search_query = input("Enter a subject to search on YouTube: ")
    video_path = download_video(search_query)

    if video_path:
        # Perform scene detection
        scene_list = detect(video_path, ContentDetector())

        # Save major frames
        save_frames(scene_list, video_path)
