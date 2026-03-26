#!/bin/bash

# Exit on any error
set -e

echo "Starting myBikeFit setup..."

# 1. Define folder paths and target environment details
PROJECT_DIR="myBikeFit"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_CMD="python3"

# 2. Check if Python is installed
if ! command -v $PYTHON_CMD >/dev/null 2>&1; then
    echo "Error: $PYTHON_CMD is not installed or not in PATH."
    echo "Please install Python 3.9+ or change the PYTHON_CMD variable in this script."
    exit 1
fi

# 3. Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists at $VENV_DIR, skipping creation."
fi

# 4. Activate Virtual Environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# 5. Install / Upgrade dependencies
echo "Upgrading pip..."
"$PWD/$VENV_DIR/bin/pip" install --upgrade pip

if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing requirements from requirements.txt..."
    # Installing using the venv's pip explicitly
    "$PWD/$VENV_DIR/bin/pip" install -r "$PROJECT_DIR/requirements.txt"
else
    echo "Warning: requirements.txt not found in $PROJECT_DIR."
fi

# 6. Set Qt plugin path so PyQt6 finds the cocoa platform plugin
PYQT_PATH=$(./myBikeFit/venv/bin/python -c "import PyQt6; import os; print(os.path.join(os.path.dirname(PyQt6.__file__), 'Qt6', 'plugins'))")
export QT_PLUGIN_PATH="$PYQT_PATH"

# 7. Run the application
echo "Starting myBikeFit..."
cd "$PROJECT_DIR"
./venv/bin/python main.py

echo "Application closed."
# Deactivate when done
deactivate
