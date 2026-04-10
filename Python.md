# Installing Python Environment
If you want to run the python scripts in a new environment 
```
uv venv .venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```
_NOTE:_ On my Coder instance of AIDP Core python3.11 was available. Use whatever you find in your environment and hope for the best.

# Run Python Scripts
The scripts should be executable and run directly.

If not type
```
python <script>.py
```
