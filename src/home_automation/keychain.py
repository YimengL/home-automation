import subprocess

def get_token(keychain_service: str) -> str:
    """Read a secret from Mac Keychain by service name."""
    result = subprocess.run(
        ["security", "find-generic-password", "-s", keychain_service, "-w"],
        capture_output=True, text=True, check=True
    )

    return result.stdout.strip()