import os

# Modules create an Anthropic() client at import time, which needs a key present.
# Offline tests never call the API; a placeholder is enough when no .env exists.
os.environ.setdefault("ANTHROPIC_API_KEY", "offline-test-placeholder")
