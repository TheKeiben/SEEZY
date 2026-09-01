#!/bin/bash -i
echo "========================================"
echo "    Starting SEEZY System Controller    "
echo "========================================"

# 1. Navigate to the software directory
cd ~/SEEZY/Software || { echo "Directory not found"; exit 1; }

# 2. Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate || { echo "Failed to activate venv."; exit 1; }

# 3. Launch the application
echo "Booting UI..."
python3 main.py

# 4. Keep the terminal open if the app crashes so you can read the error
#echo "SEEZY UI closed."
#exec bash