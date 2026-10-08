"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { createCognitoUserManager } from "@/core/auth/cognito-client";

export default function AuthCallbackPage() {
  const router = useRouter();

  useEffect(() => {
    const userManager = createCognitoUserManager();
    if (userManager) {
      userManager
        .signinRedirectCallback()
        .then((user) => {
          if (user?.access_token) {
            localStorage.setItem("saas_access_token", user.access_token);
            if (user.profile) {
              localStorage.setItem(
                "saas_auth_user",
                JSON.stringify({
                  email: user.profile.email,
                  first_name: user.profile.given_name,
                  last_name: user.profile.family_name,
                  cognito_sub: user.profile.sub,
                })
              );
            }
          }
          router.push("/dashboard");
        })
        .catch((err) => {
          console.error("Cognito callback error:", err);
          router.push("/login");
        });
    } else {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="flex h-screen w-full items-center justify-center bg-neutral-50 dark:bg-neutral-950">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-indigo-600 border-t-transparent" />
        <p className="text-xs font-medium text-neutral-400">Authenticating with Cognito...</p>
      </div>
    </div>
  );
}
