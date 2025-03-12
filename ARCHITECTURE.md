# ZonosTTS Architecture

## Overview

ZonosTTS (Zonos-v0.1) is a high-quality text-to-speech synthesis system trained on more than 200,000 hours of multilingual speech data. The architecture follows a modernized approach to TTS that focuses on expressiveness, quality, and versatility.

## System Architecture

### High-Level Architecture

The system follows a two-stage architecture:
1. **Text Processing Stage**: Normalizes and phonemizes text via eSpeak
2. **Audio Generation Stage**: Predicts discrete audio codes through a transformer or hybrid backbone

<div align="center">
<img src="assets/ArchitectureDiagram.png" 
     alt="Architecture Diagram" 
     style="width: 1000px;
            height: auto;
            object-position: center top;">
</div>

### Core Components

#### Text Processing
- **Text Normalization**: Converts raw text input into a standardized format
- **Phonemization**: Uses eSpeak to convert text to phonetic representation
- **Tokenization**: Processes phonetic data into tokens for the model

#### Conditioning System
The model accepts various conditioning inputs that control different aspects of the generated speech:

| Conditioning Type | Description | Models |
|-------------------|-------------|--------|
| espeak | Text pre-processing pipeline | Transformer & Hybrid |
| speaker | Speaker voice characteristics | Transformer & Hybrid |
| emotion | 8D vector for emotional control | Transformer & Hybrid |
| fmax | Maximum frequency specification | Transformer & Hybrid |
| pitch_std | Pitch variation control | Transformer & Hybrid |
| speaking_rate | Phonemes per second rate | Transformer & Hybrid |
| language_id | Language identifier | Transformer & Hybrid |
| vqscore_8 | Speech quality estimation | Hybrid only |
| ctc_loss | Text-audio alignment quality | Hybrid only |
| dnsmos_ovrl | Mean Opinion Score | Hybrid only |
| speaker_noised | Speaker embedding denoising flag | Hybrid only |

#### Model Variants
1. **Transformer-based Model**
   - Pure transformer architecture
   - Lighter computational requirements
   - Core conditioning support

2. **Hybrid Model**
   - Enhanced architecture
   - Requires 3000-series or newer NVIDIA GPU
   - Additional conditioning options
   - Potentially higher quality output

#### Audio Pipeline
- **DAC Token Prediction**: Predicts discrete audio codes
- **Neural Codec**: Decodes discrete tokens back into continuous audio waveforms
- **Output**: 44kHz high-quality audio

## Code Structure

```
zonos/
├── autoencoder.py          # Neural codec implementation
├── backbone/               # Model architecture implementations
├── codebook_pattern.py     # Discrete token patterns
├── conditioning.py         # Conditioning system implementation
├── config.py               # Configuration parameters
├── model.py                # Main model implementation
├── sampling.py             # Generation and sampling utilities
├── speaker_cloning.py      # Speaker embedding extraction
└── utils.py                # Utility functions
```

## Integration Points

- **Python API**: Direct integration via Python code
- **Gradio Interface**: User-friendly web interface for interactive use
- **Docker**: Containerized deployment

## Technical Details

- **Input**: Text and optional reference audio
- **Output**: 44kHz audio waveform
- **Performance**: ~2x real-time factor on RTX 4090
- **Memory Requirements**: Minimum 6GB VRAM (GPU) or equivalent RAM (CPU)
- **Dependencies**: eSpeak-ng, PyTorch, torchaudio

## MicroSaaS Extension Architecture

The ZonosTTS framework can be extended into a complete voice cloning and redubbing microSaaS platform through the addition of several key components.

### Extended System Architecture

```
┌─ Phase 1: MVP ─────────────────────────────────────────────────────┐
│                                                                     │
│  • Whisper.wasm for transcription                                   │
│  • Basic speaker segmentation (non-overlapping)                     │
│  • ZonosTTS for voice cloning and synthesis                         │
│  • Simple audio export                                              │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─ Phase 2: Enhanced ───────────────────────────────────────────────┐
│                                                                     │
│  • Add server-side Pyannote for better diarization                  │
│  • Implement basic overlap handling                                 │
│  • Add translation capabilities                                     │
│  • Improve synchronization                                          │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─ Phase 3: Advanced ───────────────────────────────────────────────┐
│                                                                     │
│  • Full speaker overlap detection and handling                      │
│  • Emotion transfer from original to synthesized speech             │
│  • Advanced audio editing capabilities                              │
│  • API access for third-party integration                           │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### CPU-Focused Architecture

For voiceover workflows without avatar rendering, a CPU-only pipeline offers cost-effective processing:

```
┌─ Client (CPU-Only) ─────────────────────────────────────────────────────┐
│                                                                          │
│  ┌──────────────┐   ┌───────────────┐   ┌────────────────┐              │
│  │ Audio/Video  │──▶│ Whisper.wasm  │──▶│ Transcript     │              │
│  │ Input        │   │ Transcription │   │ Processing     │              │
│  └──────────────┘   └───────────────┘   └────────────────┘              │
│                                                 │                        │
│  ┌──────────────┐   ┌───────────────┐   ┌──────▼─────────┐              │
│  │ Final Audio  │◀──│ ZonosTTS      │◀──│ Voice Profile  │              │
│  │ Output       │   │ (CPU version) │   │ Management     │              │
│  └──────────────┘   └───────────────┘   └────────────────┘              │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

### Modular Pipeline Components

1. **Transcription Module**
   - Whisper.wasm for browser-based speech recognition
   - Timestamp generation for synchronization
   - Language detection and handling
   
2. **Diarization Module**
   - Speaker identification and segmentation
   - Voice profile extraction
   - Sequential processing after transcription
   
3. **Voice Synthesis Module**
   - ZonosTTS for voice cloning
   - Emotion and cadence matching
   - Language-specific synthesis optimization
   
4. **Synchronization Module**
   - Alignment of synthesized speech with original timing
   - Handling of pauses and natural speech patterns
   - Optional integration with video content

### Technical Integration Strategy

- **Browser-First Approach**: Maximize client-side processing for scalability
- **Modular Components**: Allow selective server offloading when necessary
- **Progressive Enhancement**: Provide basic functionality with graceful enhancement
- **Asynchronous Processing**: Enable background processing for longer content

## Future Architecture Considerations

- Potential optimization for CPU-only environments
- Further model size reduction techniques
- Enhanced multilingual support
- Real-time streaming capability
- Integration with translation services
- Support for emotion transfer and preservation

---

(C)2025 Robin L. M. Cheung, MBA
