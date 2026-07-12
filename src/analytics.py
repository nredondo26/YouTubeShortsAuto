"""YouTube Analytics API integration for video statistics."""

import os
import sys
from typing import Optional, Dict, List
from datetime import datetime, timedelta

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.status import info, warning, error


class YouTubeAnalytics:
    """YouTube Analytics API client."""
    
    def __init__(self, credentials_path: str = None):
        """Initialize YouTube Analytics client.
        
        Args:
            credentials_path: Path to OAuth2 credentials JSON file
        """
        self.credentials_path = credentials_path or os.path.join(ROOT_DIR, "youtube_credentials.json")
        self.service = None
        self.analytics_service = None
    
    def authenticate(self) -> bool:
        """Authenticate with YouTube API.
        
        Returns:
            True if authentication successful
        """
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import pickle
            
            SCOPES = [
                'https://www.googleapis.com/auth/youtube.readonly',
                'https://www.googleapis.com/auth/yt-analytics.readonly',
            ]
            
            creds = None
            token_path = os.path.join(ROOT_DIR, '.token.pickle')
            
            if os.path.exists(token_path):
                with open(token_path, 'rb') as token:
                    creds = pickle.load(token)
            
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        warning("YouTube credentials file not found. Analytics disabled.")
                        return False
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                with open(token_path, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('youtube', 'v3', credentials=creds)
            self.analytics_service = build('youtubeAnalytics', 'v2', credentials=creds)
            
            info("YouTube Analytics authenticated successfully")
            return True
            
        except ImportError:
            warning("Google API libraries not installed. Run: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
            return False
        except Exception as e:
            error(f"YouTube Analytics authentication failed: {e}")
            return False
    
    def get_channel_stats(self, channel_id: str = None) -> Dict:
        """Get channel statistics.
        
        Args:
            channel_id: YouTube channel ID (uses authenticated user if None)
        
        Returns:
            Dict with channel statistics
        """
        if not self.service:
            return {"error": "Not authenticated"}
        
        try:
            # Get channel ID if not provided
            if not channel_id:
                response = self.service.channels().list(
                    part='statistics,snippet',
                    mine=True
                ).execute()
                
                if not response.get('items'):
                    return {"error": "No channel found"}
                
                channel = response['items'][0]
            else:
                response = self.service.channels().list(
                    part='statistics,snippet',
                    id=channel_id
                ).execute()
                
                if not response.get('items'):
                    return {"error": "Channel not found"}
                
                channel = response['items'][0]
            
            stats = channel['statistics']
            snippet = channel['snippet']
            
            return {
                "channel_id": channel['id'],
                "title": snippet.get('title', ''),
                "description": snippet.get('description', '')[:200],
                "subscribers": int(stats.get('subscriberCount', 0)),
                "views": int(stats.get('viewCount', 0)),
                "videos": int(stats.get('videoCount', 0)),
                "hidden_subs": stats.get('hiddenSubscriberCount', False),
            }
            
        except Exception as e:
            error(f"Failed to get channel stats: {e}")
            return {"error": str(e)}
    
    def get_video_stats(self, video_id: str) -> Dict:
        """Get statistics for a specific video.
        
        Args:
            video_id: YouTube video ID
        
        Returns:
            Dict with video statistics
        """
        if not self.service:
            return {"error": "Not authenticated"}
        
        try:
            response = self.service.videos().list(
                part='statistics,snippet,contentDetails',
                id=video_id
            ).execute()
            
            if not response.get('items'):
                return {"error": "Video not found"}
            
            video = response['items'][0]
            stats = video['statistics']
            snippet = video['snippet']
            
            return {
                "video_id": video['id'],
                "title": snippet.get('title', ''),
                "published_at": snippet.get('publishedAt', ''),
                "duration": video.get('contentDetails', {}).get('duration', ''),
                "views": int(stats.get('viewCount', 0)),
                "likes": int(stats.get('likeCount', 0)),
                "comments": int(stats.get('commentCount', 0)),
                "favorites": int(stats.get('favoriteCount', 0)),
            }
            
        except Exception as e:
            error(f"Failed to get video stats: {e}")
            return {"error": str(e)}
    
    def get_recent_videos(self, channel_id: str = None, max_results: int = 10) -> List[Dict]:
        """Get recent videos from a channel.
        
        Args:
            channel_id: YouTube channel ID (uses authenticated user if None)
            max_results: Maximum number of videos to return
        
        Returns:
            List of video dictionaries with statistics
        """
        if not self.service:
            return []
        
        try:
            # Get channel ID if not provided
            if not channel_id:
                response = self.service.channels().list(
                    part='contentDetails',
                    mine=True
                ).execute()
                
                if not response.get('items'):
                    return []
                
                channel_id = response['items'][0]['id']
            
            # Get uploads playlist
            response = self.service.channels().list(
                part='contentDetails',
                id=channel_id
            ).execute()
            
            if not response.get('items'):
                return []
            
            uploads_playlist = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            # Get recent videos from uploads playlist
            response = self.service.playlistItems().list(
                part='snippet',
                playlistId=uploads_playlist,
                maxResults=max_results
            ).execute()
            
            videos = []
            for item in response.get('items', []):
                video_id = item['snippet']['resourceId']['videoId']
                video_stats = self.get_video_stats(video_id)
                
                if "error" not in video_stats:
                    videos.append(video_stats)
            
            return videos
            
        except Exception as e:
            error(f"Failed to get recent videos: {e}")
            return []
    
    def get_analytics_report(self, channel_id: str = None, days: int = 30) -> Dict:
        """Get analytics report for a channel.
        
        Args:
            channel_id: YouTube channel ID
            days: Number of days to analyze
        
        Returns:
            Dict with analytics data
        """
        if not self.analytics_service:
            return {"error": "Analytics service not authenticated"}
        
        try:
            if not channel_id:
                # Get authenticated user's channel
                response = self.service.channels().list(
                    part='id',
                    mine=True
                ).execute()
                
                if not response.get('items'):
                    return {"error": "No channel found"}
                
                channel_id = response['items'][0]['id']
            
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
            
            response = self.analytics_service.reports().query(
                ids=f'channel=={channel_id}',
                startDate=start_date,
                endDate=end_date,
                metrics='views,likes,comments,estimatedMinutesWatched,subscribersGained',
                dimensions='day'
            ).execute()
            
            return {
                "channel_id": channel_id,
                "period": f"{start_date} to {end_date}",
                "rows": response.get('rows', []),
                "columnHeaders": response.get('columnHeaders', []),
            }
            
        except Exception as e:
            error(f"Failed to get analytics report: {e}")
            return {"error": str(e)}
    
    def search_videos(self, query: str, max_results: int = 10) -> List[Dict]:
        """Search for videos on YouTube.
        
        Args:
            query: Search query
            max_results: Maximum results to return
        
        Returns:
            List of video dictionaries
        """
        if not self.service:
            return []
        
        try:
            response = self.service.search().list(
                part='snippet',
                q=query,
                type='video',
                maxResults=max_results,
                order='viewCount'
            ).execute()
            
            videos = []
            for item in response.get('items', []):
                videos.append({
                    "video_id": item['id']['videoId'],
                    "title": item['snippet']['title'],
                    "description": item['snippet']['description'][:200],
                    "published_at": item['snippet']['publishedAt'],
                    "thumbnail": item['snippet']['thumbnails']['default']['url'],
                })
            
            return videos
            
        except Exception as e:
            error(f"Failed to search videos: {e}")
            return []


# Singleton instance
_analytics_instance = None


def get_analytics(credentials_path: str = None) -> YouTubeAnalytics:
    """Get or create YouTube Analytics instance."""
    global _analytics_instance
    if _analytics_instance is None:
        _analytics_instance = YouTubeAnalytics(credentials_path)
    return _analytics_instance


if __name__ == "__main__":
    analytics = YouTubeAnalytics()
    
    if analytics.authenticate():
        stats = analytics.get_channel_stats()
        print("Channel Stats:", stats)
    else:
        print("Authentication failed. Make sure youtube_credentials.json exists.")
