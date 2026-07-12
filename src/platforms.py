"""Multi-platform upload support - TikTok and Instagram Reels."""

import os
import sys
import time
import json
from typing import Optional

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.status import info, success, warning, error


class TikTokUploader:
    """TikTok video uploader using Selenium."""
    
    def __init__(self, firefox_profile_path: str):
        self.firefox_profile_path = firefox_profile_path
        self.driver = None
    
    def _init_driver(self):
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service
        
        options = Options()
        options.profile = self.firefox_profile_path
        options.headless = True
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(15)
    
    def upload(self, video_path: str, caption: str, tags: list = None) -> dict:
        """Upload video to TikTok.
        
        Args:
            video_path: Path to video file
            caption: Video caption
            tags: List of hashtags
            
        Returns:
            dict with success, url, error
        """
        try:
            self._init_driver()
            
            # Navigate to TikTok upload page
            self.driver.get("https://www.tiktok.com/upload")
            time.sleep(5)
            
            # Check if logged in
            if "login" in self.driver.current_url.lower():
                return {"success": False, "error": "Not logged in to TikTok"}
            
            # Upload video file
            from selenium.webdriver.common.by import By
            upload_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
            upload_input.send_keys(os.path.abspath(video_path))
            
            time.sleep(10)  # Wait for upload
            
            # Add caption
            caption_field = self.driver.find_element(By.CSS_SELECTOR, '[contenteditable="true"]')
            full_caption = caption
            if tags:
                tag_str = " ".join([f"#{t.strip()}" for t in tags])
                full_caption = f"{caption}\n\n{tag_str}"
            
            caption_field.clear()
            caption_field.send_keys(full_caption)
            
            time.sleep(3)
            
            # Click post button
            post_btn = self.driver.find_element(By.XPATH, '//button[contains(text(), "Post")]')
            post_btn.click()
            
            time.sleep(10)
            
            # Check success
            if "upload" not in self.driver.current_url.lower():
                success("Video uploaded to TikTok!")
                return {"success": True, "url": "https://www.tiktok.com", "error": None}
            else:
                return {"success": False, "error": "Upload may have failed"}
                
        except Exception as e:
            error(f"TikTok upload failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if self.driver:
                self.driver.quit()
    
    def close(self):
        if self.driver:
            self.driver.quit()


class InstagramUploader:
    """Instagram Reels video uploader using Selenium."""
    
    def __init__(self, firefox_profile_path: str):
        self.firefox_profile_path = firefox_profile_path
        self.driver = None
    
    def _init_driver(self):
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        
        options = Options()
        options.profile = self.firefox_profile_path
        options.headless = True
        
        self.driver = webdriver.Firefox(options=options)
        self.driver.implicitly_wait(15)
    
    def upload(self, video_path: str, caption: str, tags: list = None) -> dict:
        """Upload video to Instagram Reels.
        
        Args:
            video_path: Path to video file
            caption: Video caption
            tags: List of hashtags
            
        Returns:
            dict with success, url, error
        """
        try:
            self._init_driver()
            
            # Navigate to Instagram
            self.driver.get("https://www.instagram.com/")
            time.sleep(5)
            
            # Check if logged in
            if "login" in self.driver.current_url.lower():
                return {"success": False, "error": "Not logged in to Instagram"}
            
            # Click create button
            from selenium.webdriver.common.by import By
            create_btn = self.driver.find_element(By.CSS_SELECTOR, '[aria-label="New post"]')
            create_btn.click()
            
            time.sleep(3)
            
            # Select Reel
            reel_option = self.driver.find_element(By.XPATH, '//span[contains(text(), "Reel")]')
            reel_option.click()
            
            time.sleep(2)
            
            # Upload video
            upload_input = self.driver.find_element(By.CSS_SELECTOR, 'input[type="file"][accept*="video"]')
            upload_input.send_keys(os.path.abspath(video_path))
            
            time.sleep(10)  # Wait for processing
            
            # Click next
            next_btn = self.driver.find_element(By.XPATH, '//button[contains(text(), "Next")]')
            next_btn.click()
            
            time.sleep(3)
            
            # Add caption
            caption_field = self.driver.find_element(By.CSS_SELECTOR, 'textarea[aria-label]')
            full_caption = caption
            if tags:
                tag_str = " ".join([f"#{t.strip()}" for t in tags])
                full_caption = f"{caption}\n\n{tag_str}"
            
            caption_field.clear()
            caption_field.send_keys(full_caption)
            
            time.sleep(2)
            
            # Click share
            share_btn = self.driver.find_element(By.XPATH, '//button[contains(text(), "Share")]')
            share_btn.click()
            
            time.sleep(10)
            
            success("Video uploaded to Instagram Reels!")
            return {"success": True, "url": "https://www.instagram.com", "error": None}
                
        except Exception as e:
            error(f"Instagram upload failed: {e}")
            return {"success": False, "error": str(e)}
        finally:
            if self.driver:
                self.driver.quit()
    
    def close(self):
        if self.driver:
            self.driver.quit()


def upload_to_platform(
    platform: str,
    video_path: str,
    caption: str,
    tags: list = None,
    firefox_profile_path: str = None,
) -> dict:
    """Upload video to a specified platform.
    
    Args:
        platform: 'youtube', 'tiktok', or 'instagram'
        video_path: Path to video file
        caption: Video caption/title
        tags: List of tags/hashtags
        firefox_profile_path: Path to Firefox profile
        
    Returns:
        dict with success, url, error
    """
    if platform == "youtube":
        # YouTube upload is handled by the main YouTube class
        return {"success": False, "error": "Use YouTube class for YouTube uploads"}
    
    elif platform == "tiktok":
        if not firefox_profile_path:
            return {"success": False, "error": "Firefox profile path required for TikTok"}
        uploader = TikTokUploader(firefox_profile_path)
        return uploader.upload(video_path, caption, tags)
    
    elif platform == "instagram":
        if not firefox_profile_path:
            return {"success": False, "error": "Firefox profile path required for Instagram"}
        uploader = InstagramUploader(firefox_profile_path)
        return uploader.upload(video_path, caption, tags)
    
    else:
        return {"success": False, "error": f"Unknown platform: {platform}"}


def get_supported_platforms() -> list:
    """Get list of supported platforms."""
    return ["youtube", "tiktok", "instagram"]


if __name__ == "__main__":
    print("Supported platforms:", get_supported_platforms())
