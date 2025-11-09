from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata, logger

logger.info("Running hook-torchaudio.py")

# Torchaudio has many submodules that need to be discovered.
hiddenimports = collect_submodules('torchaudio')

# It also includes data files, like pre-compiled libraries (.dll, .so),
# that need to be bundled.
datas = collect_data_files('torchaudio', include_py_files=True)

# Package metadata can also be important for some libraries.
datas += copy_metadata('torchaudio')

logger.info(f"Collected {len(hiddenimports)} hidden imports for torchaudio.")
logger.info(f"Collected {len(datas)} data files for torchaudio.")