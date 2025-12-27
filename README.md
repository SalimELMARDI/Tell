# Tell

Linux-only CLI that turns natural language into shell commands using Groq and asks for confirmation before running them.

## Visual mode (tell.sh)

1. Install dependencies:
   ```bash
   python3 -m pip install -r requirements.txt
   ```
2. Set your Groq API key (or create a `.env` file):

```bash
export GROQ_API_KEY="your_key_here"
```

3. Run the visual CLI:

```bash
chmod +x tell.sh
./tell.sh
```

## Optional alias for visual mode

```bash
bash install_alias.sh
source ~/.bashrc  # or ~/.zshrc
```

Then run:

```bash
tell
```

## Optional non-visual CLI

```bash
python3 -m pip install .
```

```bash
tell "find all large files over 1GB"
```
