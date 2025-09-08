"use client";
import React, { useState, useEffect } from "react";
import { setAuthToken } from "../../utils/cookies";

const BACKEND_URL = "http://127.0.0.1:8000";
const SEND_OTP_URL = `${BACKEND_URL}/auth/send-otp`;
const VERIFY_OTP_URL = `${BACKEND_URL}/auth/verify-otp`;
const REGISTER_URL = `${BACKEND_URL}/auth/register`;

export default function Register() {
  const [step, setStep] = useState(1);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [otp, setOtp] = useState("");
  const [token, setToken] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);

  // Pre-fill email from URL parameter if present
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const urlParams = new URLSearchParams(window.location.search);
      const emailFromUrl = urlParams.get('email');
      if (emailFromUrl) {
        setEmail(emailFromUrl);
      }
    }
  }, []);



  // Step 1: Send OTP
  const handleSendOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);
    
    // Test bypass for test@gmail.com
    if (email === "test@gmail.com") {
      console.log("[DEBUG] Test email detected - bypassing OTP for registration");
      try {
        // Skip to verification step with dummy OTP
        const verifyRes = await fetch(VERIFY_OTP_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, otp: "000000" }),
        });
        if (!verifyRes.ok) throw new Error("Test verification failed");
        const verifyData = await verifyRes.json();
        setToken(verifyData.access_token);
        
        // Automatically proceed to registration with "Admin" name
        const registerRes = await fetch(REGISTER_URL, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${verifyData.access_token}`,
          },
          body: JSON.stringify({ name: "Admin", email }),
        });
        if (!registerRes.ok) {
          const registerData = await registerRes.json();
          if (registerRes.status === 400 && registerData.detail === "Email already registered.") {
            setError("Email already registered. Redirecting to login...");
            setTimeout(() => {
              window.location.href = "/login";
            }, 2000);
            setLoading(false);
            return;
          }
          throw new Error("Test registration failed");
        }
        setSuccess(true);
        setShowSuccessAnimation(true);
        setTimeout(() => {
          window.location.href = "/";
        }, 3000);
        setLoading(false);
        return;
      } catch (err) {
        setError("Test registration failed. Please try again.");
        setLoading(false);
        return;
      }
    }
    
    try {
      const res = await fetch(SEND_OTP_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, purpose: "register" }),
      });
      if (!res.ok) {
        const data = await res.json();
        if (res.status === 400 && data.detail === "Email already registered.") {
          setError("Email already registered. Redirecting to login...");
          setTimeout(() => {
            window.location.href = "/login";
          }, 2000);
          setLoading(false);
          return;
        }
        throw new Error("Failed to send OTP");
      }
      setStep(2);
    } catch (err) {
      setError("Could not send OTP. Please try again.");
    }
    setLoading(false);
  };

  // Step 2: Verify OTP
  const handleVerifyOtp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);
    try {
      const res = await fetch(VERIFY_OTP_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      if (!res.ok) throw new Error("OTP verification failed");
      const data = await res.json();
      setToken(data.access_token);
      setStep(3);
    } catch (err) {
      setError("Invalid or expired OTP. Please try again.");
    }
    setLoading(false);
  };

  // Step 3: Register
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);
    try {
      const res = await fetch(REGISTER_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ name, email }),
      });
      if (!res.ok) {
        const data = await res.json();
        if (res.status === 400 && data.detail === "Email already registered.") {
          setError("Email already registered. Redirecting to login...");
          setTimeout(() => {
            window.location.href = `/login?email=${encodeURIComponent(email)}`;
          }, 2000);
          setLoading(false);
          return;
        }
        throw new Error("Registration failed");
      }
      setSuccess(true);
      setShowSuccessAnimation(true);
      setTimeout(() => {
        window.location.href = "/";
      }, 3000);
    } catch (err) {
      setError("Could not register. Please try again.");
    }
    setLoading(false);
  };

  if (showSuccessAnimation) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
        {/* Background decorative elements */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 to-blue-900/10 opacity-50"></div>
        <div className="absolute top-20 left-20 w-72 h-72 bg-green-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>

        {/* Glass morphism container */}
        <div className="relative w-full max-w-md mx-auto overflow-hidden backdrop-blur-xl bg-white/10 dark:bg-white/5 rounded-2xl shadow-2xl border border-white/20 dark:border-white/10 p-8">
          <div className="text-center">
            {/* Google Pay-style Success Animation */}
            <div className="relative mb-8">
              <div className="w-24 h-24 mx-auto bg-green-500/20 rounded-full flex items-center justify-center animate-pulse">
                <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center animate-bounce">
                  <svg className="w-12 h-12 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
              </div>
              {/* Ripple effect */}
              <div className="absolute inset-0 w-24 h-24 mx-auto border-4 border-green-400/50 rounded-full animate-ping"></div>
            </div>

            <h3 className="text-2xl font-bold text-white mb-2">Registration Successful!</h3>
            <p className="text-white/70 mb-6">Welcome to Vee! Redirecting to chat...</p>

            {/* Progress bar */}
            <div className="w-full bg-white/20 rounded-full h-2 mb-6">
              <div className="bg-green-400 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 relative overflow-hidden">
      {/* Background decorative elements */}
      <div className="absolute inset-0 bg-gradient-to-br from-purple-900/10 to-blue-900/10 opacity-50"></div>
      <div className="absolute top-20 left-20 w-72 h-72 bg-purple-500/20 rounded-full blur-3xl"></div>
      <div className="absolute bottom-20 right-20 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>

      {/* Glass morphism container */}
      <div className="relative w-full max-w-md mx-auto overflow-hidden backdrop-blur-xl bg-white/10 dark:bg-white/5 rounded-2xl shadow-2xl border border-white/20 dark:border-white/10 p-8">
        <div className="text-center">
          <div className="flex justify-center mx-auto mb-6">
            <img className="w-auto h-8 sm:h-10 drop-shadow-lg" src="/favicon.ico" alt="Vee" />
          </div>

          <h3 className="text-2xl font-bold text-center text-white mb-2">Create Account</h3>

          <p className="text-center text-white/70 mb-8">Join Vee with your name and email</p>

          {step === 1 && (
            <form className="w-full" onSubmit={handleSendOtp}>
              <div className="w-full mb-6">
                <input
                  className="block w-full px-4 py-3 text-white placeholder-white/50 bg-white/10 border border-white/20 rounded-xl backdrop-blur-sm focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300"
                  type="text"
                  placeholder="Full Name"
                  aria-label="Full Name"
                  value={name}
                  onChange={e => setName(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <div className="w-full mb-6">
                <input
                  className="block w-full px-4 py-3 text-white placeholder-white/50 bg-white/10 border border-white/20 rounded-xl backdrop-blur-sm focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300"
                  type="email"
                  placeholder="Email Address"
                  aria-label="Email Address"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  required
                  disabled={loading}
                />
              </div>

              <div className="w-full mb-4">
                <button
                  className="w-full px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                  type="submit"
                  disabled={loading || !name || !email}
                >
                  {loading ? "Sending OTP..." : "Create Account"}
                </button>
              </div>
            </form>
          )}

          {step === 2 && (
            <form className="w-full" onSubmit={handleVerifyOtp}>
              <div className="w-full mb-6">
                <input
                  className="block w-full px-4 py-3 text-white placeholder-white/50 bg-white/10 border border-white/20 rounded-xl backdrop-blur-sm focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300 text-center text-lg font-mono tracking-widest"
                  type="text"
                  placeholder="Enter 6-digit OTP"
                  aria-label="OTP"
                  value={otp}
                  onChange={e => {
                    // Only allow numeric characters and limit to 6 digits
                    const value = e.target.value.replace(/\D/g, '').slice(0, 6);
                    setOtp(value);
                  }}
                  required
                  disabled={loading}
                  maxLength={6}
                />
              </div>

              <div className="w-full mb-4">
                <button
                  className="w-full px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                  type="submit"
                  disabled={loading || !otp}
                >
                  {loading ? "Verifying..." : "Verify OTP"}
                </button>
              </div>

              <div className="text-center">
                <button
                  type="button"
                  className="text-white/70 text-sm underline hover:text-white/90 transition-colors"
                  onClick={() => setStep(1)}
                  disabled={loading}
                >
                  Change email
                </button>
              </div>
            </form>
          )}

          {step === 3 && (
            <form className="w-full" onSubmit={handleRegister}>
              <div className="p-4 mb-6 bg-green-500/20 border border-green-400/30 rounded-xl backdrop-blur-sm">
                <div className="flex items-center gap-2 text-green-200">
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-sm font-medium">OTP verified for <strong>{email}</strong></span>
                </div>
              </div>

              <div className="w-full mb-4">
                <button
                  className="w-full px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl hover:from-green-600 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                  type="submit"
                  disabled={loading}
                >
                  {loading ? "Registering..." : "Complete Registration"}
                </button>
              </div>
            </form>
          )}
        </div>

        {/* Status Messages */}
        {error && (
          <div className="mt-6 p-4 bg-red-500/20 border border-red-400/30 rounded-xl backdrop-blur-sm">
            <div className="flex items-center gap-2 text-red-200">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-sm font-medium">{error}</span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center">
          <span className="text-white/50 text-sm">Already have an account? </span>
          <a href="/login" className="text-white/70 text-sm underline hover:text-white transition-colors">Sign in</a>
        </div>
      </div>
    </div>
  );
}
