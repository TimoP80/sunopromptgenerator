from PyInstaller.utils.hooks import collect_dynamic_libs, logger
import os
import sys
import glob

def hook(hook_api):
    """
    This hook ensures that the FFmpeg dynamic libraries bundled with `torio`
    are correctly included in the build.
    """
    try:
        import torio
        # The FFmpeg DLLs are in a 'lib' subdirectory of the torio package
        torio_lib_path = os.path.join(os.path.dirname(torio.__file__), 'lib')

        if os.path.isdir(torio_lib_path):
            logger.info(f"hook-torio.py: Manually collecting FFmpeg binaries from torio lib path: {torio_lib_path}")
            
            # Manually collect binaries because `search_dirs` is not supported in older PyInstaller versions.
            binaries = []
            if sys.platform == 'win32':
                file_pattern = '*.dll'
            elif sys.platform == 'darwin':
                file_pattern = '*.dylib'
            else:
                file_pattern = 'libav*.so*' # More specific for FFmpeg libs
            
            search_pattern = os.path.join(torio_lib_path, file_pattern)
            files = glob.glob(search_pattern)
            
            for file_path in files:
                # Add the binary to be placed in the root of the bundle.
                binaries.append((file_path, os.path.basename(file_path)))

            if binaries:
                hook_api.add_binaries(binaries)
                logger.info(f"hook-torio.py: Found and added {len(binaries)} binaries from {torio_lib_path} to the bundle root.")
            else:
                logger.warn(f"hook-torio.py: No dynamic libraries found in {torio_lib_path} matching pattern '{file_pattern}'")

        else:
            logger.warn(f"hook-torio.py: torio lib path not found: {torio_lib_path}. FFmpeg DLLs might be missing.")

        # Also collect any dynamic libs from the main package directory, just in case.
        hook_api.add_binaries(collect_dynamic_libs('torio'))

    except ImportError:
        logger.warn("hook-torio.py: torio package not found. Cannot collect its binaries.")