"use client";
import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { setAuthToken } from "../../utils/cookies";

const BACKEND_URL = "http://127.0.0.1:8000";
const SEND_OTP_URL = `${BACKEND_URL}/auth/send-otp`;
const VERIFY_OTP_URL = `${BACKEND_URL}/auth/verify-otp`;

export default function Login() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [otpSentMsg, setOtpSentMsg] = useState("");
  const [errorState, setErrorState] = useState(false);
  const [showSuccessAnimation, setShowSuccessAnimation] = useState(false);
  const [redirectCountdown, setRedirectCountdown] = useState(0);

  useEffect(() => {
    // Load Google Identity Services script
    const script = document.createElement("script");
    script.src = "https://accounts.google.com/gsi/client";
    script.async = true;
    script.defer = true;
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, []);

  // Handle countdown timer for redirect
  useEffect(() => {
    if (redirectCountdown > 0) {
      const timer = setTimeout(() => {
        setRedirectCountdown(redirectCountdown - 1);
      }, 1000);
      return () => clearTimeout(timer);
    }
  }, [redirectCountdown]);

  const handleSendOTP = async () => {
    setLoading(true);
    setError("");
    setSuccess(false);
    setErrorState(false);
    
    // Test bypass for test@gmail.com
    if (email === "test@gmail.com") {
      console.log("[DEBUG] Test email detected - bypassing OTP");
      try {
        const res = await fetch(VERIFY_OTP_URL, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, otp: "000000" }), // Dummy OTP
        });
        if (!res.ok) throw new Error("Test login failed");
        const data = await res.json();
        setAuthToken(data.access_token);
        setSuccess(true);
        setShowSuccessAnimation(true);
        setTimeout(() => {
          // Check for redirect parameter
          const urlParams = new URLSearchParams(window.location.search);
          const redirect = urlParams.get('redirect');
          console.log("[DEBUG] Login redirect parameter:", redirect);
          if (redirect) {
            console.log("[DEBUG] Redirecting to:", decodeURIComponent(redirect));
            router.push(decodeURIComponent(redirect));
          } else {
            console.log("[DEBUG] No redirect parameter, going to home");
            router.push("/");
          }
        }, 3000);
        setLoading(false);
        return;
      } catch (err) {
        setError("Test login failed. Please try again.");
        setLoading(false);
        return;
      }
    }
    
    try {
      const res = await fetch(SEND_OTP_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, purpose: "login" }),
      });

      if (!res.ok) {
        // Handle specific error cases
        if (res.status === 404) {
          const errorData = await res.json().catch(() => ({}));
          if (errorData.detail === "No user found with this email. Please register first.") {
            setError(`No user found with this email. Redirecting to registration page in 3 seconds...`);
            setErrorState(true);
            setRedirectCountdown(3);
            // Redirect to register page after 3 seconds
            setTimeout(() => {
              window.location.href = `/register?email=${encodeURIComponent(email)}`;
            }, 3000);
            setLoading(false);
            return;
          }
        }
        throw new Error("Failed to send OTP");
      }

      setOtpSent(true);
      setOtpSentMsg("OTP sent to your email (check console in backend)");
    } catch (err) {
      setError("Could not send OTP. Please try again.");
      setErrorState(true);
    }
    setLoading(false);
  };

  // Verify OTP
  const handleVerifyOTP = async () => {
    setLoading(true);
    setError("");
    setSuccess(false);
    setErrorState(false);
    try {
      const res = await fetch(VERIFY_OTP_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      if (!res.ok) throw new Error("Invalid OTP");
      const data = await res.json();
      // Store JWT token in localStorage
      setAuthToken(data.access_token);
      setSuccess(true);
      setShowSuccessAnimation(true);
      setTimeout(() => {
        // Check for redirect parameter
        const urlParams = new URLSearchParams(window.location.search);
        const redirect = urlParams.get('redirect');
        console.log("[DEBUG] Login redirect parameter:", redirect);
        if (redirect) {
          console.log("[DEBUG] Redirecting to:", decodeURIComponent(redirect));
          router.push(decodeURIComponent(redirect));
        } else {
          console.log("[DEBUG] No redirect parameter, going to home");
          router.push("/");
        }
      }, 3000);
    } catch (err) {
      setError("Invalid OTP or error verifying. Please try again.");
      setErrorState(true);
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

            <h3 className="text-2xl font-bold text-white mb-2">Login Successful!</h3>
            <p className="text-white/70 mb-6">Welcome back! Redirecting...</p>

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

          <h3 className="text-2xl font-bold text-center text-white mb-2">Welcome Back</h3>

          <p className="text-center text-white/70 mb-8">Enter your email to receive OTP</p>

          <form onSubmit={(e) => e.preventDefault()}>
            {!otpSent ? (
              <>
                <div className="w-full mb-6">
                  <input
                    className="block w-full px-4 py-3 text-white placeholder-white/50 bg-white/10 border border-white/20 rounded-xl backdrop-blur-sm focus:border-white/40 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300"
                    type="email"
                    placeholder="Email Address"
                    aria-label="Email Address"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    disabled={loading}
                  />
                </div>

                <div className="w-full mb-4">
                  <button
                    className="w-full px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-blue-500 to-purple-600 rounded-xl hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                    onClick={handleSendOTP}
                    disabled={loading || !email}
                  >
                    {loading ? "Sending..." : "Send OTP"}
                  </button>
                </div>
                
                <div className="text-center">
                  <span className="text-white/70 text-sm">
                    New user? <a href="/register" className="text-white underline hover:text-white/90 transition-colors">Create account</a>
                  </span>
                </div>
              </>
            ) : (
              <>
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
                    disabled={loading}
                    maxLength={6}
                  />
                </div>

                <div className="w-full mb-4">
                  <button
                    className="w-full px-6 py-3 text-sm font-semibold text-white bg-gradient-to-r from-green-500 to-emerald-600 rounded-xl hover:from-green-600 hover:to-emerald-700 focus:outline-none focus:ring-2 focus:ring-white/20 transition-all duration-300 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                    onClick={handleVerifyOTP}
                    disabled={loading || otp.length !== 6}
                  >
                    {loading ? "Verifying..." : "Verify OTP"}
                  </button>
                </div>

                <div className="text-center">
                  <button
                    type="button"
                    className="text-white/70 text-sm underline hover:text-white/90 transition-colors"
                    onClick={() => setOtpSent(false)}
                    disabled={loading}
                  >
                    Change email
                  </button>
                </div>
              </>
            )}
          </form>
        </div>

        {/* Status Messages */}
        {otpSentMsg && !success && !errorState && (
          <div className="mt-6 p-4 bg-blue-500/20 border border-blue-400/30 rounded-xl backdrop-blur-sm">
            <div className="flex items-center gap-2 text-blue-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm font-medium">{otpSentMsg}</span>
            </div>
          </div>
        )}

        {error && errorState && (
          <div className="mt-6 p-4 bg-red-500/20 border border-red-400/30 rounded-xl backdrop-blur-sm">
            <div className="flex items-center gap-2 text-red-200">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-sm font-medium">
                {redirectCountdown > 0
                  ? `No user found with this email. Redirecting to registration page in ${redirectCountdown} second${redirectCountdown !== 1 ? 's' : ''}...`
                  : error
                }
              </span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center">
          <span className="text-white/50 text-sm">Need help? </span>
          <a href="#" className="text-white/70 text-sm underline hover:text-white transition-colors">Contact Support</a>
        </div>
      </div>
    </div>
  );
}
