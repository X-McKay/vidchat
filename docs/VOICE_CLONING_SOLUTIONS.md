# Voice Cloning Solutions for VidChat

Modern alternatives to RVC for voice cloning, compatible with Python 3.13 and current PyTorch.

## The Problem with RVC

**RVC (Retrieval-based Voice Conversion)** has compatibility issues:
- Requires Python 3.10 (not 3.13)
- Requires PyTorch <2.6 (for Fairseq compatibility)
- RTX 5090 needs PyTorch 2.6+
- **Result**: Fundamental incompatibility requiring extensive workarounds

## Modern Alternatives (2024/2025)

### 🏆 Recommended: Coqui XTTS v2

**Status**: ✅ Python 3.13 compatible, actively maintained

**Key Features**:
- **Voice cloning with just 6 seconds** of audio
- **17 languages** supported (multilingual)
- **Emotion and style transfer**
- **<150ms streaming latency** on consumer GPUs
- **MIT-like license** (Apache 2.0)
- Pure PyTorch implementation

**Python Support**: 3.10-3.13 ✅
**Installation**:
```bash
pip install coqui-tts
```

**Usage**:
```python
from TTS.api import TTS

tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cuda")
wav = tts.tts(
    text="Hello world!",
    speaker_wav="reference_audio.wav",  # 6+ seconds
    language="en"
)
```

**Pros**:
- ✅ Works with Python 3.13
- ✅ Modern PyTorch (2.0+)
- ✅ Very fast inference (real-time)
- ✅ Minimal training data needed
- ✅ Easy to use API
- ✅ Cross-language voice cloning
- ✅ Active community

**Cons**:
- Model size is larger (~2GB)
- Requires GPU for best performance (works on CPU but slower)

**GitHub**: https://github.com/idiap/coqui-ai-TTS
**Maintained Fork**: Active as of 2024/2025

---

### 🥈 Alternative: GPT-SoVITS

**Status**: ⚠️ Python 3.10-3.12 only (not 3.13 yet)

**Key Features**:
- **1-minute voice data** for training
- **5-second clips** give 80-95% similarity
- **Cross-lingual**: English, Japanese, Korean, Cantonese, Chinese
- **Integrated WebUI** with tools (voice separation, auto-segmentation, ASR)
- **Fast training**: One-minute fine-tuning capability

**Python Support**: 3.10-3.12 ⚠️ (not 3.13)
**Installation**: Manual from GitHub

**Pros**:
- ✅ Very high quality
- ✅ Fast training and inference (3x real-time on RTX 4070)
- ✅ Minimal data requirements
- ✅ Good documentation
- ✅ WebUI included

**Cons**:
- ❌ Not Python 3.13 compatible yet
- More complex setup than XTTS
- Larger download

**GitHub**: https://github.com/RVC-Boss/GPT-SoVITS
**Same Team as RVC**: RVC-Boss organization

---

### 🥉 Other Options

#### OpenVoice v2
- **Status**: Active, MIT license
- **Features**: Tone color replication, emotion/accent/rhythm control
- **Python**: Modern versions supported
- **Use Case**: Fine control over voice characteristics
- **GitHub**: https://github.com/myshell-ai/OpenVoice

#### StyleTTS 2
- **Status**: Active, research-focused
- **Features**: Diffusion-based, zero-shot cloning, natural rhythm
- **Quality**: Matches human ratings in tests
- **Use Case**: Highest quality, research applications

#### Fish Audio
- **Status**: Commercial but has free tier
- **Features**: "Insanely real" voices with emotion, breathing, pauses
- **Quality**: Industry-leading according to reviews
- **Use Case**: When quality > open source requirement

## Comparison Matrix

| Feature | XTTS v2 | GPT-SoVITS | RVC | OpenVoice v2 |
|---------|---------|------------|-----|--------------|
| **Python 3.13** | ✅ | ⚠️ (3.12) | ❌ (3.10) | ✅ |
| **Modern PyTorch** | ✅ | ✅ | ❌ | ✅ |
| **Training Data** | 6 seconds | 1 minute | 10+ minutes | ~1 minute |
| **Setup Difficulty** | Easy | Medium | Hard | Medium |
| **Inference Speed** | Real-time | 3x real-time | Fast | Real-time |
| **Quality** | Very High | Excellent | Excellent | Very High |
| **Languages** | 17 | 5 | Any | Many |
| **License** | Apache 2.0 | MIT | MIT | MIT |
| **Maintenance** | Active | Active | Active | Active |

## Recommendation for VidChat

### 🎯 Best Choice: **Coqui XTTS v2**

**Reasons**:
1. ✅ **Python 3.13 compatible** - No version conflicts
2. ✅ **Easy integration** - Simple pip install, clean API
3. ✅ **Minimal requirements** - Only 6 seconds of audio needed
4. ✅ **Fast** - Real-time inference on GPU
5. ✅ **Proven** - Most downloaded TTS model on Hugging Face
6. ✅ **Multilingual** - 17 languages out of the box
7. ✅ **Active** - Maintained fork with 2024/2025 updates

### Implementation Plan

**Phase 1: Basic Integration** (Easy - 1-2 hours)
```python
# Add to VidChat TTS engine
class XTTSTTS(BaseTTS):
    def __init__(self, reference_audio: str):
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self.reference_audio = reference_audio

    def synthesize(self, text: str, output_path: str) -> str:
        wav = self.tts.tts(
            text=text,
            speaker_wav=self.reference_audio,
            language="en"
        )
        # Save wav to output_path
        return output_path
```

**Phase 2: Voice Training** (Optional)
- Users provide 6+ seconds of audio
- No training needed! XTTS does zero-shot cloning
- Just specify the reference audio path

**Phase 3: Advanced Features**
- Multi-speaker support
- Emotion control
- Language switching

### Migration from RVC

1. **Remove RVC training code** - Document as "historical attempt"
2. **Add XTTS as dependency** - `coqui-tts` in pyproject.toml
3. **Create XTTS TTS engine** - Implement `XTTSTTS` class
4. **Update CLI** - Add `--voice-clone` option to use custom audio
5. **Test** - Verify with sample audio files

### Next Steps

**Immediate** (Recommended):
```bash
# 1. Add dependency
echo 'coqui-tts>=0.27.0' >> requirements.txt

# 2. Test installation
uv pip install coqui-tts

# 3. Quick test
python -c "from TTS.api import TTS; print('XTTS Ready!')"
```

**Short-term**:
- Implement `XTTSTTS` class in `src/vidchat/tts/xtts.py`
- Add voice cloning docs
- Create example scripts

**Long-term**:
- Add voice preview feature
- Multi-language support
- Voice library management

## Cost-Benefit Analysis

### XTTS v2
- **Setup time**: 30 minutes
- **Learning curve**: Low
- **Maintenance**: Minimal
- **Compatibility**: Perfect ✅
- **Quality**: Very High
- **Risk**: Low

### GPT-SoVITS
- **Setup time**: 2-3 hours
- **Learning curve**: Medium
- **Maintenance**: Medium
- **Compatibility**: Need Python 3.12 environment ⚠️
- **Quality**: Excellent
- **Risk**: Medium

### Keep RVC
- **Setup time**: Already done (but broken)
- **Learning curve**: High
- **Maintenance**: High (constant patching)
- **Compatibility**: Poor ❌
- **Quality**: Excellent (when working)
- **Risk**: High

## Conclusion

**Switch to Coqui XTTS v2** - it solves all compatibility issues, provides excellent quality, and is much easier to maintain than RVC. The 6-second cloning capability is actually better than RVC's 10+ minute requirement.

GPT-SoVITS is a good alternative if Python 3.12 is acceptable, but XTTS v2 is the clear winner for VidChat's requirements.

---

**Decision**: Let's implement XTTS v2 🚀

**Would you like me to**:
1. Remove RVC code and implement XTTS v2?
2. Create a comparison demo first?
3. Keep RVC as optional Docker-based feature?
