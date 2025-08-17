"""
YouTube Batch Upload Script - VS Code Ready
Uploads all videos from a specified folder to YouTube with customizable metadata.
Now supports YouTube Shorts detection!
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import tempfile

# You'll need to install these packages:
# pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaFileUpload
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    import pickle
except ImportError as e:
    print(f"Missing required package. Please install: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)

# ==================== CONFIGURATION ====================

# Your YouTube API credentials (embedded directly in code)
CREDENTIALS_DATA = {
  "installed": {
    "client_id": "CHANGE >>>>>>> YOUR CLIENT ID",
    "project_id": "CHANGE >>>>>>> PROJECT ID",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": " CHANGE >>>>>>> CLIENT SECRET",
    "redirect_uris": [
      "http://localhost"
    ]
  }
}

# ==================== USER SETTINGS ====================
# Modify these settings for your uploads

# Path to your video folder (change this to your folder path)
VIDEO_FOLDER = r"CHANGE >>>>>>> To your folders location"  # Updated to your actual video folder

# Account Selection Settings
FORCE_ACCOUNT_SELECTION = True  # Set to True to choose account every time, False to remember choice

# Default settings for all videos
DEFAULT_SETTINGS = {
    "description": "Video Descryption",
    "tags": [
    "tag", "tag", "tag", "tag", "tag", 
    "tag", "tag", "tag", "tag", "tag", 
    "tag", "tag", "tag", "tag", "tag",  
    "tag", "tag", "tag", "tag", "tag", 
    "tag", "tag", "tag", "tag", "tag"
    "tag", "tag", "tag", "tag", 
],
    "privacy": "public",  # Options: "private", "unlisted", "public"
    "category_id": 22,  # 22 = People & Blogs, 24 = Entertainment, 10 = Music
    "made_for_kids": False
}

# Specific settings for individual videos (optional)
# Use the exact filename as the key
VIDEO_SPECIFIC_SETTINGS = {
    "my_special_video.mp4": {
        "title": "My Special Video Title",
        "description": "This is a special video with custom settings",
        "tags": ["special", "custom", "video"],
        "privacy": "unlisted",
        "category_id": 24,
        "made_for_kids": False
    }
    # Add more videos here if needed
    # "another_video.mp4": { ... }
}

# ==================== SCRIPT CODE ====================

# YouTube API settings
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
API_SERVICE_NAME = 'youtube'
API_VERSION = 'v3'

# Supported video formats
SUPPORTED_FORMATS = {'.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv', '.webm', '.m4v'}

def is_shorts_video(filename: str) -> bool:
    """Check if video should be treated as a YouTube Short based on filename."""
    return filename.lower().startswith('shorts')

def get_clean_title(filename: str) -> str:
    """Get clean title from filename, removing 'shorts' prefix if present."""
    # Remove file extension
    title = Path(filename).stem
    
    # If it starts with "shorts" (case insensitive), remove it and clean up
    if title.lower().startswith('shorts'):
        # Remove "shorts" prefix and any following spaces, dashes, underscores
        title = title[6:].lstrip(' -_')
    
    return title

class YouTubeUploader:
    def __init__(self):
        """Initialize the YouTube uploader with embedded credentials."""
        self.youtube = None
        self.authenticate()
        
    def authenticate(self):
        """Authenticate with YouTube API using embedded credentials."""
        creds = None
        
        # If forced account selection, remove existing token
        if FORCE_ACCOUNT_SELECTION and os.path.exists('token.pickle'):
            os.remove('token.pickle')
            logging.info("Forced account selection - you'll be prompted to choose your YouTube account")
        
        # Token file stores the user's access and refresh tokens
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        
        # If there are no valid credentials, request authorization
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                # Create temporary credentials file
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                    json.dump(CREDENTIALS_DATA, temp_file)
                    temp_file_path = temp_file.name
                
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(temp_file_path, SCOPES)
                    # This will open browser and let you choose which Google account to use
                    creds = flow.run_local_server(port=0)
                    logging.info("Authentication completed. Videos will be uploaded to the selected YouTube channel.")
                finally:
                    # Clean up temporary file
                    os.unlink(temp_file_path)
            
            # Save credentials for future use
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        
        self.youtube = build(API_SERVICE_NAME, API_VERSION, credentials=creds)
        logging.info("Successfully authenticated with YouTube API")
    
    def upload_video(self, video_path: str, video_config: Dict) -> Optional[str]:
        """Upload a single video to YouTube."""
        try:
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': video_config.get('title', Path(video_path).stem),
                    'description': video_config.get('description', ''),
                    'tags': video_config.get('tags', []),
                    'categoryId': str(video_config.get('category_id', 22))
                },
                'status': {
                    'privacyStatus': video_config.get('privacy', 'private'),
                    'selfDeclaredMadeForKids': video_config.get('made_for_kids', False)
                }
            }
            
            # Create media upload object
            media = MediaFileUpload(
                video_path,
                chunksize=-1,
                resumable=True,
                mimetype='video/*'
            )
            
            # Execute upload
            logging.info(f"Starting upload for: {video_path}")
            insert_request = self.youtube.videos().insert(
                part=','.join(body.keys()),
                body=body,
                media_body=media
            )
            
            video_id = self._resumable_upload(insert_request)
            if video_id:
                logging.info(f"Successfully uploaded: {video_config.get('title', Path(video_path).stem)}")
                logging.info(f"Video URL: https://www.youtube.com/watch?v={video_id}")
                return video_id
            
        except HttpError as e:
            logging.error(f"HTTP error occurred: {e}")
        except Exception as e:
            logging.error(f"Error uploading {video_path}: {e}")
        
        return None
    
    def _resumable_upload(self, insert_request):
        """Handle resumable upload with progress tracking."""
        response = None
        error = None
        retry = 0
        
        while response is None:
            try:
                status, response = insert_request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logging.info(f"Upload progress: {progress}%")
            except HttpError as e:
                if e.resp.status in [500, 502, 503, 504]:
                    error = f"A retriable HTTP error {e.resp.status} occurred:\n{e.content}"
                else:
                    raise
            except Exception as e:
                error = f"A retriable error occurred: {e}"
            
            if error is not None:
                logging.warning(error)
                retry += 1
                if retry > 3:
                    logging.error("Maximum retry attempts exceeded")
                    return None
                
                import time
                time.sleep(2 ** retry)
        
        if 'id' in response:
            return response['id']
        else:
            logging.error(f"Upload failed with response: {response}")
            return None

def get_video_files(folder_path: str) -> List[str]:
    """Get all video files from the specified folder."""
    video_files = []
    folder = Path(folder_path)
    
    if not folder.exists():
        logging.error(f"Folder does not exist: {folder_path}")
        return video_files
    
    logging.info(f"Scanning folder: {folder_path}")
    
    # Debug: List ALL files in the folder first
    all_files = list(folder.iterdir())
    logging.info(f"Total files in folder: {len(all_files)}")
    
    for file_path in all_files:
        if file_path.is_file():
            file_ext = file_path.suffix.lower()
            logging.info(f"Found file: {file_path.name} (extension: '{file_ext}')")
            
            if file_ext in SUPPORTED_FORMATS:
                video_files.append(str(file_path))
                logging.info(f"  ADDED as video file")
            else:
                logging.info(f"  Not a supported video format")
        else:
            logging.info(f"Found directory: {file_path.name}")
    
    logging.info(f"Final result: Found {len(video_files)} video files in {folder_path}")
    return sorted(video_files)

def main():
    """Main function to run the upload process."""
    # Setup logging with UTF-8 encoding to handle emojis
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('youtube_upload.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("Starting YouTube batch upload process...")
    logging.info(f"Looking for videos in: {VIDEO_FOLDER}")
    logging.info(f"Supported formats: {', '.join(sorted(SUPPORTED_FORMATS))}")
    
    # Validate video folder
    if not os.path.exists(VIDEO_FOLDER):
        logging.error(f"Video folder does not exist: {VIDEO_FOLDER}")
        logging.error("Please check the folder path and try again")
        return
    
    # Get video files with detailed debugging
    video_files = get_video_files(VIDEO_FOLDER)
    if not video_files:
        logging.error("No video files found to upload")
        logging.error("Make sure your MP4 files are directly in the folder (not in subfolders)")
        logging.error("Check that file extensions are lowercase (.mp4, not .MP4)")
        return
    
    logging.info(f"Found {len(video_files)} videos to upload:")
    for i, video_file in enumerate(video_files, 1):
        file_size = Path(video_file).stat().st_size / (1024*1024)  # Size in MB
        filename = Path(video_file).name
        is_short = is_shorts_video(filename)
        video_type = "SHORT" if is_short else "REGULAR"
        logging.info(f"  {i}. {filename} ({file_size:.1f} MB) [{video_type}]")
    
    # Ask for confirmation before proceeding
    print(f"\nReady to upload {len(video_files)} videos to YouTube.")
    print("Press Enter to continue or Ctrl+C to cancel...")
    try:
        input()
    except KeyboardInterrupt:
        print("\nUpload cancelled by user")
        return
    
    # Initialize uploader
    try:
        logging.info("Initializing YouTube uploader...")
        uploader = YouTubeUploader()
    except Exception as e:
        logging.error(f"Failed to initialize uploader: {e}")
        return
    
    # Upload videos
    successful_uploads = 0
    failed_uploads = 0
    
    for i, video_file in enumerate(video_files, 1):
        filename = Path(video_file).name
        is_short = is_shorts_video(filename)
        
        logging.info(f"[{i}/{len(video_files)}] Processing: {filename}")
        if is_short:
            logging.info("  This video will be uploaded as a YouTube SHORT")
        
        # Get configuration for this specific video or use defaults
        video_config = DEFAULT_SETTINGS.copy()
        if filename in VIDEO_SPECIFIC_SETTINGS:
            video_config.update(VIDEO_SPECIFIC_SETTINGS[filename])
        
        # Use clean title (removing "shorts" prefix if present)
        if 'title' not in video_config:
            video_config['title'] = get_clean_title(filename)
        
        logging.info(f"  Title: {video_config['title']}")
        logging.info(f"  Privacy: {video_config['privacy']}")
        logging.info(f"  Tags: {', '.join(video_config.get('tags', []))}")
        
        video_id = uploader.upload_video(video_file, video_config)
        
        if video_id:
            successful_uploads += 1
            logging.info(f"  SUCCESS - Video ID: {video_id}")
            logging.info(f"  URL: https://www.youtube.com/watch?v={video_id}")
            if is_short:
                logging.info(f"  This video should appear as a SHORT on YouTube")
        else:
            failed_uploads += 1
            logging.error(f"  FAILED to upload {filename}")
        
        # Add a small delay between uploads to be respectful to the API
        if i < len(video_files):  # Don't delay after the last video
            logging.info("  Waiting 3 seconds before next upload...")
            import time
            time.sleep(3)
    
    # Summary
    logging.info("=" * 60)
    logging.info(f"UPLOAD COMPLETED!")
    logging.info(f"Successful uploads: {successful_uploads}")
    logging.info(f"Failed uploads: {failed_uploads}")
    if successful_uploads > 0:
        logging.info(f"Check your YouTube channel for the uploaded videos")
        logging.info(f"Videos starting with 'shorts' should appear as YouTube Shorts")
    logging.info("=" * 60)

# ==================== RUN SCRIPT ====================

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nUpload process interrupted by user")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to exit...")