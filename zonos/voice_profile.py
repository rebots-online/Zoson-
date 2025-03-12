"""
Voice Profile Management System for ZonosTTS.

This module provides functionality for saving, loading, and managing voice profiles,
allowing users to store voice embeddings and associated parameters for later use.
"""

import os
import json
import uuid
import base64
import torch
import torchaudio
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple

from zonos.model import Zonos
from zonos.utils import DEFAULT_DEVICE as device


class VoiceProfileManager:
    """
    Manages voice profiles for ZonosTTS, including saving and loading embeddings,
    organizing profiles, and providing an interface for modifying voice parameters.
    """
    
    def __init__(self, model: Zonos, base_dir: str = None):
        """
        Initialize the VoiceProfileManager.
        
        Args:
            model: The ZonosTTS model instance
            base_dir: Base directory for storing voice profiles. Defaults to 'voices/' in the
                      current working directory if not specified.
        """
        self.model = model
        self.base_dir = base_dir or os.path.join(os.getcwd(), "voices")
        
        # Create directory structure if it doesn't exist
        self.profiles_dir = os.path.join(self.base_dir, "profiles")
        self.samples_dir = os.path.join(self.base_dir, "samples")
        self.kokoro_dir = os.path.join(self.base_dir, "kokoro")
        
        os.makedirs(self.profiles_dir, exist_ok=True)
        os.makedirs(self.samples_dir, exist_ok=True)
        os.makedirs(self.kokoro_dir, exist_ok=True)
        
        # Cache for loaded profiles
        self._profile_cache = {}
        
    def list_profiles(self) -> List[Dict[str, Any]]:
        """
        List all available voice profiles with their metadata.
        
        Returns:
            A list of dictionaries containing profile metadata.
        """
        profiles = []
        
        for filename in os.listdir(self.profiles_dir):
            if filename.endswith(".json"):
                profile_path = os.path.join(self.profiles_dir, filename)
                try:
                    with open(profile_path, "r") as f:
                        profile_data = json.load(f)
                        # Return only metadata, not the full embedding
                        profiles.append({
                            "profile_id": profile_data.get("profile_id"),
                            "name": profile_data.get("name"),
                            "description": profile_data.get("description"),
                            "created_at": profile_data.get("created_at"),
                            "updated_at": profile_data.get("updated_at"),
                            "source": profile_data.get("source", {}).get("type"),
                            "tags": profile_data.get("tags", [])
                        })
                except (json.JSONDecodeError, IOError) as e:
                    print(f"Error reading profile {filename}: {e}")
        
        return sorted(profiles, key=lambda x: x.get("name", ""))
    
    def create_profile_from_audio(
        self, 
        audio_path: str, 
        name: str, 
        description: str = "",
        parameters: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> str:
        """
        Create a new voice profile from a reference audio file.
        
        Args:
            audio_path: Path to the reference audio file
            name: Name for the profile
            description: Optional description
            parameters: Optional voice parameters
            tags: Optional tags for categorization
            
        Returns:
            The profile ID of the newly created profile
        """
        # Generate profile ID
        profile_id = str(uuid.uuid4())
        
        # Create profile directory for samples
        profile_samples_dir = os.path.join(self.samples_dir, profile_id)
        os.makedirs(profile_samples_dir, exist_ok=True)
        
        # Load and process audio
        try:
            wav, sr = torchaudio.load(audio_path)
            wav = wav.to(device)
            
            # Generate speaker embedding
            speaker_embedding = self.model.make_speaker_embedding(wav, sr).to(device)
            
            # Encode tensor to base64 for storage
            encoded_embedding = self._encode_tensor(speaker_embedding)
            
            # Default parameters if not provided
            if parameters is None:
                parameters = {
                    "fmax": 24000,
                    "pitch_std": 45.0,
                    "speaking_rate": 15.0,
                    "dnsmos_ovrl": 4.0,
                    "emotions": [1.0, 0.05, 0.05, 0.05, 0.05, 0.05, 0.1, 0.2],
                    "vqscore": 0.78
                }
            
            # Prepare profile data
            now = datetime.now().isoformat()
            profile_data = {
                "profile_id": profile_id,
                "name": name,
                "description": description or "",
                "created_at": now,
                "updated_at": now,
                "source": {
                    "type": "sample",
                    "path": os.path.abspath(audio_path)
                },
                "speaker_embedding": {
                    "format": "tensor",
                    "data": encoded_embedding
                },
                "parameters": parameters,
                "tags": tags or [],
                "samples": []
            }
            
            # Save profile
            profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
            with open(profile_path, "w") as f:
                json.dump(profile_data, f, indent=2)
            
            return profile_id
            
        except Exception as e:
            raise ValueError(f"Failed to create profile from audio: {e}")
    
    def load_profile(self, profile_id: str) -> Tuple[torch.Tensor, Dict[str, Any]]:
        """
        Load a voice profile by ID and return the speaker embedding and parameters.
        
        Args:
            profile_id: The ID of the profile to load
            
        Returns:
            A tuple containing (speaker_embedding, profile_parameters)
        """
        # Check cache first
        if profile_id in self._profile_cache:
            return self._profile_cache[profile_id]
        
        profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        
        if not os.path.exists(profile_path):
            raise ValueError(f"Profile {profile_id} not found")
        
        try:
            with open(profile_path, "r") as f:
                profile_data = json.load(f)
            
            # Decode embedding
            embedding_data = profile_data.get("speaker_embedding", {}).get("data")
            if not embedding_data:
                raise ValueError(f"No embedding data found in profile {profile_id}")
            
            speaker_embedding = self._decode_tensor(embedding_data)
            parameters = profile_data.get("parameters", {})
            
            # Cache for future use
            self._profile_cache[profile_id] = (speaker_embedding, parameters)
            
            return speaker_embedding, parameters
            
        except Exception as e:
            raise ValueError(f"Failed to load profile {profile_id}: {e}")
    
    def update_profile(
        self, 
        profile_id: str, 
        name: str = None, 
        description: str = None,
        parameters: Dict[str, Any] = None,
        tags: List[str] = None
    ) -> bool:
        """
        Update a voice profile's metadata and/or parameters.
        
        Args:
            profile_id: The ID of the profile to update
            name: New name (optional)
            description: New description (optional)
            parameters: New parameters (optional)
            tags: New tags (optional)
            
        Returns:
            True if successful, False otherwise
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        
        if not os.path.exists(profile_path):
            return False
        
        try:
            # Load existing profile
            with open(profile_path, "r") as f:
                profile_data = json.load(f)
            
            # Update fields
            if name is not None:
                profile_data["name"] = name
            
            if description is not None:
                profile_data["description"] = description
            
            if parameters is not None:
                profile_data["parameters"] = parameters
            
            if tags is not None:
                profile_data["tags"] = tags
            
            # Update timestamp
            profile_data["updated_at"] = datetime.now().isoformat()
            
            # Save updated profile
            with open(profile_path, "w") as f:
                json.dump(profile_data, f, indent=2)
            
            # Clear cache
            if profile_id in self._profile_cache:
                del self._profile_cache[profile_id]
            
            return True
            
        except Exception as e:
            print(f"Failed to update profile {profile_id}: {e}")
            return False
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Delete a voice profile and its associated samples.
        
        Args:
            profile_id: The ID of the profile to delete
            
        Returns:
            True if successful, False otherwise
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        profile_samples_dir = os.path.join(self.samples_dir, profile_id)
        
        if not os.path.exists(profile_path):
            return False
        
        try:
            # Delete profile file
            os.remove(profile_path)
            
            # Delete samples directory if it exists
            if os.path.exists(profile_samples_dir):
                for sample_file in os.listdir(profile_samples_dir):
                    os.remove(os.path.join(profile_samples_dir, sample_file))
                os.rmdir(profile_samples_dir)
            
            # Clear from cache
            if profile_id in self._profile_cache:
                del self._profile_cache[profile_id]
            
            return True
            
        except Exception as e:
            print(f"Failed to delete profile {profile_id}: {e}")
            return False
    
    def add_sample_to_profile(self, profile_id: str, audio_path: str, sample_name: str = None) -> bool:
        """
        Add a sample audio to a profile.
        
        Args:
            profile_id: The ID of the profile
            audio_path: Path to the sample audio file
            sample_name: Optional name for the sample (defaults to filename)
            
        Returns:
            True if successful, False otherwise
        """
        profile_path = os.path.join(self.profiles_dir, f"{profile_id}.json")
        profile_samples_dir = os.path.join(self.samples_dir, profile_id)
        
        if not os.path.exists(profile_path):
            return False
        
        try:
            # Ensure samples directory exists
            os.makedirs(profile_samples_dir, exist_ok=True)
            
            # Generate sample name if not provided
            if sample_name is None:
                sample_name = os.path.basename(audio_path)
            
            # Copy sample to samples directory
            sample_filename = f"{uuid.uuid4()}_{sample_name}"
            sample_path = os.path.join(profile_samples_dir, sample_filename)
            
            # Copy audio file
            import shutil
            shutil.copy2(audio_path, sample_path)
            
            # Update profile with sample
            with open(profile_path, "r") as f:
                profile_data = json.load(f)
            
            profile_data["samples"] = profile_data.get("samples", []) + [sample_path]
            profile_data["updated_at"] = datetime.now().isoformat()
            
            with open(profile_path, "w") as f:
                json.dump(profile_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Failed to add sample to profile {profile_id}: {e}")
            return False
    
    def _encode_tensor(self, tensor: torch.Tensor) -> str:
        """
        Encode a PyTorch tensor to a base64 string for storage.
        """
        buffer = torch.save(tensor, '')
        return base64.b64encode(buffer).decode('utf-8')
    
    def _decode_tensor(self, encoded_str: str) -> torch.Tensor:
        """
        Decode a base64 string back to a PyTorch tensor.
        """
        buffer = base64.b64decode(encoded_str)
        return torch.load(buffer, map_location=device)


# Initialize Kokoro voices
KOKORO_VOICES = {
    "None (Use Voice Cloning)": None,
    "Kokoro - Female 1 (English)": "voices/kokoro/female1_en.wav",
    "Kokoro - Female 2 (English)": "voices/kokoro/female2_en.wav",
    "Kokoro - Male 1 (English)": "voices/kokoro/male1_en.wav",
    "Kokoro - Male 2 (English)": "voices/kokoro/male2_en.wav",
    "Kokoro - Female 1 (Japanese)": "voices/kokoro/female1_jp.wav",
    "Kokoro - Male 1 (Japanese)": "voices/kokoro/male1_jp.wav",
    "Kokoro - Female 1 (Chinese)": "voices/kokoro/female1_zh.wav",
    "Kokoro - Female 1 (French)": "voices/kokoro/female1_fr.wav",
    "Kokoro - Female 1 (German)": "voices/kokoro/female1_de.wav",
}
