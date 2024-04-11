from pytube import YouTube
from googleapiclient.discovery import build
from scenedetect import detect, ContentDetector
import cv2
import os
import easyocr
from easyocr import Reader

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

    # Iterate through the scene list and save major frames
    for scene in scene_list:
        frame_num += 1
        cap.set(cv2.CAP_PROP_POS_FRAMES, scene[0].get_frames())
        ret, frame = cap.read()
        if ret:
            # frame_path = f"frame_{frame_num}.jpg"
            frame_path = os.path.join(
                frames_directory, f"frame_{frame_num}.jpg")
            cv2.imwrite(frame_path, frame)
            print(f"Saved {frame_path}")

            # Use EasyOCR to detect text in the frame
            result = reader.readtext(frame_path)

            # Print the detected text
            for text in result:
                print(f"Detected text: {text[1]}")

    cap.release()


if __name__ == "__main__":
    search_query = input("Enter a subject to search on YouTube: ")
    video_path = download_video(search_query)

    if video_path:
        # Perform scene detection
        scene_list = detect(video_path, ContentDetector())

        # Save major frames
        save_frames(scene_list, video_path)
