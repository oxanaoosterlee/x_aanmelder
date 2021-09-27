#!/bin/bash
BASH_SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
LIBRARY_DIR="$(dirname "$BASH_SCRIPT_DIR")"
VENV_SCRIPT_DIR="$LIBRARY_DIR/venv/bin/python3" 
SCRIPT_DIR="$LIBRARY_DIR/xaanmelder" 
echo $LIBRARY_DIR
echo $VENV_SCRIPT_DIR
echo $SCRIPT_DIR
gnome-terminal -- $VENV_SCRIPT_DIR $SCRIPT_DIR/x_aanmelder.py