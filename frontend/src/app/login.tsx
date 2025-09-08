"use client";
import React, { useState } from "react";

const BACKEND_URL = "http://127.0.0.1:8000";

export default function Login() {
  const [email, setEmail] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [otp, setOtp] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  // Send OTP
  const handleSendOTP = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${BACKEND_URL}/send-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      if (!res.ok) throw new Error("Failed to send OTP");
      setOtpSent(true);
      setSuccess("OTP sent to your email (check console in backend)");
    } catch (err) {
      setError("Could not send OTP. Please try again.");
    }
    setLoading(false);
  };

  // Verify OTP
  const handleVerifyOTP = async () => {
    setLoading(true);
    setError("");
    setSuccess("");
    try {
      const res = await fetch(`${BACKEND_URL}/verify-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, otp }),
      });
      if (!res.ok) throw new Error("Invalid OTP");
      const data = await res.json();
      setSuccess("Login successful! Token: " + data.access_token);
      // TODO: Store token, redirect, etc.
    } catch (err) {
      setError("Invalid OTP or error verifying. Please try again.");
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f7f7f8] dark:bg-gradient-to-r dark:from-[#000046] dark:to-[#1CB5E0]">
      <div className="w-full max-w-sm mx-auto overflow-hidden bg-white rounded-lg shadow-md dark:bg-[#232328] border border-gray-200 dark:border-gray-700">
        <div className="px-6 py-4">
          <div className="flex justify-center mx-auto">
            <img className="w-auto h-7 sm:h-8" src="/favicon.ico" alt="Vee" />
          </div>

          <h3 className="mt-3 text-xl font-medium text-center text-gray-600 dark:text-gray-200">Welcome Back</h3>

          <p className="mt-1 text-center text-gray-500 dark:text-gray-400">Enter your email to receive OTP</p>

          <form onSubmit={(e) => e.preventDefault()}>
            {!otpSent ? (
              <>
                <div className="w-full mt-4">
                  <input 
                    className="block w-full px-4 py-2 mt-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300" 
                    type="email" 
                    placeholder="Email Address" 
                    aria-label="Email Address"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    disabled={loading}
                  />
                </div>

                <div className="w-full mt-4">
                  <button 
                    className="px-6 py-2 text-sm font-medium tracking-wide text-white capitalize transition-colors duration-300 transform bg-blue-500 rounded-lg hover:bg-blue-400 focus:outline-none focus:ring focus:ring-blue-300 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed w-full"
                    onClick={handleSendOTP}
                    disabled={loading || !email}
                  >
                    {loading ? "Sending..." : "Send OTP"}
                  </button>
                </div>
              </>
            ) : (
              <>
                <div className="w-full mt-4">
                  <input 
                    className="block w-full px-4 py-2 mt-2 text-gray-700 placeholder-gray-500 bg-white border rounded-lg dark:bg-gray-800 dark:border-gray-600 dark:placeholder-gray-400 focus:border-blue-400 dark:focus:border-blue-300 focus:ring-opacity-40 focus:outline-none focus:ring focus:ring-blue-300" 
                    type="text" 
                    placeholder="Enter OTP" 
                    aria-label="OTP"
                    value={otp}
                    onChange={e => setOtp(e.target.value)}
                    disabled={loading}
                    maxLength={6}
                  />
                </div>

                <div className="w-full mt-4">
                  <button 
                    className="px-6 py-2 text-sm font-medium tracking-wide text-white capitalize transition-colors duration-300 transform bg-green-500 rounded-lg hover:bg-green-400 focus:outline-none focus:ring focus:ring-green-300 focus:ring-opacity-50 disabled:opacity-50 disabled:cursor-not-allowed w-full"
                    onClick={handleVerifyOTP}
                    disabled={loading || otp.length !== 6}
                  >
                    {loading ? "Verifying..." : "Verify OTP"}
                  </button>
                </div>
              </>
            )}
          </form>
        </div>

        {/* Status Messages */}
        {error && (
          <div className="px-6 py-3 bg-red-50 dark:bg-red-900/20 border-t border-red-200 dark:border-red-800">
            <div className="flex items-center gap-2 text-red-600 dark:text-red-400">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <span className="text-sm">{error}</span>
            </div>
          </div>
        )}

        {success && (
          <div className="px-6 py-3 bg-green-50 dark:bg-green-900/20 border-t border-green-200 dark:border-green-800">
            <div className="flex items-center gap-2 text-green-600 dark:text-green-400">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-sm">{success}</span>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-center py-4 text-center bg-gray-50 dark:bg-gray-700">
          <span className="text-sm text-gray-600 dark:text-gray-200">Need help? </span>
          <a href="#" className="mx-2 text-sm font-bold text-blue-500 dark:text-blue-400 hover:underline">Contact Support</a>
        </div>
      </div>
    </div>
  );
}
