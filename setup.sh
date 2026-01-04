python -m venv venv
source venv/bin/activate
which python # Should return something like ../../CNLC/venv/bin/python
echo "Virtual environment created and activated."


pip install -r requirements.txt --no-cache-dir # Forces python to install from scratch and make sure the requirements aren't corrupted
cat << EOF
=======================================
Setup Complete - Dependencies Installed.
=======================================
To activate the virtual environment in the future, run:
source venv/bin/activate
EOF
