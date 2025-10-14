# External Dependencies

This directory contains external dependencies that are cloned during setup.

## SadTalker

For realistic AI-driven talking head animations.

**Setup:**
```bash
cd external
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt
bash scripts/download_models.sh
```

## RVC (Retrieval-based Voice Conversion)

For voice cloning and conversion (optional).

**Setup:**
```bash
cd external
git clone https://github.com/RVC-Project/Retrieval-based-Voice-Conversion-WebUI.git RVC
cd RVC
pip install -r requirements.txt
```

## Notes

- These dependencies are optional and not required for basic VidChat functionality
- They are cloned during setup if you opt-in
- Models are downloaded to each dependency's own directory
- All paths are relative to the project root to ensure OS compatibility
