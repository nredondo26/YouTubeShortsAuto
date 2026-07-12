"""YouTube Shorts pipeline: topic -> script -> metadata -> images -> TTS -> video -> upload.

Major fixes over the original:
- No unbounded recursion in generate_script/generate_metadata/generate_prompts
- Proper exception handling (no bare except)
- Retry limits configurable via config.json
- Explicit imports (no wildcards)
- Clean separation of concerns
"""

import re
import json
import time
import os
import base64
import requests

from uuid import uuid4
from typing import Optional
from datetime import datetime

from moviepy import (
    AudioFileClip,
    ImageClip,
    TextClip,
    CompositeAudioClip,
    CompositeVideoClip,
    concatenate_videoclips,
    vfx,
    afx,
)
from moviepy.video.tools.subtitles import SubtitlesClip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager

from src.config import (
    ROOT_DIR,
    MP_DIR,
    get_verbose,
    get_headless,
    get_firefox_profile_path,
    get_threads,
    get_is_for_kids,
    get_font,
    get_fonts_dir,
    get_script_sentence_length,
    get_subtitle_max_chars,
    get_subtitle_color,
    get_subtitle_stroke_color,
    get_subtitle_stroke_width,
    get_subtitle_font_size,
    get_subtitle_position,
    get_subtitle_max_width,
    get_subtitle_bg_alpha,
    get_subtitle_text_alpha,
    get_nanobanana2_api_key,
    get_nanobanana2_api_base_url,
    get_nanobanana2_model,
    get_nanobanana2_aspect_ratio,
    get_stt_provider,
    get_assemblyai_api_key,
    get_whisper_model,
    get_whisper_device,
    get_whisper_compute_type,
    get_max_script_retries,
    get_max_metadata_retries,
    get_max_prompts_retries,
)
from src.llm import generate_text
from src.tts import TTS
from src.cache import add_video, get_videos
from src.utils import build_youtube_url, choose_random_song
from src.status import info, success, warning, error
from src.constants import (
    YOUTUBE_TEXTBOX_ID,
    YOUTUBE_MADE_FOR_KIDS_NAME,
    YOUTUBE_NOT_MADE_FOR_KIDS_NAME,
    YOUTUBE_NEXT_BUTTON_ID,
    YOUTUBE_RADIO_BUTTON_XPATH,
    YOUTUBE_DONE_BUTTON_ID,
)


class YouTube:
    """Automated YouTube Shorts pipeline."""

    def __init__(
        self,
        account_uuid: str,
        account_nickname: str,
        fp_profile_path: str,
        niche: str,
        language: str,
    ) -> None:
        self._account_uuid = account_uuid
        self._account_nickname = account_nickname
        self._niche = niche
        self._language = language

        self.images: list[str] = []
        self.subject: str = ""
        self.script: str = ""
        self.metadata: dict = {}
        self.image_prompts: list[str] = []
        self.tts_path: str = ""
        self.video_path: str = ""
        self.thumbnail_path: str = ""
        self.channel_id: str = ""
        self.uploaded_video_url: str = ""

        # Firefox setup - lazy initialization
        if not os.path.isdir(fp_profile_path):
            raise ValueError(f"Firefox profile path does not exist: {fp_profile_path}")

        self._fp_profile_path = fp_profile_path
        self.browser = None
        self._browser_initialized = False

    def _init_browser(self) -> None:
        """Initialize browser lazily - only when needed for upload."""
        if self._browser_initialized:
            return
        
        self.options = Options()
        if get_headless():
            self.options.add_argument("--headless")
        self.options.add_argument("-profile")
        self.options.add_argument(self._fp_profile_path)
        self.service = Service(GeckoDriverManager().install())
        self.browser = webdriver.Firefox(service=self.service, options=self.options)
        self._browser_initialized = True

    def close(self) -> None:
        """Safely close the browser."""
        try:
            if self.browser and self._browser_initialized:
                self.browser.quit()
                self.browser = None
                self._browser_initialized = False
        except Exception:
            pass

    # ──────────────────────────────────────────────
    # LLM Generation
    # ──────────────────────────────────────────────

    def _generate(self, prompt: str, model_name: Optional[str] = None) -> str:
        return generate_text(prompt, model_name=model_name)

    def generate_topic(self) -> str:
        """Generate a unique video topic based on the channel niche."""
        # Get previously generated topics to avoid repetition
        previous_videos = get_videos(self._account_uuid)
        previous_topics = [v.get("title", "") for v in previous_videos[-10:]]
        
        avoid_text = ""
        if previous_topics:
            avoid_text = (
                f"\n\nIMPORTANT: These topics have been used recently, DO NOT repeat them:\n"
                + "\n".join(f"- {t}" for t in previous_topics)
                + "\n\nGenerate something COMPLETELY DIFFERENT and UNIQUE."
            )

        completion = self._generate(
            f"Generate a specific video idea about: {self._niche}. "
            f"Make it exactly one sentence. Only return the topic, nothing else."
            f"{avoid_text}"
        )
        if not completion:
            raise RuntimeError("Failed to generate topic (empty response from LLM).")

        self.subject = completion
        info(f"Topic: {self.subject}")
        return completion

    def generate_script(self, _retries: int = 0) -> str:
        """Generate a script with bounded retries."""
        max_retries = get_max_script_retries()
        sentence_length = get_script_sentence_length()

        prompt = f"""Generate a script for a video in {sentence_length} sentences about: {self.subject}

Rules:
- Write in {self._language}.
- Do NOT exceed {sentence_length} sentences. Keep sentences SHORT.
- Do NOT use any markdown, formatting, titles, or labels like "NARRATOR:".
- Do NOT reference this prompt or talk about the script itself.
- Get straight to the point. Do NOT start with "welcome to this video".
- ONLY return the raw script text.

Subject: {self.subject}
Language: {self._language}"""

        completion = self._generate(prompt)
        completion = re.sub(r"\*", "", completion)

        if not completion:
            if _retries < max_retries:
                warning(f"Empty script, retrying ({_retries + 1}/{max_retries})...")
                return self.generate_script(_retries + 1)
            raise RuntimeError("Failed to generate script after max retries.")

        if len(completion) > 5000:
            if _retries < max_retries:
                warning(f"Script too long ({len(completion)} chars), retrying ({_retries + 1}/{max_retries})...")
                return self.generate_script(_retries + 1)
            raise RuntimeError(f"Script still too long after {max_retries} retries.")

        self.script = completion
        info(f"Script generated ({len(completion)} chars)")
        return completion

    def generate_metadata(self, _retries: int = 0) -> dict:
        """Generate video title and description with bounded retries."""
        max_retries = get_max_metadata_retries()

        title = self._generate(
            f"Generate a YouTube Video Title for: {self.subject}. "
            "Include hashtags. Only return the title. Limit under 100 characters."
        )

        if len(title) > 100:
            if _retries < max_retries:
                warning(f"Title too long ({len(title)} chars), retrying ({_retries + 1}/{max_retries})...")
                return self.generate_metadata(_retries + 1)
            title = title[:97] + "..."

        description = self._generate(
            f"Generate a YouTube Video Description for this script: {self.script}. "
            "Only return the description, nothing else."
        )

        self.metadata = {"title": title, "description": description}
        info(f"Metadata: {title[:60]}...")
        return self.metadata

    def generate_prompts(self, _retries: int = 0) -> list[str]:
        """Generate AI image prompts with bounded retries."""
        max_retries = get_max_prompts_retries()
        n_prompts = min(8, max(3, int(len(self.script) / 3)))

        prompt = f"""Generate exactly {n_prompts} AI Image Prompts for a video about: {self.subject}

Rules:
- Return ONLY a JSON array of strings.
- Each prompt should be a full sentence with descriptive adjectives.
- Prompts must relate to the video subject.
- MUST return exactly {n_prompts} prompts, no more.
- Example format: ["prompt 1", "prompt 2", "prompt 3"]

Full script for context:
{self.script}"""

        completion = self._generate(prompt)
        completion = str(completion).replace("```json", "").replace("```", "")

        image_prompts: list[str] = []

        if "image_prompts" in completion:
            try:
                image_prompts = json.loads(completion)["image_prompts"]
            except (json.JSONDecodeError, KeyError):
                pass
        else:
            try:
                parsed = json.loads(completion)
                if isinstance(parsed, list):
                    image_prompts = parsed
            except json.JSONDecodeError:
                match = re.search(r"\[.*\]", completion, re.DOTALL)
                if match:
                    try:
                        image_prompts = json.loads(match.group())
                    except json.JSONDecodeError:
                        pass

        if not image_prompts:
            if _retries < max_retries:
                warning(f"Failed to parse image prompts, retrying ({_retries + 1}/{max_retries})...")
                return self.generate_prompts(_retries + 1)
            raise RuntimeError(f"Failed to generate image prompts after {max_retries} retries.")

        image_prompts = [str(p) for p in image_prompts[:n_prompts]]
        self.image_prompts = image_prompts
        success(f"Generated {len(image_prompts)} image prompts.")
        return image_prompts

    # ──────────────────────────────────────────────
    # Image Generation
    # ──────────────────────────────────────────────

    def _persist_image(self, image_bytes: bytes, provider_label: str) -> str:
        image_path = os.path.join(MP_DIR, f"img_{uuid4()}.png")
        with open(image_path, "wb") as f:
            f.write(image_bytes)
        self.images.append(image_path)
        if get_verbose():
            info(f"Image saved from {provider_label}: {image_path}")
        return image_path

    def _generate_image_pollinations(self, prompt: str) -> Optional[str]:
        """Generate image using Pollinations AI (free, no API key needed)."""
        try:
            import urllib.parse
            encoded_prompt = urllib.parse.quote(prompt)
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1080&height=1920&nologo=true&seed={int(time.time())}"

            response = requests.get(url, timeout=120)
            if response.status_code == 200 and len(response.content) > 1000:
                return self._persist_image(response.content, "Pollinations AI")
            else:
                warning(f"Pollinations returned invalid response ({len(response.content)} bytes)")
                return None
        except Exception as e:
            warning(f"Pollinations failed: {e}")
            return None

    def _generate_image_gemini(self, prompt: str) -> Optional[str]:
        """Generate image using Gemini API."""
        api_key = get_nanobanana2_api_key()
        if not api_key:
            return None

        base_url = get_nanobanana2_api_base_url().rstrip("/")
        model = get_nanobanana2_model()
        aspect_ratio = get_nanobanana2_aspect_ratio()

        endpoint = f"{base_url}/models/{model}:generateContent"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseModalities": ["IMAGE"],
                "imageConfig": {"aspectRatio": aspect_ratio},
            },
        }

        try:
            response = requests.post(
                endpoint,
                headers={"x-goog-api-key": api_key, "Content-Type": "application/json"},
                json=payload,
                timeout=120,
            )
            if response.status_code == 429:
                return None

            response.raise_for_status()
            body = response.json()

            for candidate in body.get("candidates", []):
                for part in candidate.get("content", {}).get("parts", []):
                    inline_data = part.get("inlineData") or part.get("inline_data")
                    if not inline_data:
                        continue
                    data = inline_data.get("data")
                    mime = inline_data.get("mimeType") or inline_data.get("mime_type", "")
                    if data and str(mime).startswith("image/"):
                        return self._persist_image(base64.b64decode(data), "Gemini")
            return None
        except Exception:
            return None

    def generate_image(self, prompt: str, max_retries: int = 3) -> Optional[str]:
        """Generate image using Pollinations AI (primary) with Gemini fallback."""
        for attempt in range(1, max_retries + 1):
            # Try Pollinations AI first (free, no key needed)
            result = self._generate_image_pollinations(prompt)
            if result:
                return result

            # Fallback to Gemini if Pollinations fails
            result = self._generate_image_gemini(prompt)
            if result:
                return result

            if attempt < max_retries:
                warning(f"Image generation failed, retry {attempt}/{max_retries}...")
                time.sleep(3)

        warning(f"Failed to generate image after {max_retries} retries.")
        return None

    def generate_all_images(self) -> None:
        """Generate images for all prompts with delay between requests."""
        for i, prompt in enumerate(self.image_prompts):
            info(f"Generating image {i + 1}/{len(self.image_prompts)}: {prompt[:60]}...")
            self.generate_image(prompt)
            # Small delay between requests
            if i < len(self.image_prompts) - 1:
                time.sleep(3)

        if not self.images:
            raise RuntimeError("No images were generated. Cannot create video.")

        success(f"Generated {len(self.images)} images.")

    def generate_thumbnail(self) -> Optional[str]:
        """Generate a thumbnail for the video using AI."""
        prompt = f"""Generate a YouTube Shorts thumbnail for a video about: {self.subject}

Rules:
- The thumbnail should be eye-catching and clickbait-worthy
- Use bright colors and bold composition
- Include visual elements that represent the topic
- Make it dramatic and attention-grabbing
- Return ONLY the image, no text overlay needed
- Aspect ratio: 9:16 (vertical)"""

        info("Generating thumbnail...")
        thumbnail_path = self.generate_image(prompt)
        if thumbnail_path:
            success(f"Thumbnail saved: {thumbnail_path}")
            self.thumbnail_path = thumbnail_path
        return thumbnail_path

    # ──────────────────────────────────────────────
    # Subtitles
    # ──────────────────────────────────────────────

    @staticmethod
    def _format_srt_timestamp(seconds: float) -> str:
        total_millis = max(0, int(round(seconds * 1000)))
        hours = total_millis // 3600000
        minutes = (total_millis % 3600000) // 60000
        secs = (total_millis % 60000) // 1000
        millis = total_millis % 1000
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    def generate_subtitles(self, audio_path: str) -> str:
        """Generate SRT subtitles from audio using the configured STT provider."""
        provider = get_stt_provider().lower()
        if provider == "third_party_assemblyai":
            return self._generate_subtitles_assemblyai(audio_path)
        return self._generate_subtitles_whisper(audio_path)

    def _generate_subtitles_assemblyai(self, audio_path: str) -> str:
        import assemblyai as aai

        aai.settings.api_key = get_assemblyai_api_key()
        transcriber = aai.Transcriber(config=aai.TranscriptionConfig())
        transcript = transcriber.transcribe(audio_path)
        subtitles = transcript.export_subtitles_srt()

        srt_path = os.path.join(MP_DIR, f"subs_{uuid4()}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(subtitles)
        return srt_path

    def _generate_subtitles_whisper(self, audio_path: str) -> str:
        from faster_whisper import WhisperModel

        model = WhisperModel(
            get_whisper_model(),
            device=get_whisper_device(),
            compute_type=get_whisper_compute_type(),
        )
        segments, _ = model.transcribe(audio_path, vad_filter=True)

        lines = []
        idx = 0
        for segment in segments:
            text = str(segment.text).strip()
            if not text:
                continue
            idx += 1
            start = self._format_srt_timestamp(segment.start)
            end = self._format_srt_timestamp(segment.end)
            lines.extend([str(idx), f"{start} --> {end}", text, ""])

        srt_path = os.path.join(MP_DIR, f"subs_{uuid4()}.srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return srt_path

    # ──────────────────────────────────────────────
    # Video Composition
    # ──────────────────────────────────────────────

    def combine(self) -> str:
        """Combine images, audio, subtitles, and music into a final MP4 video."""
        output_path = os.path.join(MP_DIR, f"video_{uuid4()}.mp4")
        threads = get_threads()
        tts_clip = AudioFileClip(self.tts_path)
        max_duration = tts_clip.duration
        req_dur = max_duration / len(self.images)

        font_path = os.path.join(get_fonts_dir(), get_font())
        
        # Get transparency settings
        bg_alpha = int(get("subtitle_bg_alpha", 60))
        text_alpha = int(get("subtitle_text_alpha", 100))

        def make_subtitle_clip(txt: str, start: float, end: float) -> TextClip:
            # Convert hex color to RGBA for transparency
            color = get_subtitle_color()
            if len(color) == 7:  # #RRGGBB
                r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
                alpha = int(text_alpha * 2.55)
                text_color = f"#{color[1:]}{'%02x' % alpha}"
            else:
                text_color = color
            
            clip = TextClip(
                text=txt,
                font=font_path,
                font_size=get_subtitle_font_size(),
                color=text_color,
                stroke_color=get_subtitle_stroke_color(),
                stroke_width=get_subtitle_stroke_width(),
                size=(get_subtitle_max_width(), None),
                method="caption",
            )
            clip = clip.with_start(start)
            clip = clip.with_duration(end - start)
            
            # Position based on config
            position = get_subtitle_position()
            if position == "top":
                clip = clip.with_position(("center", 50))
            elif position == "bottom":
                clip = clip.with_position(("center", -50))
            else:  # center
                clip = clip.with_position(("center", "center"))
            
            return clip

        info("Compositing video clips...")
        clips = []
        total_dur = 0.0

        while total_dur < max_duration:
            for image_path in self.images:
                clip = ImageClip(image_path)
                clip = clip.with_duration(req_dur)
                clip = clip.with_fps(30)

                aspect = round(clip.w / clip.h, 4)
                if aspect < 0.5625:
                    clip = clip.with_effects([vfx.Crop(
                        x_center=clip.w / 2,
                        y_center=clip.h / 2,
                        width=clip.w,
                        height=round(clip.w / 0.5625),
                    )])
                else:
                    clip = clip.with_effects([vfx.Crop(
                        x_center=clip.w / 2,
                        y_center=clip.h / 2,
                        width=round(0.5625 * clip.h),
                        height=clip.h,
                    )])
                clip = clip.with_effects([vfx.Resize((1080, 1920))])
                clips.append(clip)
                total_dur += clip.duration

        final_clip = concatenate_videoclips(clips).with_fps(30)

        # Subtitles - manual implementation to avoid SubtitlesClip bug
        subtitle_clips = []
        try:
            srt_path = self.generate_subtitles(self.tts_path)
            import srt_equalizer
            srt_equalizer.equalize_srt_file(srt_path, srt_path, get_subtitle_max_chars())
            import srt
            with open(srt_path, "r", encoding="utf-8") as f:
                subs = list(srt.parse(f.read()))
            for sub in subs:
                try:
                    sub_clip = make_subtitle_clip(sub.content, sub.start.total_seconds(), sub.end.total_seconds())
                    subtitle_clips.append(sub_clip)
                except Exception:
                    pass
            if subtitle_clips:
                success(f"Created {len(subtitle_clips)} subtitle clips")
        except Exception as e:
            warning(f"Subtitle generation failed, continuing without: {e}")

        # Background music
        song_path = choose_random_song()
        if song_path:
            music_clip = AudioFileClip(song_path).with_fps(44100)
            music_clip = music_clip.with_effects([afx.MultiplyVolume(0.1)])
            audio = CompositeAudioClip([tts_clip.with_fps(44100), music_clip])
        else:
            audio = CompositeAudioClip([tts_clip.with_fps(44100)])

        final_clip = final_clip.with_audio(audio)
        final_clip = final_clip.with_duration(tts_clip.duration)

        if subtitle_clips:
            final_clip = CompositeVideoClip([final_clip] + subtitle_clips)

        final_clip.write_videofile(
            output_path,
            threads=threads,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            ffmpeg_params=["-crf", "28"],
            logger=None,
        )

        success(f"Video saved: {output_path}")
        return output_path

    # ──────────────────────────────────────────────
    # Full Pipeline
    # ──────────────────────────────────────────────

    def generate_video(self, tts: TTS) -> str:
        """Run the full YouTube Shorts generation pipeline.

        Returns:
            Path to the generated MP4 file.
        """
        self.generate_topic()
        self.generate_script()
        self.generate_metadata()
        self.generate_prompts()
        self.generate_all_images()
        self.generate_thumbnail()

        # Clean script for TTS (remove non-speech characters)
        clean_script = re.sub(r"[^\w\s.?!]", "", self.script)
        self.tts_path = tts.synthesize(clean_script)

        self.video_path = os.path.abspath(self.combine())
        info(f"Full pipeline complete: {self.video_path}")
        return self.video_path

    # ──────────────────────────────────────────────
    # YouTube Upload via Selenium
    # ──────────────────────────────────────────────

    def get_channel_id(self) -> str:
        """Navigate to YouTube Studio and extract the channel ID."""
        self._init_browser()
        self.browser.get("https://studio.youtube.com")
        time.sleep(3)
        self.channel_id = self.browser.current_url.split("/")[-1]
        return self.channel_id

    def upload_video(self) -> bool:
        """Upload the generated video to YouTube as unlisted via Selenium."""
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys

        try:
            # Initialize browser if not already done
            self._init_browser()
            
            self.get_channel_id()
            driver = self.browser

            # Navigate to upload page
            driver.get("https://www.youtube.com/upload")
            time.sleep(5)

            # Select file
            file_picker = driver.find_element(By.TAG_NAME, "ytcp-uploads-file-picker")
            file_input = file_picker.find_element(By.TAG_NAME, "input")
            file_input.send_keys(self.video_path)
            time.sleep(10)

            # Set title - find all textbox elements
            info("Setting title...")
            try:
                title_box = driver.find_element(By.ID, "title-textarea")
                inner = title_box.find_element(By.CSS_SELECTOR, "div[contenteditable='true'], #text, ytcp-textarea-counter")
                inner.click()
                time.sleep(0.5)
                ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
                time.sleep(0.2)
                ActionChains(driver).send_keys(self.metadata["title"]).perform()
            except Exception:
                try:
                    title_box = driver.find_element(By.ID, "title-textarea")
                    title_box.click()
                    time.sleep(0.5)
                    ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
                    time.sleep(0.2)
                    ActionChains(driver).send_keys(self.metadata["title"]).perform()
                except Exception:
                    warning("Could not set title via Selenium, trying JS fallback")
                    driver.execute_script(f"""
                        var containers = document.querySelectorAll('ytcp-textarea-counter, ycp-form-textarea');
                        for (var c of containers) {{
                            var d = c.querySelector('[contenteditable]');
                            if (d) {{
                                d.focus();
                                d.innerText = '{self.metadata["title"]}';
                                d.dispatchEvent(new Event('input', {{bubbles: true}}));
                                d.dispatchEvent(new Event('change', {{bubbles: true}}));
                                break;
                            }}
                        }}
                    """)
            time.sleep(2)

            # Set description
            info("Setting description...")
            try:
                desc_box = driver.find_element(By.ID, "description-textarea")
                inner = desc_box.find_element(By.CSS_SELECTOR, "div[contenteditable='true'], #text, ytcp-textarea-counter")
                inner.click()
                time.sleep(0.5)
                ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
                time.sleep(0.2)
                ActionChains(driver).send_keys(self.metadata["description"]).perform()
            except Exception:
                try:
                    desc_box = driver.find_element(By.ID, "description-textarea")
                    desc_box.click()
                    time.sleep(0.5)
                    ActionChains(driver).key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
                    time.sleep(0.2)
                    ActionChains(driver).send_keys(self.metadata["description"]).perform()
                except Exception:
                    warning("Could not set description via Selenium, trying JS fallback")
                    driver.execute_script(f"""
                        var containers = document.querySelectorAll('ytcp-textarea-counter, ycp-form-textarea');
                        for (var c of containers) {{
                            var d = c.querySelector('[contenteditable]');
                            if (d && d !== document.querySelector('#title-textarea [contenteditable]')) {{
                                d.focus();
                                d.innerText = '{self.metadata["description"]}';
                                d.dispatchEvent(new Event('input', {{bubbles: true}}));
                                d.dispatchEvent(new Event('change', {{bubbles: true}}));
                                break;
                            }}
                        }}
                    """)
            time.sleep(2)

            # Set kids option
            info("Setting kids option...")
            kids_set = driver.execute_script(f"""
                var names = ['{YOUTUBE_NOT_MADE_FOR_KIDS_NAME}', 'NOT_MADE_FOR_KIDS'];
                for (var n of names) {{
                    var r = document.querySelector('[name=\"' + n + '\"]');
                    if (r) {{ r.click(); return 'name:' + n; }}
                }}
                var radios = document.querySelectorAll('tp-yt-paper-radio-button');
                for (var i = 0; i < radios.length; i++) {{
                    var txt = radios[i].textContent.toLowerCase();
                    var nm = (radios[i].getAttribute('name') || '').toLowerCase();
                    if (txt.includes('no') && txt.includes('kid') || nm.includes('not_mfk') || nm.includes('not_made')) {{
                        radios[i].click(); return 'radio:' + i;
                    }}
                }}
                if (radios.length >= 2) {{ radios[1].click(); return 'fallback:1'; }}
                return null;
            """)
            info(f"Kids option: {kids_set}")
            time.sleep(1)

            # Navigate through upload wizard (3x Next)
            for step in range(1, 4):
                info(f"Clicking next ({step}/3)...")
                driver.execute_script(f"""
                    var btn = document.querySelector('#{YOUTUBE_NEXT_BUTTON_ID}');
                    if (!btn) btn = document.querySelector('ytcp-button#next-button, [id="next-button"]');
                    if (btn) btn.click();
                """)
                time.sleep(3)

            # Set as unlisted
            info("Setting as unlisted...")
            driver.execute_script("""
                var radios = document.querySelectorAll('tp-yt-paper-radio-button');
                for (var i = 0; i < radios.length; i++) {
                    var text = radios[i].textContent.trim().toLowerCase();
                    var name = (radios[i].getAttribute('name') || '').toLowerCase();
                    if (text.includes('unlisted') || text.includes('no listado') || name.includes('unlisted')) {
                        radios[i].click(); break;
                    }
                }
            """)
            time.sleep(1)

            # Click done
            info("Finalizing upload...")
            driver.execute_script(f"""
                var btn = document.querySelector('#{YOUTUBE_DONE_BUTTON_ID}');
                if (!btn) btn = document.querySelector('ytcp-button#done-button, [id="done-button"]');
                if (btn) btn.click();
            """)
            time.sleep(5)

            # Get the uploaded video URL
            driver.get(f"https://studio.youtube.com/channel/{self.channel_id}/videos/short")
            time.sleep(4)
            videos = driver.find_elements(By.TAG_NAME, "ytcp-video-row")
            if not videos:
                warning("Could not find uploaded video in Studio.")
                return False

            anchor = videos[0].find_element(By.TAG_NAME, "a")
            href = anchor.get_attribute("href")
            video_id = href.split("/")[-2]
            url = build_youtube_url(video_id)
            self.uploaded_video_url = url

            success(f"Uploaded: {url}")

            add_video(
                self._account_uuid,
                {
                    "title": self.metadata["title"],
                    "description": self.metadata["description"],
                    "url": url,
                    "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                },
            )

            self.browser.quit()
            return True

        except Exception as e:
            error(f"Upload failed: {e}")
            try:
                self.browser.quit()
            except Exception:
                pass
            return False

    def get_videos(self) -> list[dict]:
        """Get previously uploaded videos for this account."""
        return get_videos(self._account_uuid)
