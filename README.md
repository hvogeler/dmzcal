# Activate venv

```
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```

# Check venv

```
echo $VIRTUAL_ENV

which python
```

# Install requirements

```
pip install -r requirements-dev.txt
pip install -e .
```
# Create new venv
```
rm -rf .venv
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -e .
```