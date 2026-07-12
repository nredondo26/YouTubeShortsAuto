"""Credentials encryption module for secure storage."""

import os
import sys
import json
import base64
from typing import Optional, Dict, Any
from pathlib import Path

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

CREDENTIALS_FILE = os.path.join(ROOT_DIR, ".credentials")
KEY_FILE = os.path.join(ROOT_DIR, ".secret_key")


def _get_or_create_key() -> bytes:
    """Get or create encryption key."""
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "rb") as f:
            return f.read()
    
    # Generate new key
    try:
        from cryptography.fernet import Fernet
        key = Fernet.generate_key()
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        # Restrict permissions on Windows
        if sys.platform == "win32":
            import subprocess
            subprocess.run(["icacls", KEY_FILE, "/inheritance:r", "/grant:r", f"{os.environ.get('USERNAME', 'Everyone')}:R"], capture_output=True)
        else:
            os.chmod(KEY_FILE, 0o600)
        return key
    except ImportError:
        # Fallback if cryptography not installed
        import hashlib
        import secrets
        key_seed = secrets.token_hex(32)
        key = base64.urlsafe_b64encode(hashlib.sha256(key_seed.encode()).digest())
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        return key


def encrypt_value(value: str) -> str:
    """Encrypt a string value.
    
    Args:
        value: Plain text string to encrypt
    
    Returns:
        Encrypted string (base64 encoded)
    """
    try:
        from cryptography.fernet import Fernet
        key = _get_or_create_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(value.encode())
        return base64.urlsafe_b64encode(encrypted).decode()
    except ImportError:
        # Fallback: simple base64 encoding (NOT secure, but better than plain text)
        return base64.urlsafe_b64encode(value.encode()).decode()


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt an encrypted value.
    
    Args:
        encrypted_value: Encrypted string to decrypt
    
    Returns:
        Decrypted plain text string
    """
    try:
        from cryptography.fernet import Fernet
        key = _get_or_create_key()
        fernet = Fernet(key)
        decoded = base64.urlsafe_b64decode(encrypted_value.encode())
        decrypted = fernet.decrypt(decoded)
        return decrypted.decode()
    except ImportError:
        # Fallback: simple base64 decoding
        return base64.urlsafe_b64decode(encrypted_value.encode()).decode()


def encrypt_config(config: Dict[str, Any], sensitive_keys: list = None) -> Dict[str, Any]:
    """Encrypt sensitive values in a config dictionary.
    
    Args:
        config: Configuration dictionary
        sensitive_keys: List of keys to encrypt (default: common sensitive keys)
    
    Returns:
        Config with encrypted sensitive values
    """
    if sensitive_keys is None:
        sensitive_keys = [
            "nanobanana2_api_key",
            "assemblyai_api_key",
            "sender_password",
            "api_key",
            "secret",
            "token",
            "password",
        ]
    
    encrypted_config = config.copy()
    
    for key in sensitive_keys:
        if key in encrypted_config and encrypted_config[key]:
            encrypted_config[key] = encrypt_value(str(encrypted_config[key]))
            encrypted_config[f"{key}_encrypted"] = True
    
    return encrypted_config


def decrypt_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Decrypt sensitive values in a config dictionary.
    
    Args:
        config: Configuration dictionary with encrypted values
    
    Returns:
        Config with decrypted sensitive values
    """
    decrypted_config = config.copy()
    
    keys_to_decrypt = [k for k in decrypted_config.keys() if k.endswith("_encrypted") and decrypted_config[k]]
    
    for encrypted_marker in keys_to_decrypt:
        key = encrypted_marker.replace("_encrypted", "")
        if key in decrypted_config:
            try:
                decrypted_config[key] = decrypt_value(decrypted_config[key])
            except Exception:
                pass  # Keep original value if decryption fails
            del decrypted_config[encrypted_marker]
    
    return decrypted_config


def save_encrypted_config(config: Dict[str, Any], filepath: str = None):
    """Save config with encrypted sensitive values.
    
    Args:
        config: Configuration to save
        filepath: Path to save file (default: config.json)
    """
    if filepath is None:
        filepath = os.path.join(ROOT_DIR, "config.json")
    
    encrypted_config = encrypt_config(config)
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(encrypted_config, f, indent=2, ensure_ascii=False)


def load_encrypted_config(filepath: str = None) -> Dict[str, Any]:
    """Load and decrypt config.
    
    Args:
        filepath: Path to config file (default: config.json)
    
    Returns:
        Decrypted configuration dictionary
    """
    if filepath is None:
        filepath = os.path.join(ROOT_DIR, "config.json")
    
    if not os.path.exists(filepath):
        return {}
    
    with open(filepath, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    return decrypt_config(config)


def migrate_to_encrypted(config_path: str = None):
    """Migrate existing config to encrypted format.
    
    Args:
        config_path: Path to config file (default: config.json)
    """
    if config_path is None:
        config_path = os.path.join(ROOT_DIR, "config.json")
    
    if not os.path.exists(config_path):
        print("Config file not found")
        return
    
    # Load current config
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # Check if already encrypted
    if any(k.endswith("_encrypted") for k in config.keys()):
        print("Config already contains encrypted values")
        return
    
    # Encrypt and save
    save_encrypted_config(config, config_path)
    print(f"Config migrated to encrypted format: {config_path}")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_to_encrypted()
    else:
        print("Usage:")
        print("  python credentials.py migrate  # Migrate config to encrypted format")
