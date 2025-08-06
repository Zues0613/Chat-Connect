import random, time
from typing import Dict, Optional

class OTPManager:
    def __init__(self):
        self.otp_store: Dict[str, Dict] = {}
        # Test email bypass for development
        self.test_email = "test@gmail.com"
        self.test_otp = "000000"  # Always valid for test email

    def generate_otp(self, email: str) -> str:
        # For test email, return the test OTP without storing
        if email == self.test_email:
            print(f"[DEBUG] Test email detected: {email}, using bypass OTP")
            return self.test_otp
            
        otp = f"{random.randint(100000, 999999):06d}"
        self.otp_store[email] = {
            "otp": otp,
            "expires_at": time.time() + 300  # 5 minutes
        }
        return otp

    def verify_otp(self, email: str, otp: str) -> bool:
        # Special bypass for test email
        if email == self.test_email:
            print(f"[DEBUG] Test email verification: {email}")
            if otp == self.test_otp:
                print("[DEBUG] Test email OTP verified successfully")
                return True
            else:
                print(f"[DEBUG] Test email OTP mismatch: expected {self.test_otp}, got {otp}")
                return False
        
        # Normal OTP verification for other emails
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
