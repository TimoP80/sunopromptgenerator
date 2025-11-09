from PyInstaller.utils.hooks import collect_data_files, collect_submodules, copy_metadata, logger

logger.info("hook-torchaudio.py: Running for torchaudio")

# Torchaudio has many submodules that need to be discovered.
logger.info("hook-torchaudio.py: Collecting hidden imports...")
hiddenimports = collect_submodules('torchaudio')
logger.info(f"hook-torchaudio.py: Collected {len(hiddenimports)} hidden imports for torchaudio.")

# It also includes data files, like pre-compiled libraries (.dll, .so),
# that need to be bundled.
logger.info("hook-torchaudio.py: Collecting data files...")
datas = collect_data_files('torchaudio', include_py_files=True)

# Package metadata can also be important for some libraries.
logger.info("hook-torchaudio.py: Collecting metadata...")
datas += copy_metadata('torchaudio')

logger.info(f"hook-torchaudio.py: Collected {len(datas)} total data files and metadata for torchaudio.")