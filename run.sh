echo Starting FramePack-Studio...

if [ -z "$(command -v python)" ]; then
  echo "Did not find a Python binary. Exiting."
  exit 1
fi

if [ ! -f "./venv/bin/activate" ]; then
  echo "Did not find a Python virtual environment. Exiting."
  exit 1
fi

source venv/bin/activate

python studio.py "$@"