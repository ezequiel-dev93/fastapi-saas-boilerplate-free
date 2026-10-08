"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/core/auth/auth-context";
import { useTranslation } from "@/core/i18n/context";
import { env } from "@/core/config/env";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Sparkles, UserCheck, ShieldCheck } from "lucide-react";
import { LanguageToggle } from "@/components/layout/LanguageToggle";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import { toast } from "sonner";

interface DevUser {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  organizations?: Array<{ name: string; role: string }>;
}

export default function LoginPage() {
  const { isAuthenticated, authMode, loginWithDevToken, loginWithCognito } = useAuth();
  const { t } = useTranslation();
  const router = useRouter();

  const [devUsers, setDevUsers] = useState<DevUser[]>([]);
  const [customEmail, setCustomEmail] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.push("/dashboard");
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    if (authMode === "dev") {
      fetch(`${env.NEXT_PUBLIC_API_URL}/api/v1/auth/dev-users`)
        .then((res) => (res.ok ? res.json() : []))
        .then((data) => setDevUsers(data))
        .catch(() => setDevUsers([]));
    }
  }, [authMode]);

  const handleDevLogin = async (email: string) => {
    setIsSubmitting(true);
    try {
      await loginWithDevToken(email);
      toast.success(t.common.success);
      router.push("/dashboard");
    } catch (err: unknown) {
      toast.error((err as Error).message || t.common.error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 bg-neutral-50 dark:bg-neutral-950 relative">
      {/* Top Bar Toggles */}
      <div className="absolute top-6 right-6 flex items-center gap-2">
        <LanguageToggle />
        <ThemeToggle />
      </div>

      <div className="w-full max-w-md space-y-6">
        {/* Logo and Brand Title */}
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-md shadow-indigo-500/20 mb-2">
            <Sparkles className="h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
            FastAPI SaaS Boilerplate
          </h1>
          <p className="text-xs text-neutral-500 dark:text-neutral-400">
            Sign in to access your organization dashboard
          </p>
        </div>

        <Card className="border-neutral-200/80 dark:border-neutral-800 shadow-lg">
          <CardHeader className="pb-4">
            <CardTitle className="text-base">Authentication</CardTitle>
            <CardDescription className="text-xs">
              {authMode === "dev"
                ? "Local development mode: One-click instant login enabled."
                : "Enterprise single sign-on with AWS Cognito."}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {authMode === "cognito" ? (
              <div className="space-y-4">
                <Button
                  onClick={loginWithCognito}
                  className="w-full h-11 text-sm font-semibold gap-2"
                >
                  <ShieldCheck className="h-4 w-4" />
                  Continue with AWS Cognito
                </Button>
              </div>
            ) : (
              <div className="space-y-4">
                {devUsers.length > 0 && (
                  <div className="space-y-2">
                    <Label className="text-xs text-neutral-400 font-semibold uppercase tracking-wider">
                      Select Dev Seed User
                    </Label>
                    <div className="space-y-1.5">
                      {devUsers.map((u) => (
                        <button
                          key={u.id}
                          disabled={isSubmitting}
                          onClick={() => handleDevLogin(u.email)}
                          className="w-full flex items-center justify-between p-2.5 rounded-lg border border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800/80 transition-colors text-left cursor-pointer group"
                        >
                          <div className="min-w-0">
                            <p className="text-xs font-semibold text-neutral-800 dark:text-neutral-200 group-hover:text-indigo-600 dark:group-hover:text-indigo-400 truncate">
                              {u.first_name} {u.last_name}
                            </p>
                            <p className="text-[11px] text-neutral-400 truncate">
                              {u.email}
                            </p>
                          </div>
                          <div className="flex items-center gap-1.5">
                            {u.organizations?.[0] && (
                              <span className="text-[10px] bg-neutral-100 dark:bg-neutral-800 px-2 py-0.5 rounded-full text-neutral-600 dark:text-neutral-400 font-medium">
                                {u.organizations[0].role}
                              </span>
                            )}
                            <UserCheck className="h-4 w-4 text-neutral-400 group-hover:text-indigo-600 dark:group-hover:text-indigo-400" />
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                <div className="relative py-2">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-neutral-200 dark:border-neutral-800" />
                  </div>
                  <div className="relative flex justify-center text-[11px] uppercase">
                    <span className="bg-white dark:bg-neutral-900 px-2 text-neutral-400 font-medium">
                      Or type any email
                    </span>
                  </div>
                </div>

                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    if (customEmail) handleDevLogin(customEmail);
                  }}
                  className="space-y-3"
                >
                  <div className="space-y-1.5">
                    <Label htmlFor="email" className="text-xs">
                      Email Address
                    </Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="founder@example.com"
                      value={customEmail}
                      onChange={(e) => setCustomEmail(e.target.value)}
                      required
                    />
                  </div>
                  <Button
                    type="submit"
                    isLoading={isSubmitting}
                    className="w-full h-10 text-xs font-semibold"
                  >
                    Quick Dev Sign In
                  </Button>
                </form>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
