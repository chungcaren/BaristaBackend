#!/bin/bash

echo "Starting automated Gemini project setup..."

# 1. Create a Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# 2. Activate the virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# 3. Upgrade pip to avoid warnings
echo "Upgrading pip..."
pip install --upgrade pip

# 4. Install requirements
echo "Installing dependencies from requirements.txt..."
pip install -r requirements.txt

# 5. Run the test script
echo "Running main.py..."
python main.py

echo "Script finished!"