"use client";
import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";

export default function OAuthCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code");
      const state = searchParams.get("state");
      const error = searchParams.get("error");

      if (error) {
        // OAuth error occurred
        router.push(`/settings?tab=mcp-servers&oauth_error=${error}`);
        return;
      }

      if (!code || !state) {
        // Missing required parameters
        router.push("/settings?tab=mcp-servers&oauth_error=missing_params");
        return;
      }

      try {
        // The backend will handle the OAuth callback
        // We just need to redirect to the backend callback endpoint
        const callbackUrl = `http://127.0.0.1:8000/auth/oauth/callback?code=${code}&state=${state}`;
        window.location.href = callbackUrl;
      } catch (error) {
        console.error("OAuth callback error:", error);
        router.push("/settings?tab=mcp-servers&oauth_error=callback_failed");
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f7f7f8] dark:bg-[#18181a]">
      <div className="bg-white dark:bg-[#232328] rounded-2xl shadow-lg p-8 max-w-md w-full mx-4">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            Completing Authentication
          </h2>
          <p className="text-gray-600 dark:text-gray-400">
            Please wait while we complete your OAuth authentication...
          </p>
        </div>
      </div>
    </div>
  );
} 