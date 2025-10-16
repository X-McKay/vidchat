# Phase 2 Cleanup Plan - Code Quality Improvements

**Date**: 2025-10-16
**Status**: Ready to Start
**Estimated Duration**: 2-3 weeks
**Focus**: Code quality, modularity, and maintainability

---

## Overview

Phase 2 focuses on medium-effort improvements that were deferred from Phase 1:
- Consolidating duplicate functionality
- Improving code organization
- Adding type safety
- Enhancing modularity

**Goals:**
1. Eliminate duplicate code paths
2. Create single source of truth for configs
3. Improve code modularity (split large files)
4. Add type hints for better IDE support and error catching

---

## Task Breakdown

### Task 2.1: Split Training Script into Modules (Priority 1)

**Current State:**
- `rvc_train_with_tracking.py` is 580 lines
- Multiple responsibilities: cache, preprocessing, training, tracking
- Hard to test individual components

**Target State:**
```
src/vidchat/training/
├── rvc_train.py (main orchestration, ~150 lines)
├── cache.py (cache management, ~100 lines)
├── preprocessing.py (RVC preprocessing, ~200 lines)
└── mlflow_tracker.py (already modular ✓)
```

**Implementation Steps:**

1. **Create `cache.py` module**
   ```python
   class PreprocessingCache:
       def __init__(self, exp_dir: Path)
       def compute_key(self, files: list, params: dict) -> str
       def is_valid(self) -> bool
       def save_metadata(self, key: str, params: dict)
       def load_metadata(self) -> dict
   ```

2. **Create `preprocessing.py` module**
   ```python
   class RVCPreprocessor:
       def __init__(self, exp_dir: Path, config: dict)
       def preprocess_audio(self)
       def extract_pitch(self, gpu: bool = False)
       def extract_features(self, gpu: bool = False)
       def create_filelist(self)
       def create_config(self)
       def run_all(self, gpu: bool = False)
   ```

3. **Refactor `rvc_train.py` to use modules**
   - Import and use `PreprocessingCache`
   - Import and use `RVCPreprocessor`
   - Keep only orchestration logic
   - Maintain backward compatibility

**Estimated Time**: 1-2 days
**Risk**: Medium (need thorough testing)
**Benefits**: Better testability, code reuse, clearer structure

---

### Task 2.2: Consolidate Voice Data Preparation (Priority 2)

**Current State:**
- `voice_prep/prepare_voice_data.py` (370 lines) - Simple CLI script
- `data/pipeline.py` (267 lines) - Complex pipeline with Whisper
- Both referenced in documentation
- Duplicate YouTube download and audio processing logic

**Analysis:**
```bash
voice_prep/:
  ✓ Simple, focused on YouTube → audio
  ✓ Actually used in training workflow
  ✓ Referenced in docs/RVC_TRAINING.md

data/:
  ✓ More features (Whisper transcription)
  ✓ Better structure (separate modules)
  ⚠ Not actively used in training
  ⚠ More complex than needed for current use case
```

**Decision: Keep `voice_prep/` as primary, enhance it with `data/` features**

**Implementation Steps:**

1. **Analyze dependencies**
   ```bash
   # Check what uses voice_prep
   grep -r "prepare_voice_data" src/ docs/

   # Check what uses data pipeline
   grep -r "VoiceDataPipeline" src/ docs/
   ```

2. **Extract useful features from `data/` package**
   - Better audio segmentation from `preprocessor.py`
   - Whisper transcription as optional feature
   - Configuration validation

3. **Enhance `voice_prep/prepare_voice_data.py`**
   - Add optional transcription flag: `--transcribe`
   - Integrate better audio segmentation
   - Keep simple CLI interface
   - Add proper error handling

4. **Deprecate `data/` package**
   - Add deprecation warnings
   - Update documentation to use `voice_prep/`
   - Create migration guide
   - Keep code for 1 release cycle, then remove

**Estimated Time**: 2-3 days
**Risk**: Medium (need to update documentation)
**Benefits**: Single code path, less confusion, easier maintenance

---

### Task 2.3: Merge Config Systems (Priority 3)

**Current State:**
- `config/settings.py` (131 lines) - Pydantic models
- `data/config.py` (131 lines) - Data prep config
- `utils/config_loader.py` (198 lines) - YAML loading

**Target State:**
```python
# Single config system using Pydantic
src/vidchat/config/
├── __init__.py (re-exports)
├── models.py (Pydantic config models)
├── loader.py (YAML loading logic)
└── defaults.py (default values)
```

**Implementation Steps:**

1. **Merge config models into single file**
   ```python
   # config/models.py
   from pydantic import BaseModel, Field

   class DataPrepConfig(BaseModel):
       """Voice data preparation configuration."""
       voice_name: str
       urls: list[str] = []
       duration: int = 600
       ...

   class RVCTrainingConfig(BaseModel):
       """RVC training configuration."""
       epochs: int = 500
       batch_size: int = 4
       gpu: bool = True
       ...

   class AppConfig(BaseModel):
       """Main application configuration."""
       data_prep: DataPrepConfig = Field(default_factory=DataPrepConfig)
       rvc_training: RVCTrainingConfig = Field(default_factory=RVCTrainingConfig)
       ...
   ```

2. **Update config loader to use Pydantic**
   ```python
   # config/loader.py
   def load_config(path: str = "config.yaml") -> AppConfig:
       """Load config from YAML and validate with Pydantic."""
       with open(path) as f:
           data = yaml.safe_load(f)
       return AppConfig(**data)
   ```

3. **Update all imports**
   ```python
   # Old
   from vidchat.config import default_config
   from vidchat.data.config import DataPrepConfig

   # New
   from vidchat.config import load_config
   config = load_config()
   ```

4. **Add migration guide**
   - Document old vs new config structure
   - Provide example configs
   - Update all documentation

**Estimated Time**: 1-2 days
**Risk**: High (touches many files)
**Benefits**: Type safety, single config schema, better validation

---

### Task 2.4: Add Comprehensive Type Hints (Priority 4)

**Current State:**
- Inconsistent type hints across codebase
- No mypy checking
- Some functions completely untyped

**Target State:**
- All functions have type hints
- Mypy configured and passing
- Type hints in CI/CD

**Implementation Steps:**

1. **Install and configure mypy**
   ```bash
   uv add --dev mypy types-PyYAML types-requests

   # Create mypy.ini
   [mypy]
   python_version = 3.13
   warn_return_any = True
   warn_unused_configs = True
   disallow_untyped_defs = True
   ```

2. **Add type hints incrementally by module**
   - Start with `utils/` (small, simple)
   - Then `config/` (after merge)
   - Then `training/` (after split)
   - Finally `core/`, `tts/`, `data/`

3. **Run mypy and fix errors**
   ```bash
   uv run mypy src/vidchat
   ```

4. **Add to CI/CD**
   ```yaml
   # .github/workflows/type-check.yml
   - name: Type check with mypy
     run: uv run mypy src/vidchat
   ```

**Estimated Time**: 3-4 days
**Risk**: Low (non-breaking)
**Benefits**: Better IDE support, catch bugs early, improved documentation

---

## Implementation Order

**Week 1:**
- Days 1-2: Task 2.1 - Split training script ✓
- Days 3-4: Task 2.4 (partial) - Add type hints to training modules

**Week 2:**
- Days 1-3: Task 2.2 - Consolidate voice data preparation
- Days 4-5: Task 2.3 - Merge config systems

**Week 3:**
- Days 1-3: Task 2.4 (complete) - Add type hints to remaining modules
- Days 4-5: Testing, documentation, cleanup

---

## Testing Strategy

### For Each Task

1. **Unit Tests**
   - Test new modules independently
   - Mock dependencies
   - Cover edge cases

2. **Integration Tests**
   - Test modules working together
   - Verify backward compatibility
   - Test error handling

3. **Regression Tests**
   - Run existing end-to-end tests
   - Verify training still works
   - Check CLI commands

4. **Manual Testing**
   - Run training workflow
   - Test voice data preparation
   - Verify config loading

---

## Risk Mitigation

### High-Risk Changes

**Config System Merge:**
- Create feature branch: `feature/unified-config`
- Test thoroughly before merging
- Keep old config system for 1 release
- Add deprecation warnings
- Document migration path

**Voice Prep Consolidation:**
- Create feature branch: `feature/unified-voice-prep`
- Deprecate old code gradually
- Provide migration guide
- Keep both for 1 release cycle

### Medium-Risk Changes

**Training Script Split:**
- Test each module independently first
- Maintain backward compatibility
- Keep old script as fallback temporarily

**Type Hints:**
- Add incrementally (non-breaking)
- Fix mypy errors module by module
- Don't enforce strict mode initially

---

## Success Criteria

**Code Quality:**
- [ ] Training script < 200 lines
- [ ] No duplicate voice prep logic
- [ ] Single config system
- [ ] 80%+ type hint coverage

**Functionality:**
- [ ] All existing features work
- [ ] Training completes successfully
- [ ] Voice prep produces valid data
- [ ] Config loading works

**Testing:**
- [ ] All tests pass
- [ ] Mypy passes
- [ ] No regressions detected
- [ ] Manual testing complete

**Documentation:**
- [ ] Updated for all changes
- [ ] Migration guides created
- [ ] Examples updated
- [ ] Architecture doc reflects reality

---

## Rollback Plan

If issues arise:

1. **Revert problematic commit**
   ```bash
   git revert <commit-hash>
   ```

2. **Use feature branches**
   - Develop on branches
   - Merge only when stable
   - Can abandon branch if needed

3. **Keep old code temporarily**
   - Deprecate but don't delete immediately
   - Allow 1 release cycle for migration
   - Document deprecation timeline

---

## Documentation Updates

### Files to Update

- [ ] `README.md` - Update quick start if needed
- [ ] `docs/ARCHITECTURE.md` - Reflect new structure
- [ ] `docs/RVC_TRAINING.md` - Update if training script changes
- [ ] `docs/VOICE_DATA_PREP_GUIDE.md` - Update for consolidated voice prep
- [ ] `plans/CLEANUP.md` - Mark Phase 2 complete

### New Documentation

- [ ] `docs/MIGRATION_GUIDE.md` - How to migrate to new config
- [ ] `docs/TYPE_HINTS.md` - Type hints guidelines for contributors
- [ ] `plans/PHASE2_COMPLETION_SUMMARY.md` - Final summary

---

## Next Steps

1. **Review this plan** with team/stakeholders
2. **Create feature branches** for each major task
3. **Start with Task 2.1** (split training script)
4. **Test thoroughly** after each task
5. **Update documentation** as you go
6. **Review and merge** each task individually

---

## Notes

- **Don't rush**: Each task should be done thoroughly
- **Test extensively**: Regressions are costly
- **Document as you go**: Don't leave docs for the end
- **Ask for feedback**: Code reviews catch issues early
- **Stay focused**: One task at a time

---

**Created By**: Claude Code
**Date**: 2025-10-16
**Status**: Ready to Start
**Next Task**: 2.1 - Split Training Script
