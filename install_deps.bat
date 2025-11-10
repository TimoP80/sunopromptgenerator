@echo off
echo "Installing Python dependencies from requirements.txt..."
pip install -r requirements.txt

echo "Installing Playwright browsers..."
playwright install

echo "Installation complete."
pause