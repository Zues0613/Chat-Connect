import random, time
from typing import Dict, Optional

class OTPManager:
    def __init__(self):
        self.otp_store: Dict[str, Dict] = {}

    def generate_otp(self, email: str) -> str:
        otp = f"{random.randint(100000, 999999):06d}"
        self.otp_store[email] = {
            "otp": otp,
            "expires_at": time.time() + 300  # 5 minutes
        }
        return otp

    def verify_otp(self, email: str, otp: str) -> bool:
        entry = self.otp_store.get(email)
        print(f"[DEBUG] Verifying OTP for email: {email}")
        print(f"[DEBUG] Provided OTP: {otp}")
        print(f"[DEBUG] Stored entry: {entry}")
        if not entry:
            print("[DEBUG] No OTP entry found for this email.")
            return False
        if time.time() > entry["expires_at"]:
            print("[DEBUG] OTP expired.")
            self.otp_store.pop(email, None)
            return False
        if entry["otp"] == otp:
            print("[DEBUG] OTP matched. Verification successful.")
            self.otp_store.pop(email, None)
            return True
        print("[DEBUG] OTP did not match.")
        return False
