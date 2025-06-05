"""
Audio module for Smart Lamp.
Handles internet radio streaming and ambient sound playback.
Team member: Leyla (Temperature and Soundscape features)
"""

import pygame
import threading
import time
import os
import json
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from urllib.parse import urlparse
import requests

from .config import settings


@dataclass
class AudioTrack:
    """Represents an audio track or stream."""
    name: str
    url: str
    type: str  # 'radio', 'ambient', 'local'
    description: Optional[str] = None


class AudioController:
    """Audio controller for the Smart Lamp."""
    
    def __init__(self):
        self.is_playing = False
        self.current_track = None
        self.volume = settings.hardware.speaker_volume
        self.radio_stations = self._load_radio_stations()
        self.ambient_sounds = self._load_ambient_sounds()
        self.player_thread = None
        self.stop_playback = False
        
        # Initialize pygame mixer
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.audio_available = True
            print("Audio system initialized")
        except Exception as e:
            print(f"Audio initialization failed: {e}")
            self.audio_available = False
    
    def _load_radio_stations(self) -> List[AudioTrack]:
        """Load internet radio stations from configuration."""
        stations = []
        
        # Add configured radio stations
        for station_data in settings.system.radio_stations:
            stations.append(AudioTrack(
                name=station_data.get('name', 'Unknown Station'),
                url=station_data.get('url', ''),
                type='radio',
                description=station_data.get('description', '')
            ))
        
        # Add some default stations if none configured
        if not stations:
            default_stations = [
                {
                    'name': 'Chillhop Radio',
                    'url': 'http://webradio.angriff.de/chillhop.m3u',
                    'description': 'Relaxing chillhop music'
                },
                {
                    'name': 'Ambient Sleeping Pill',
                    'url': 'http://radio.stereoscenic.com/asp-s',
                    'description': 'Ambient sounds for relaxation'
                },
                {
                    'name': 'SomaFM Drone Zone',
                    'url': 'http://ice1.somafm.com/dronezone-128-mp3',
                    'description': 'Atmospheric ambient space music'
                },
                {
                    'name': 'Nature Sounds Radio',
                    'url': 'http://streaming.radionomy.com/Nature-Sounds',
                    'description': 'Natural ambient sounds'
                }
            ]
            
            for station in default_stations:
                stations.append(AudioTrack(
                    name=station['name'],
                    url=station['url'],
                    type='radio',
                    description=station['description']
                ))
        
        return stations
    
    def _load_ambient_sounds(self) -> List[AudioTrack]:
        """Load ambient sound files from local directory."""
        sounds = []
        ambient_dir = settings.system.ambient_sounds_path
        
        # Create ambient sounds directory if it doesn't exist
        os.makedirs(ambient_dir, exist_ok=True)
        
        # Define ambient sound files to look for
        ambient_files = {
            'rain.mp3': 'Gentle rain sounds',
            'rain_heavy.mp3': 'Heavy rain with thunder',
            'wind.mp3': 'Gentle wind through trees',
            'birds.mp3': 'Morning bird songs',
            'ocean.mp3': 'Ocean waves',
            'forest.mp3': 'Forest ambience',
            'fire.mp3': 'Crackling fireplace',
            'white_noise.mp3': 'White noise for concentration'
        }
        
        for filename, description in ambient_files.items():
            filepath = os.path.join(ambient_dir, filename)
            if os.path.exists(filepath):
                sounds.append(AudioTrack(
                    name=filename.replace('.mp3', '').replace('_', ' ').title(),
                    url=filepath,
                    type='ambient',
                    description=description
                ))
        
        # If no files exist, add some online ambient sounds as fallback
        if not sounds:
            online_ambient = [
                {
                    'name': 'Rain Sounds',
                    'url': 'https://www.soundjay.com/misc/rain-01.mp3',
                    'description': 'Soothing rain sounds'
                },
                {
                    'name': 'Forest Birds',
                    'url': 'https://www.soundjay.com/nature/birds-chirping-01.mp3',
                    'description': 'Peaceful bird chirping'
                }
            ]
            
            for sound in online_ambient:
                sounds.append(AudioTrack(
                    name=sound['name'],
                    url=sound['url'],
                    type='ambient',
                    description=sound['description']
                ))
        
        return sounds
    
    def get_available_tracks(self) -> Dict[str, List[AudioTrack]]:
        """Get all available audio tracks organized by type."""
        return {
            'radio': self.radio_stations,
            'ambient': self.ambient_sounds
        }
    
    def play_track(self, track: AudioTrack) -> bool:
        """Play a specific audio track."""
        if not self.audio_available:
            print("Audio system not available")
            return False
        
        try:
            # Stop current playback
            self.stop()
            
            self.current_track = track
            self.stop_playback = False
            
            print(f"Starting playback: {track.name}")
            
            if track.type == 'radio':
                self.player_thread = threading.Thread(
                    target=self._play_radio_stream,
                    args=(track,),
                    daemon=True
                )
            else:
                self.player_thread = threading.Thread(
                    target=self._play_local_file,
                    args=(track,),
                    daemon=True
                )
            
            self.player_thread.start()
            self.is_playing = True
            return True
            
        except Exception as e:
            print(f"Error starting playback: {e}")
            return False
    
    def _play_radio_stream(self, track: AudioTrack):
        """Play internet radio stream."""
        try:
            # For radio streams, we would typically use a streaming library
            # This is a simplified implementation
            print(f"Streaming radio: {track.name} from {track.url}")
            
            # Since pygame doesn't handle streams well, we'll simulate streaming
            # In a real implementation, you'd use libraries like python-vlc or ffmpeg
            while not self.stop_playback:
                print(f"🎵 Playing radio: {track.name}")
                time.sleep(10)  # Simulate streaming
                
        except Exception as e:
            print(f"Error streaming radio: {e}")
        finally:
            self.is_playing = False
    
    def _play_local_file(self, track: AudioTrack):
        """Play local audio file."""
        try:
            if not os.path.exists(track.url):
                print(f"Audio file not found: {track.url}")
                return
            
            pygame.mixer.music.load(track.url)
            pygame.mixer.music.set_volume(self.volume / 100.0)
            pygame.mixer.music.play(-1)  # Loop indefinitely
            
            print(f"🎵 Playing ambient sound: {track.name}")
            
            # Wait while playing
            while pygame.mixer.music.get_busy() and not self.stop_playback:
                time.sleep(0.1)
                
        except Exception as e:
            print(f"Error playing local file: {e}")
        finally:
            self.is_playing = False
    
    def stop(self):
        """Stop current audio playback."""
        self.stop_playback = True
        
        if pygame.mixer.get_init():
            pygame.mixer.music.stop()
        
        if self.player_thread and self.player_thread.is_alive():
            self.player_thread.join(timeout=2)
        
        self.is_playing = False
        self.current_track = None
        print("Audio playback stopped")
    
    def pause(self):
        """Pause current audio playback."""
        if self.is_playing and pygame.mixer.get_init():
            pygame.mixer.music.pause()
            print("Audio paused")
    
    def resume(self):
        """Resume paused audio playback."""
        if pygame.mixer.get_init():
            pygame.mixer.music.unpause()
            print("Audio resumed")
    
    def set_volume(self, volume: int):
        """Set audio volume (0-100)."""
        self.volume = max(0, min(100, volume))
        if pygame.mixer.get_init():
            pygame.mixer.music.set_volume(self.volume / 100.0)
        print(f"Volume set to {self.volume}%")
    
    def get_volume(self) -> int:
        """Get current audio volume."""
        return self.volume
    
    def is_playing_audio(self) -> bool:
        """Check if audio is currently playing."""
        return self.is_playing
    
    def get_current_track(self) -> Optional[AudioTrack]:
        """Get currently playing track."""
        return self.current_track
    
    def play_radio_by_name(self, name: str) -> bool:
        """Play radio station by name."""
        for station in self.radio_stations:
            if station.name.lower() == name.lower():
                return self.play_track(station)
        print(f"Radio station '{name}' not found")
        return False
    
    def play_ambient_by_name(self, name: str) -> bool:
        """Play ambient sound by name."""
        for sound in self.ambient_sounds:
            if sound.name.lower() == name.lower():
                return self.play_track(sound)
        print(f"Ambient sound '{name}' not found")
        return False
    
    def play_mood_based_audio(self, mood: str):
        """Play audio based on mood or environment."""
        mood_mapping = {
            'relaxing': 'rain',
            'focus': 'white noise',
            'sleep': 'ocean',
            'energetic': 'birds',
            'cozy': 'fire',
            'calm': 'forest'
        }
        
        ambient_name = mood_mapping.get(mood.lower())
        if ambient_name:
            self.play_ambient_by_name(ambient_name)
        else:
            # Default to a random ambient sound
            if self.ambient_sounds:
                self.play_track(self.ambient_sounds[0])
    
    def play_temperature_based_audio(self, temperature_celsius: float):
        """Play audio based on temperature."""
        if temperature_celsius < 10:
            # Very cold - cozy sounds
            self.play_ambient_by_name('fire')
        elif temperature_celsius < 20:
            # Cool - indoor ambience
            self.play_ambient_by_name('rain')
        elif temperature_celsius > 30:
            # Hot - cooling sounds
            self.play_ambient_by_name('ocean')
        else:
            # Moderate - nature sounds
            self.play_ambient_by_name('birds')
    
    def download_default_ambient_sounds(self):
        """Download default ambient sound files if they don't exist."""
        # This would download sample ambient sounds
        # Implementation would depend on where to source the files
        pass
    
    def cleanup(self):
        """Clean up audio resources."""
        self.stop()
        if pygame.mixer.get_init():
            pygame.mixer.quit()
        print("Audio system cleaned up")


class AudioManager:
    """High-level audio manager that integrates with the lamp system."""
    
    def __init__(self, lamp_controller=None):
        self.lamp_controller = lamp_controller
        self.audio_controller = AudioController()
        self.auto_audio_enabled = False
        self.current_environment = None
        
    def enable_environmental_audio(self, enable: bool = True):
        """Enable automatic audio based on environmental conditions."""
        self.auto_audio_enabled = enable
        print(f"Environmental audio {'enabled' if enable else 'disabled'}")
    
    def on_temperature_change(self, temp_celsius: float, temp_fahrenheit: float, humidity: float):
        """Handle temperature changes with appropriate audio."""
        if not self.auto_audio_enabled:
            return
        
        print(f"Temperature changed to {temp_celsius:.1f}°C - adjusting audio")
        self.audio_controller.play_temperature_based_audio(temp_celsius)
    
    def on_earthquake_alert(self, magnitude: float, location: str, event_time):
        """Handle earthquake alerts with calming audio."""
        if not self.auto_audio_enabled:
            return
        
        print("Earthquake detected - playing calming sounds")
        # Play calming sounds during/after earthquake
        self.audio_controller.play_ambient_by_name('ocean')
    
    def on_air_quality_alert(self, aqi: int, status: str):
        """Handle air quality alerts."""
        if not self.auto_audio_enabled:
            return
        
        if aqi > 100:
            print("Poor air quality - playing indoor ambient sounds")
            # Encourage staying indoors with cozy sounds
            self.audio_controller.play_ambient_by_name('rain')
    
    def set_bedtime_mode(self):
        """Set audio for bedtime."""
        print("Setting bedtime audio mode")
        self.audio_controller.play_ambient_by_name('ocean')
        self.audio_controller.set_volume(30)  # Lower volume for sleep
    
    def set_work_mode(self):
        """Set audio for work/focus."""
        print("Setting work audio mode")
        self.audio_controller.play_ambient_by_name('white noise')
        self.audio_controller.set_volume(50)
    
    def set_relaxation_mode(self):
        """Set audio for relaxation."""
        print("Setting relaxation audio mode")
        self.audio_controller.play_ambient_by_name('forest')
        self.audio_controller.set_volume(60)
    
    def get_audio_status(self) -> Dict:
        """Get current audio status."""
        current_track = self.audio_controller.get_current_track()
        return {
            'is_playing': self.audio_controller.is_playing_audio(),
            'current_track': current_track.name if current_track else None,
            'volume': self.audio_controller.get_volume(),
            'auto_enabled': self.auto_audio_enabled,
            'available_tracks': len(self.audio_controller.get_available_tracks()['radio'] + 
                                   self.audio_controller.get_available_tracks()['ambient'])
        }
    
    def cleanup(self):
        """Clean up audio manager."""
        self.audio_controller.cleanup() 