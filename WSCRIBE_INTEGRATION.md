# ZonosTTS + wscribe-editor Integration

This document outlines the detailed implementation strategy for integrating wscribe-editor with ZonosTTS to enable phoneme-level editing and re-synthesis of TTS-generated audio.

## Integration Goals

1. Create a seamless workflow from TTS generation to speech editing
2. Enable phoneme-level editing with precise timing control
3. Allow re-synthesis of only modified speech segments
4. Preserve natural prosody across edits
5. Support multiple audio/subtitle formats
6. Connect with the Voice Profile Management System

## Technical Implementation Plan

### 1. Phoneme Extraction and Timestamping

#### Required Modifications to ZonosTTS

```python
# Pseudocode for phoneme extraction and timestamping
def generate_phoneme_timestamped_audio(text, speaker_embedding, parameters):
    # Extract phonemes from text using eSpeak
    phonemes = extract_phonemes(text)
    
    # Track phoneme positions during generation
    codes, phoneme_timestamps = model.generate_with_timestamps(
        text=text,
        phonemes=phonemes,
        speaker=speaker_embedding,
        parameters=parameters
    )
    
    # Generate audio from codes
    audio = autoencoder.decode(codes)
    
    # Return both audio and phoneme-level timestamp mapping
    return {
        "audio": audio,
        "phoneme_timestamps": phoneme_timestamps,
        "phonemes": phonemes,
        "text": text
    }
```

#### Phoneme Timestamp Format

```json
{
  "text": "Hello, world!",
  "duration": 1.75,
  "phonemes": [
    {
      "phoneme": "h",
      "start": 0.0,
      "end": 0.12,
      "text_position": [0, 1],
      "confidence": 0.98
    },
    {
      "phoneme": "ə",
      "start": 0.12,
      "end": 0.18,
      "text_position": [1, 2],
      "confidence": 0.97
    },
    // ... more phonemes
  ],
  "words": [
    {
      "word": "Hello",
      "start": 0.0,
      "end": 0.45,
      "text_position": [0, 5],
      "phonemes": [0, 1, 2, 3, 4]
    },
    // ... more words
  ],
  "segments": [
    {
      "text": "Hello,",
      "start": 0.0,
      "end": 0.65,
      "words": [0, 1]
    },
    // ... more segments
  ]
}
```

### 2. Formats Export Module

The system will export metadata in multiple formats:

#### SRT (SubRip Text)

```
1
00:00:00,000 --> 00:00:00,650
Hello,

2
00:00:00,650 --> 00:00:01,750
world!
```

#### WebVTT

```
WEBVTT

00:00:00.000 --> 00:00:00.650
Hello,

00:00:00.650 --> 00:00:01.750
world!
```

#### Extended JSON (with Phoneme Data)

This format will extend the standard wscribe JSON format to include phoneme-level data and voice profile information.

### 3. Editor Launch Integration

```python
def launch_editor(audio_data, metadata, format="json"):
    # Save audio to temporary file
    audio_path = save_temp_audio(audio_data)
    
    # Save metadata to temporary file
    metadata_path = save_temp_metadata(metadata, format)
    
    # Launch wscribe-editor with the files
    editor_url = f"http://localhost:8080/wscribe-editor/?audio={audio_path}&data={metadata_path}"
    
    # Open in browser
    open_browser(editor_url)
    
    return editor_url
```

### 4. Editor Modifications

The wscribe-editor will need these adaptations:

1. **Phoneme visualization**: Display phonemes with timing information
2. **Edit boundaries**: Identify natural segment boundaries for re-synthesis
3. **Voice profile selector**: Allow changing voice profiles per segment
4. **Parameter controls**: Adjust TTS parameters for specific segments
5. **Re-synthesis triggers**: Enable regeneration of modified segments

### 5. Re-synthesis API

```python
def resynthesize_segment(segment_text, context_before, context_after, voice_profile, parameters):
    """
    Regenerate a specific segment of audio while maintaining context.
    
    Args:
        segment_text: The text to regenerate
        context_before: Text/phonemes before the segment (for context)
        context_after: Text/phonemes after the segment (for context)
        voice_profile: Voice profile to use
        parameters: TTS parameters
        
    Returns:
        New audio segment and updated timing information
    """
    # Use context for prosody matching
    full_text = context_before + segment_text + context_after
    
    # Generate with timestamps
    result = generate_phoneme_timestamped_audio(full_text, voice_profile, parameters)
    
    # Extract just the relevant segment
    segment_phonemes = extract_segment_phonemes(result, len(context_before), len(segment_text))
    segment_audio = extract_segment_audio(result, segment_phonemes)
    
    return segment_audio, segment_phonemes
```

### 6. Audio Stitching

```python
def stitch_audio_segments(segments):
    """
    Combine multiple audio segments into a continuous stream.
    
    Args:
        segments: List of audio segments with timing information
        
    Returns:
        Combined audio and updated timing
    """
    # Implement crossfade between segments for seamless transitions
    output = crossfade_segments(segments)
    
    # Recalculate timing for all phonemes based on new positions
    timing = recalculate_timing(segments)
    
    return output, timing
```

## Integration Workflow

1. **Generation**: User generates TTS audio with ZonosTTS
2. **Export**: System creates audio file with metadata (JSON/SRT/VTT)
3. **Editing**: wscribe-editor loads for editing with phoneme visualization
4. **Modification**: User edits text or adjusts parameters
5. **Re-synthesis**: Modified segments are regenerated
6. **Preview**: User can preview changes before finalizing
7. **Export**: Final audio and updated metadata are exported

## Required Components

1. **Phoneme Extraction Module**: Enhanced eSpeak integration
2. **Timestamp Tracking**: Modified TTS generation pipeline
3. **Format Converter**: Metadata export in multiple formats
4. **Editor Integration**: Modified wscribe-editor 
5. **Re-synthesis API**: Segment-based audio regeneration
6. **Audio Processor**: Tools for stitching and processing audio segments

## Development Roadmap

### Phase 1: Core Implementation
1. Fork wscribe-editor repository
2. Implement phoneme extraction and timestamping in ZonosTTS
3. Create basic metadata export functionality
4. Build simple editor launch mechanism

### Phase 2: Basic Editing Features
1. Implement phoneme visualization in editor
2. Create segment identification logic
3. Build basic re-synthesis API
4. Implement audio segment stitching

### Phase 3: Advanced Integration
1. Connect with Voice Profile Management System
2. Implement multi-speaker support
3. Add parameter adjustment interface
4. Create comprehensive export options

## Future Considerations

- **Real-time Editing**: Immediate feedback during editing
- **Batch Processing**: Apply edits to multiple files
- **Emotion Transfer**: Preserve emotional qualities across edits
- **Translation Integration**: Edit in one language, output in another
- **Video Synchronization**: Maintain lip-sync with video content

(C)2025 Robin L. M. Cheung, MBA
