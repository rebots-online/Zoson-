# Browser-Compatible Speaker Diarization Analysis

This document analyzes current approaches for implementing speaker diarization in browser environments, presenting options for the ZonosTTS microSaaS platform.

## Overview of Speaker Diarization

Speaker diarization answers the question "who spoke when?" by segmenting audio and attributing each segment to a specific speaker. Traditional diarization pipelines involve:

1. Voice Activity Detection (VAD)
2. Speaker Change Detection
3. Speech Segmentation
4. Speaker Embedding Extraction
5. Clustering
6. (Optional) Overlap Detection

## Browser Implementation Challenges

Implementing diarization in browsers faces several challenges:

| Challenge | Description | Potential Solutions |
|-----------|-------------|---------------------|
| Computation Limits | Browsers have restricted access to system resources | Use WebAssembly, Quantized Models, Chunked Processing |
| Memory Constraints | Limited memory for large model inference | Model Pruning, Progressive Loading, Streaming Processing |
| Model Availability | Few diarization models optimized for browsers | Convert existing models to ONNX/TFLite, Simplified Algorithms |
| API Restrictions | Limited access to audio processing capabilities | Use WebAudio API, AudioWorklet, SharedArrayBuffer |

## Current State of Browser-Compatible Diarization

### Existing Implementations

1. **TensorFlow.js Speaker Recognition**
   - Simple speaker identification (not full diarization)
   - Uses MFCC features and lightweight models
   - Limited to identifying speakers, not handling "when"

2. **Whisper.wasm + Basic Clustering**
   - Leverages Whisper's speaker-awareness capabilities
   - Implements simple clustering on client-side
   - Limited accuracy for overlapping speech

3. **BrowserSpeechToText Projects**
   - Focused on transcription with basic speaker identification
   - Doesn't provide detailed timing information
   - Often struggles with more than 2-3 speakers

### Web Technologies Enabling Diarization

- **WebAssembly**: Near-native performance for computation-heavy algorithms
- **WebAudio API**: Access to raw audio data and processing capabilities
- **WebWorkers**: Background processing to prevent UI blocking
- **AudioWorklet**: Real-time audio processing with low latency
- **SharedArrayBuffer**: Efficient memory sharing between threads
- **WebGPU**: (Emerging) Potential for GPU-accelerated model inference

## Approach Options for ZonosTTS MicroSaaS

### Option 1: Lightweight Client-Side Diarization

```
┌─ Browser ─────────────────────────────────────────────────────────┐
│                                                                    │
│  ┌───────────┐    ┌────────────┐    ┌───────────┐    ┌──────────┐ │
│  │ Audio     │───▶│ VAD (WASM) │───▶│ Feature   │───▶│ Simple   │ │
│  │ Input     │    │            │    │ Extraction│    │ Clustering│ │
│  └───────────┘    └────────────┘    └───────────┘    └──────────┘ │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Works entirely in-browser
- No server costs or latency
- Compatible with privacy-focused use cases

**Cons:**
- Limited accuracy (70-80%)
- Struggles with >3 speakers
- Poor handling of overlapping speech
- Higher client resource usage

### Option 2: Hybrid Processing

```
┌─ Browser ───────────────────────┐   ┌─ Server ────────────────────┐
│                                  │   │                             │
│  ┌───────────┐    ┌────────────┐ │   │ ┌────────────┐  ┌────────┐ │
│  │ Audio     │───▶│ Initial    │─┼───┼▶│ Pyannote/  │─▶│Refined │ │
│  │ Input     │    │ Processing │ │   │ │ NeMo       │  │Results │ │
│  └───────────┘    └────────────┘ │   │ └────────────┘  └────────┘ │
│                         ▲        │   │        │                    │
│  ┌───────────┐    ┌─────┴──────┐ │   │ ┌──────▼─────┐             │
│  │ Final     │◀───│ Result     │◀┼───┼─│ Server     │             │
│  │ Output    │    │ Integration│ │   │ │ Response   │             │
│  └───────────┘    └────────────┘ │   │ └────────────┘             │
│                                  │   │                             │
└──────────────────────────────────┘   └─────────────────────────────┘
```

**Pros:**
- Higher accuracy (85-95%)
- Handles more speakers and overlapping speech
- Lower client resource requirements
- Uses state-of-the-art models

**Cons:**
- Server costs and maintenance
- Potential privacy concerns
- Latency for server processing
- Requires internet connectivity

### Option 3: Progressive Enhancement

```
┌─ Browser ────────────────────────────────────────────────────────┐
│                                                                   │
│  ┌───────────┐    ┌────────────┐    ┌───────────────────────┐    │
│  │ Audio     │───▶│ Basic WASM │───▶│ Initial Results       │    │
│  │ Input     │    │ Diarization│    │                       │    │
│  └───────────┘    └────────────┘    └───────────┬───────────┘    │
│                         │                        │                │
│                         │                        │                │
│                         ▼                        ▼                │
│  ┌───────────┐    ┌────────────┐    ┌───────────────────────┐    │
│  │ Final     │◀───│ Result     │◀───│ Optional Server       │    │
│  │ Output    │    │ Integration│    │ Enhancement           │    │
│  └───────────┘    └────────────┘    └───────────────────────┘    │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

**Pros:**
- Works immediately with basic results
- Can be enhanced with server processing when available
- Balances client-server resource usage
- Flexible deployment options

**Cons:**
- More complex implementation
- Potentially inconsistent user experience
- Requires maintaining two processing paths
- More complex testing and validation

## Technical Implementation Approaches

### 1. Voice Activity Detection (VAD)

WebAssembly-compatible VAD options:
- Silero VAD (ONNX/TFLite compatible)
- TensorFlow.js VAD models
- Simple energy-based detection using WebAudio API

Example implementation with WebAudio API:
```javascript
const audioContext = new AudioContext();
const analyser = audioContext.createAnalyser();
analyser.fftSize = 2048;

// Connect to audio source
source.connect(analyser);

// Process frames
function detectSpeech(dataArray) {
  const average = dataArray.reduce((a, b) => a + b) / dataArray.length;
  return average > THRESHOLD;
}
```

### 2. Speaker Embedding Models

Options for browser-compatible speaker embeddings:
- TensorFlow.js port of VGGVox
- SpeechBrain models converted to ONNX
- Simplified x-vector or d-vector architectures

Implementation approach:
1. Convert embeddings model to ONNX or TFLite format
2. Load and run using ONNX.js or TF.js
3. Extract embeddings for detected speech segments

```javascript
// Example with ONNX.js
async function extractEmbeddings(audioData) {
  const session = await ort.InferenceSession.create('speaker_model.onnx');
  const dims = [1, audioData.length];
  const tensor = new ort.Tensor('float32', audioData, dims);
  const results = await session.run({ input: tensor });
  return results.embedding;
}
```

### 3. Clustering Approaches

Lightweight clustering algorithms suitable for browsers:
- k-means with pre-determined k
- Agglomerative Hierarchical Clustering
- DBSCAN for unknown speaker count

Example implementation of simplified clustering:
```javascript
function simpleClustering(embeddings, threshold = 0.7) {
  const clusters = [];
  
  for (const embedding of embeddings) {
    let assigned = false;
    
    for (let i = 0; i < clusters.length; i++) {
      const similarity = cosineSimilarity(embedding, clusters[i].centroid);
      if (similarity > threshold) {
        // Add to existing cluster
        clusters[i].embeddings.push(embedding);
        clusters[i].centroid = updateCentroid(clusters[i].embeddings);
        assigned = true;
        break;
      }
    }
    
    if (!assigned) {
      // Create new cluster
      clusters.push({
        embeddings: [embedding],
        centroid: embedding
      });
    }
  }
  
  return clusters;
}
```

## Recommended Implementation Strategy

For the ZonosTTS microSaaS platform, we recommend a **progressive enhancement approach** with these components:

1. **Initial Browser Processing**:
   - Implement basic VAD using Silero VAD in WASM
   - Extract simple audio features (MFCCs) using WebAudio API
   - Perform preliminary segmentation and clustering
   - Present initial results immediately to user

2. **Optional Server Enhancement**:
   - Send audio to server for processing with Pyannote or similar
   - Replace browser results with server results when available
   - Provide clear indication of "enhanced results available"

3. **Hybrid Processing Pipeline**:
   - Sequential processing (VAD → Segmentation → Embeddings → Clustering)
   - Parallel implementation (browser and optional server)
   - Result integration with confidence scoring

4. **Performance Optimization**:
   - Process audio in chunks (10-30 seconds)
   - Progressive loading of models
   - Caching of intermediate results
   - Background processing using WebWorkers

## Comparative Analysis of Browser-Compatible Implementations

| Approach | Accuracy | Resource Usage | Privacy | Implementation Difficulty |
|----------|----------|----------------|---------|---------------------------|
| Whisper.wasm + Basic Clustering | 70-80% | Medium | High | Medium |
| TF.js Custom Models | 75-85% | High | High | High |
| ONNX Speaker Models | 80-90% | Medium-High | High | Medium-High |
| Hybrid (Browser+Server) | 90-95% | Low (Browser), High (Server) | Medium | Medium |
| Full Server Offload | 95%+ | Low | Low | Low |

## Conclusion

Browser-compatible speaker diarization is feasible with current web technologies, though with trade-offs in accuracy and resource usage compared to server implementations. For the ZonosTTS microSaaS, a progressive enhancement approach offers the best balance of immediate results and optional accuracy improvements.

The recommended implementation strategy allows for deployment flexibility, where the platform can operate in browser-only mode for privacy-sensitive applications or leverage server-side processing for professional use cases requiring higher accuracy.

---

(C)2025 Robin L. M. Cheung, MBA
