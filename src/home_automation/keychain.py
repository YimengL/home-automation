import os
import subprocess

def get_token(keychain_service: str) -> str:
    """Read a secret from Mac Keychain by service name."""
    env_key = keychain_service.upper().replace("-", "_")
    if env_key in os.environ:
        return os.environ[env_key]
    result = subprocess.run(
        ["security", "find-generic-password", "-s", keychain_service, "-w"],
        capture_output=True, text=True, check=True
    )

    return result.stdout.strip()