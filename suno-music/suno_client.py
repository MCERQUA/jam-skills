#!/usr/bin/env python3
"""
Suno API Client for OpenClaw
Official SunoAPI.org client with full 20 endpoint support
Generates AI music and saves to OpenVoiceUI generated_music folder
"""

import os
import json
import requests
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path


class SunoMusicClient:
    """Client for interacting with official Suno API at sunoapi.org"""

    def __init__(
        self,
        api_base: str = None,
        api_key: str = None,
        callback_url: str = None,
        output_dir: str = "/home/mike/WEBSITES/OpenVoiceUI/generated_music"
    ):
        """
        Initialize Suno client

        Args:
            api_base: API base URL (defaults to https://api.sunoapi.org)
            api_key: API key (defaults to SUNO_API_KEY env var)
            callback_url: Webhook callback URL (defaults to SUNO_CALLBACK_URL env var)
            output_dir: Directory to save generated music
        """
        self.api_base = api_base or os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org")
        self.api_key = api_key or os.environ.get("SUNO_API_KEY", "")
        self.callback_url = callback_url or os.environ.get("SUNO_CALLBACK_URL", "")
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Metadata file (uses filename as key for OpenVoiceUI)
        self.metadata_file = self.output_dir / "generated_metadata.json"
        self._load_metadata()

        # Session with Bearer token authentication
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            })
        else:
            self.session.headers.update({"Content-Type": "application/json"})

    def _get_callback_url(self, provided_hook_url: Optional[str] = None) -> Optional[str]:
        """
        Get callback URL to use (priority: provided -> class callback_url -> None)

        Args:
            provided_hook_url: Hook URL provided to method

        Returns:
            URL to use for callbacks, or None if not set
        """
        if provided_hook_url:
            return provided_hook_url
        return self.callback_url or None

    def _prepare_payload_with_callback(self, payload: Dict, hook_url: Optional[str] = None) -> Dict:
        """
        Add hookUrl to payload if callbacks are configured

        Args:
            payload: Base payload
            hook_url: Optional override hook URL

        Returns:
            Payload with hookUrl added if configured
        """
        callback = self._get_callback_url(hook_url)
        if callback:
            payload["hookUrl"] = callback
        return payload

    def _load_metadata(self):
        """Load existing metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                self.metadata = json.load(f)
        else:
            self.metadata = {}

    def _save_metadata(self):
        """Save metadata to file"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)

    def _add_song_metadata(self, filename: str, data: Dict[str, Any], instrumental: bool = False):
        """Add song metadata to tracking using OpenVoiceUI format (filename as key)"""
        # Determine energy from prompt
        prompt = data.get("prompt", data.get("description", ""))
        prompt_lower = prompt.lower()
        if any(w in prompt_lower for w in ["heavy", "aggressive", "epic", "intense", "powerful"]):
            energy = "high"
        elif any(w in prompt_lower for w in ["chill", "calm", "relaxing", "soft", "mellow"]):
            energy = "low"
        else:
            energy = "medium"

        entry = {
            "title": data.get("title", "Untitled"),
            "description": prompt[:200] if len(prompt) > 200 else prompt,
            "genre": data.get("style", data.get("genre", "AI-Generated")),
            "energy": energy,
            "themes": [],
            "duration_seconds": data.get("duration", 0),
            "fun_facts": [],
            "dj_intro_hints": [],
            "dj_backstory": "Fresh from the AI oven.",
            "made_by": "Clawdbot",
            "created_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "suno_id": data.get("id", str(uuid.uuid4())),
            "artist": "Clawdbot AI"
        }

        self.metadata[filename] = entry
        self._save_metadata()
        return entry

    # ========================================
    # MUSIC GENERATION APIs (6 endpoints)
    # ========================================

    def generate_from_prompt(
        self,
        prompt: str,
        instrumental: bool = False,
        model: str = "v5",
        gpt_description: str = None,
        hook_url: str = None,
        wait_for_completion: bool = True,
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Generate music from a text description

        Args:
            prompt: Music description
            instrumental: Generate instrumental only (no lyrics)
            model: Model version (v4, v4_5, v4_5PLUS, v4_5ALL, v5)
            gpt_description: Optional inspiration prompt
            hook_url: Webhook URL for completion notification
            wait_for_completion: Wait for generation to complete
            timeout: Max seconds to wait for completion

        Returns:
            Dict with song data and saved file path
        """
        endpoint = f"{self.api_base}/generate"

        payload = {
            "custom": False,
            "instrumental": instrumental,
            "mv": model,
            "prompt": prompt
        }

        if gpt_description:
            payload["gpt_description_prompt"] = gpt_description

        payload = self._prepare_payload_with_callback(payload, hook_url)

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True) or "data" not in data:
            raise ValueError(f"Generation failed: {data}")

        songs = data["data"]
        if not songs:
            raise ValueError("No songs returned")

        song = songs[0]

        # Download audio
        filename = self._download_song(song, prompt)
        metadata = self._add_song_metadata(filename, {
            "title": song.get("title"),
            "prompt": prompt,
            "model": model,
            "style": song.get("style", ""),
            "id": song.get("id"),
            "duration": song.get("duration", 0)
        })

        return {
            "success": True,
            "song": song,
            "filename": filename,
            "path": str(self.output_dir / filename),
            "metadata": metadata
        }

    def generate_custom(
        self,
        lyrics: str,
        title: str,
        tags: str,
        instrumental: bool = False,
        model: str = "v5",
        hook_url: str = None
    ) -> Dict[str, Any]:
        """
        Generate custom song with lyrics and title

        Args:
            lyrics: Custom lyrics
            title: Song title
            tags: Comma-separated style tags
            instrumental: Generate instrumental only
            model: Model version
            hook_url: Webhook URL

        Returns:
            Dict with song data and saved file path
        """
        endpoint = f"{self.api_base}/generate"

        payload = {
            "custom": True,
            "instrumental": instrumental,
            "mv": model,
            "prompt": lyrics,
            "tags": tags,
            "title": title
        }

        payload = self._prepare_payload_with_callback(payload, hook_url)

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True) or "data" not in data:
            raise ValueError(f"Generation failed: {data}")

        songs = data["data"]
        if not songs:
            raise ValueError("No songs returned")

        song = songs[0]

        # Download audio
        filename = self._download_song(song, lyrics)
        metadata = self._add_song_metadata(filename, {
            "title": title,
            "prompt": lyrics,
            "model": model,
            "style": tags,
            "id": song.get("id"),
            "duration": song.get("duration", 0)
        })

        return {
            "success": True,
            "song": song,
            "filename": filename,
            "path": str(self.output_dir / filename),
            "metadata": metadata
        }

    def extend_audio(
        self,
        audio_id: str,
        extension_prompt: str = "continue the melody",
        model: str = "v5"
    ) -> Dict[str, Any]:
        """
        Extend an existing audio track

        Args:
            audio_id: Song ID to extend
            extension_prompt: Instructions for extension
            model: Model version

        Returns:
            Dict with extended song data
        """
        endpoint = f"{self.api_base}/extend"

        payload = {
            "aid": audio_id,
            "bark_prompt": extension_prompt,
            "mv": model,
            "prompt": extension_prompt
        }

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Extension failed: {data}")

        return data

    def upload_and_cover(
        self,
        audio_url: str,
        cover_prompt: str,
        model: str = "v5"
    ) -> Dict[str, Any]:
        """
        Transform existing audio into new styles

        Args:
            audio_url: URL of audio to transform
            cover_prompt: Description of desired style
            model: Model version

        Returns:
            Dict with transformed audio data
        """
        endpoint = f"{self.api_base}/upload_and_cover"

        payload = {
            "audio_url": audio_url,
            "cover_prompt": cover_prompt,
            "mv": model
        }

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Cover failed: {data}")

        return data

    def upload_and_extend(
        self,
        audio_url: str,
        extend_prompt: str,
        model: str = "v5"
    ) -> Dict[str, Any]:
        """
        Upload audio and extend it with AI content

        Args:
            audio_url: URL of audio to extend
            extend_prompt: Extension instructions
            model: Model version

        Returns:
            Dict with extended audio data
        """
        endpoint = f"{self.api_base}/upload_and_extend"

        payload = {
            "audio_url": audio_url,
            "extend_prompt": extend_prompt,
            "mv": model
        }

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Extend failed: {data}")

        return data

    def add_vocals(
        self,
        audio_url: str,
        lyric: str,
        model: str = "v5"
    ) -> Dict[str, Any]:
        """
        Generate vocal tracks for instrumental music

        Args:
            audio_url: URL of instrumental audio
            lyric: Lyrics for the vocal track
            model: Model version

        Returns:
            Dict with vocal-added audio data
        """
        endpoint = f"{self.api_base}/add_vocals"

        payload = {
            "audio_url": audio_url,
            "lyric": lyric,
            "mv": model
        }

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Add vocals failed: {data}")

        return data

    def add_instrumental(
        self,
        audio_url: str,
        model: str = "v5",
        tags: str = ""
    ) -> Dict[str, Any]:
        """
        Create instrumental accompaniment for vocal tracks

        Args:
            audio_url: URL of vocal-only audio
            model: Model version
            tags: Style tags for accompaniment

        Returns:
            Dict with instrumental-added audio data
        """
        endpoint = f"{self.api_base}/add_instrumental"

        payload = {
            "audio_url": audio_url,
            "mv": model
        }

        if tags:
            payload["tags"] = tags

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Add instrumental failed: {data}")

        return data

    def cover_music(
        self,
        audio_url: str,
        cover_prompt: str,
        model: str = "v5"
    ) -> Dict[str, Any]:
        """
        Reinterpret existing music in different styles

        Args:
            audio_url: URL of original audio
            cover_prompt: Description of desired style
            model: Model version

        Returns:
            Dict with cover audio data
        """
        endpoint = f"{self.api_base}/cover"

        payload = {
            "audio_url": audio_url,
            "cover_prompt": cover_prompt,
            "mv": model
        }

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Cover failed: {data}")

        return data

    # ========================================
    # LYRICS CREATION APIs (2 endpoints)
    # ========================================

    def generate_lyrics(self, prompt: str, tags: str = "") -> str:
        """
        Generate lyrics only (without music)

        Args:
            prompt: Lyrics generation prompt
            tags: Style tags

        Returns:
            Generated lyrics string
        """
        endpoint = f"{self.api_base}/generate_lyrics"

        payload = {
            "prompt": prompt,
            "tags": tags
        }

        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Lyrics generation failed: {data}")

        return data.get("data", {}).get("lyric", "")

    def get_timestamped_lyrics(self, song_id: str) -> Dict[str, Any]:
        """
        Retrieve lyrics with precise timestamps

        Args:
            song_id: Song ID to get lyrics for

        Returns:
            Dict with timestamped lyrics
        """
        endpoint = f"{self.api_base}/get_lyrics_timeline"

        response = self.session.get(endpoint, params={"song_id": song_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get lyrics failed: {data}")

        return data.get("data", {})

    # ========================================
    # AUDIO PROCESSING APIs (4 endpoints)
    # ========================================

    def separate_vocals(self, audio_url: str) -> Dict[str, Any]:
        """
        Split mixed audio into vocals and instrumental tracks

        Args:
            audio_url: URL of mixed audio

        Returns:
            Dict with vocals_url and instrumental_url
        """
        endpoint = f"{self.api_base}/separate_vocals"

        payload = {"audio_url": audio_url}

        response = self.session.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Separation failed: {data}")

        return data.get("data", {})

    def convert_wav(self, song_id: str) -> Dict[str, Any]:
        """
        Convert music to high-quality WAV format

        Args:
            song_id: Song ID to convert

        Returns:
            Dict with WAV conversion task data
        """
        endpoint = f"{self.api_base}/convert_wav"

        response = self.session.post(endpoint, json={"song_id": song_id}, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"WAV conversion failed: {data}")

        return data.get("data", {})

    def boost_style(
        self,
        audio_url: str,
        boost_prompt: str,
        model: str = "v5"
    ) -> Dict[str, Any]:
        """
        Enhance and refine music styles

        Args:
            audio_url: URL of audio to boost
            boost_prompt: Description of enhancement
            model: Model version

        Returns:
            Dict with boosted audio data
        """
        endpoint = f"{self.api_base}/boost_style"

        payload = {
            "audio_url": audio_url,
            "boost_prompt": boost_prompt,
            "mv": model
        }

        response = self.session.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Style boost failed: {data}")

        return data.get("data", {})

    # ========================================
    # MUSIC VIDEO API (1 endpoint)
    # ========================================

    def create_video(
        self,
        audio_url: str,
        video_prompt: str
    ) -> Dict[str, Any]:
        """
        Generate a music video from audio

        Args:
            audio_url: URL of audio to visualize
            video_prompt: Description of desired visuals

        Returns:
            Dict with video_url and thumbnail_url
        """
        endpoint = f"{self.api_base}/create_video"

        payload = {
            "audio_url": audio_url,
            "video_prompt": video_prompt
        }

        response = self.session.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Video creation failed: {data}")

        return data.get("data", {})

    # ========================================
    # UTILITY APIs (7 endpoints)
    # ========================================

    def get_music_details(self, task_id: str) -> Dict[str, Any]:
        """Get detailed information about a music generation task"""
        endpoint = f"{self.api_base}/get_music_details"

        response = self.session.get(endpoint, params={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get details failed: {data}")

        return data.get("data", {})

    def get_credits(self) -> Dict[str, Any]:
        """Get remaining account credits"""
        endpoint = f"{self.api_base}/get_credits"

        response = self.session.get(endpoint, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get credits failed: {data}")

        return data.get("data", {})

    def get_lyrics_details(self, task_id: str) -> Dict[str, Any]:
        """Get status of lyrics generation task"""
        endpoint = f"{self.api_base}/get_lyrics_details"

        response = self.session.get(endpoint, params={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get lyrics details failed: {data}")

        return data.get("data", {})

    def get_wav_details(self, task_id: str) -> Dict[str, Any]:
        """Get status of WAV conversion task"""
        endpoint = f"{self.api_base}/get_wav_details"

        response = self.session.get(endpoint, params={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get WAV details failed: {data}")

        return data.get("data", {})

    def get_separation_details(self, task_id: str) -> Dict[str, Any]:
        """Get status of vocal separation task"""
        endpoint = f"{self.api_base}/get_separation_details"

        response = self.session.get(endpoint, params={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get separation details failed: {data}")

        return data.get("data", {})

    def get_video_details(self, task_id: str) -> Dict[str, Any]:
        """Get status of music video task"""
        endpoint = f"{self.api_base}/get_video_details"

        response = self.session.get(endpoint, params={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get video details failed: {data}")

        return data.get("data", {})

    def get_cover_details(self, task_id: str) -> Dict[str, Any]:
        """Get status of music cover task"""
        endpoint = f"{self.api_base}/get_cover_details"

        response = self.session.get(endpoint, params={"task_id": task_id}, timeout=10)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True):
            raise ValueError(f"Get cover details failed: {data}")

        return data.get("data", {})

    # ========================================
    # FILE UPLOAD METHODS
    # ========================================

    def generate_from_file(
        self,
        file_path: str,
        title: str = None,
        tags: str = "",
        instrumental: bool = False,
        model: str = "v5",
        hook_url: str = None
    ) -> Dict[str, Any]:
        """
        Generate music by uploading an audio file as reference

        Args:
            file_path: Path to audio file to upload
            title: Optional title for generated song
            tags: Style tags
            instrumental: Generate instrumental only
            model: Model version
            hook_url: Webhook callback URL

        Returns:
            Dict with song data and saved file path
        """
        endpoint = f"{self.api_base}/upload_and_cover"

        # Prepare multipart file upload
        files = {
            "audio": (os.path.basename(file_path), open(file_path, "rb"), "audio/mpeg")
        }

        data = {
            "cover_prompt": tags if tags else "enhance this audio",
            "mv": model
        }

        if title:
            data["title"] = title

        data = self._prepare_payload_with_callback(data, hook_url)

        # Create session without Content-Type for multipart
        upload_session = requests.Session()
        upload_session.headers.update({"Authorization": f"Bearer {self.api_key}"})

        response = upload_session.post(endpoint, files=files, data=data, timeout=60)
        response.raise_for_status()
        data = response.json()

        if not data.get("success", True) or "data" not in data:
            raise ValueError(f"File upload failed: {data}")

        songs = data["data"]
        if not songs:
            raise ValueError("No songs returned")

        song = songs[0]

        # Download audio
        filename = self._download_song(song, title or "uploaded")
        metadata = self._add_song_metadata(filename, {
            "title": song.get("title", title),
            "prompt": f"Uploaded file: {file_path}",
            "model": model,
            "style": tags,
            "id": song.get("id"),
            "duration": song.get("duration", 0)
        })

        return {
            "success": True,
            "song": song,
            "filename": filename,
            "path": str(self.output_dir / filename),
            "metadata": metadata
        }

    def extend_from_file(
        self,
        file_path: str,
        extend_prompt: str = "continue the music",
        model: str = "v5",
        hook_url: str = None
    ) -> Dict[str, Any]:
        """
        Upload and extend an audio file

        Args:
            file_path: Path to audio file to extend
            extend_prompt: Extension instructions
            model: Model version
            hook_url: Webhook callback URL

        Returns:
            Dict with extended song data
        """
        endpoint = f"{self.api_base}/upload_and_extend"

        files = {
            "audio": (os.path.basename(file_path), open(file_path, "rb"), "audio/mpeg")
        }

        data = {
            "extend_prompt": extend_prompt,
            "mv": model
        }

        data = self._prepare_payload_with_callback(data, hook_url)

        upload_session = requests.Session()
        upload_session.headers.update({"Authorization": f"Bearer {self.api_key}"})

        response = upload_session.post(endpoint, files=files, data=data, timeout=60)
        response.raise_for_status()
        result = response.json()

        if not result.get("success", True):
            raise ValueError(f"File extend failed: {result}")

        return result.get("data", {})

    # ========================================
    # WEBHOOK HANDLING
    # ========================================

    def handle_webhook(self, webhook_data: Dict[str, Any]) -> str:
        """
        Process incoming webhook callback from Suno API

        Args:
            webhook_data: JSON data received from webhook POST

        Returns:
            Status message describing the result
        """
        # Typical webhook payload structure:
        # {
        #   "task_id": "task-id",
        #   "status": "complete",
        #   "data": { song data }
        # }

        task_id = webhook_data.get("task_id", "unknown")
        status = webhook_data.get("status", "unknown")
        song_data = webhook_data.get("data", {})

        if status == "complete" and song_data:
            # Download and save the generated music
            audio_url = song_data.get("audio_url")
            if audio_url:
                title = song_data.get("title", "webhook-generated")
                filename = self._download_song(song_data, title)
                metadata = self._add_song_metadata(filename, {
                    "title": title,
                    "prompt": song_data.get("style", "webhook generation"),
                    "model": song_data.get("model", "v5"),
                    "style": song_data.get("style", ""),
                    "id": song_data.get("id"),
                    "duration": song_data.get("duration", 0)
                })
                return f"Webhook processed: Saved {filename} (task: {task_id})"
            else:
                return f"Webhook received complete but no audio URL (task: {task_id})"
        elif status == "failed":
            error = webhook_data.get("error", "unknown error")
            return f"Webhook: Task {task_id} failed: {error}"
        else:
            return f"Webhook: Task {task_id} status: {status}"

    def register_callback(self, callback_url: str) -> Dict[str, Any]:
        """
        Register a callback URL with the client for future requests

        Args:
            callback_url: Full URL for webhook callbacks

        Returns:
            Configuration status
        """
        self.callback_url = callback_url
        return {
            "success": True,
            "callback_url": callback_url,
            "message": "Callback URL registered for future requests"
        }

    # ========================================
    # HELPER METHODS
    # ========================================

    def _download_song(self, song: Dict, prompt: str) -> str:
        """Download and save song audio"""
        audio_url = song.get("audio_url")
        if not audio_url:
            raise ValueError("No audio_url in response")

        # Generate filename
        title = song.get("title", "untitled")
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_title = clean_title.replace(" ", "-")[:50]

        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        filename = f"{clean_title}-{timestamp}.mp3"
        filepath = self.output_dir / filename

        # Download
        audio_response = requests.get(audio_url, timeout=60)
        audio_response.raise_for_status()

        with open(filepath, 'wb') as f:
            f.write(audio_response.content)

        # Set proper permissions
        os.chmod(filepath, 0o644)

        return filename

    def get_local_songs(self) -> List[Dict]:
        """Get list of locally generated songs"""
        return [
            {"filename": filename, **metadata}
            for filename, metadata in self.metadata.items()
            if isinstance(metadata, dict)
        ]

    def get_local_song_metadata(self, filename: str) -> Optional[Dict]:
        """Get metadata for a specific local song"""
        return self.metadata.get(filename)


def main():
    """CLI interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Suno Music Generation CLI (Official API)")
    parser.add_argument("prompt", help="Music description or lyrics")
    parser.add_argument("--title", help="Song title (for custom mode)")
    parser.add_argument("--tags", help="Style tags (for custom mode)")
    parser.add_argument("--instrumental", action="store_true", help="Generate instrumental only")
    parser.add_argument("--model", default="v5", choices=["v4", "v4_5", "v4_5PLUS", "v4_5ALL", "v5"],
                       help="Model version (default: v5)")
    parser.add_argument("--custom", action="store_true", help="Custom mode with lyrics")
    parser.add_argument("--api-key", help="API key")
    parser.add_argument("--api-base", help="API base URL")

    args = parser.parse_args()

    # Check for API key
    api_key = args.api_key or os.environ.get("SUNO_API_KEY")
    if not api_key:
        print("Error: API key required. Set SUNO_API_KEY or use --api-key")
        print("Get your key at: https://sunoapi.org/api-key")
        return 1

    api_base = args.api_base or os.environ.get("SUNO_API_BASE", "https://api.sunoapi.org")

    client = SunoMusicClient(
        api_base=api_base,
        api_key=api_key
    )

    try:
        if args.custom:
            result = client.generate_custom(
                lyrics=args.prompt,
                title=args.title or "Custom Song",
                tags=args.tags or "electronic",
                instrumental=args.instrumental,
                model=args.model
            )
        else:
            result = client.generate_from_prompt(
                prompt=args.prompt,
                instrumental=args.instrumental,
                model=args.model
            )

        print(f"Generated: {result['filename']}")
        print(f"Path: {result['path']}")
        print(f"Title: {result['song'].get('title', 'N/A')}")
        print(f"Model: {result['song'].get('model', 'N/A')}")
        print(f"Audio URL: {result['song'].get('audio_url', 'N/A')}")

        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
