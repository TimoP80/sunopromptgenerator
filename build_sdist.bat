@echo off
echo "Building source distribution..."
python setup.py sdist
echo "Build complete. The distribution is in the dist/ folder."
pause