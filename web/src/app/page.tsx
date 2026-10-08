"use client";

import Link from "next/link";
import { useAuth } from "@/core/auth/auth-context";
import { useTranslation } from "@/core/i18n/context";
import { Button } from "@/components/ui/button";
import { LanguageToggle } from "@/components/layout/LanguageToggle";
import { ThemeToggle } from "@/components/layout/ThemeToggle";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Zap,
  Users,
  CreditCard,
  Bot,
  Gauge,
} from "lucide-react";

export default function HomePage() {
  const { isAuthenticated } = useAuth();
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-neutral-50 dark:bg-neutral-950 flex flex-col justify-between">
      {/* Top Navigation */}
      <header className="h-16 border-b border-neutral-200/80 dark:border-neutral-800/80 px-6 max-w-7xl w-full mx-auto flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-sm shadow-indigo-500/20">
            <Sparkles className="h-5 w-5" />
          </div>
          <span className="text-sm font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
            FastAPI SaaS Boilerplate
          </span>
        </div>

        <div className="flex items-center gap-3">
          <LanguageToggle />
          <ThemeToggle />
          {isAuthenticated ? (
            <Link href="/dashboard">
              <Button size="sm" className="gap-1.5 text-xs font-semibold">
                <span>Dashboard</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          ) : (
            <Link href="/login">
              <Button size="sm" className="gap-1.5 text-xs font-semibold">
                <span>Sign In</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          )}
        </div>
      </header>

      {/* Hero Section */}
      <main className="max-w-5xl mx-auto px-6 py-20 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-indigo-200 dark:border-indigo-900/60 bg-indigo-50/60 dark:bg-indigo-950/40 text-xs font-medium text-indigo-700 dark:text-indigo-300">
          <Zap className="h-3.5 w-3.5" />
          <span>Production-Ready Enterprise Stack</span>
        </div>

        <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight text-neutral-900 dark:text-neutral-100 max-w-3xl mx-auto leading-tight">
          Ship your B2B AI SaaS in days, not months.
        </h1>

        <p className="text-base md:text-lg text-neutral-600 dark:text-neutral-400 max-w-2xl mx-auto leading-relaxed">
          Full-stack boilerplate powered by FastAPI, Next.js, AWS Cognito, Stripe, and Redis.
          Includes atomic monthly quotas, AI streaming with SSE, and complete multi-tenancy.
        </p>

        <div className="flex items-center justify-center gap-4 pt-4">
          <Link href={isAuthenticated ? "/dashboard" : "/login"}>
            <Button size="lg" className="gap-2 text-sm font-semibold h-12 px-6">
              <span>{isAuthenticated ? "Go to Dashboard" : "Get Started Now"}</span>
              <ArrowRight className="h-4 w-4" />
            </Button>
          </Link>
          <a
            href="http://localhost:8000/docs"
            target="_blank"
            rel="noreferrer"
          >
            <Button variant="outline" size="lg" className="text-sm font-medium h-12 px-6">
              Swagger API Docs
            </Button>
          </a>
        </div>

        {/* Feature Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-16 text-left">
          <div className="p-6 rounded-2xl border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-neutral-900/60 shadow-xs space-y-3">
            <div className="h-10 w-10 rounded-xl bg-indigo-100 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <Users className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
              Multi-Tenancy & RBAC
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed">
              Workspaces with Owner, Admin, and Member roles. Secure cryptographic email invitations.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-neutral-900/60 shadow-xs space-y-3">
            <div className="h-10 w-10 rounded-xl bg-emerald-100 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <CreditCard className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
              Stripe Subscriptions
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed">
              Customer Portal integration, verified idempotent webhooks, and free trial protection.
            </p>
          </div>

          <div className="p-6 rounded-2xl border border-neutral-200/80 dark:border-neutral-800 bg-white dark:bg-neutral-900/60 shadow-xs space-y-3">
            <div className="h-10 w-10 rounded-xl bg-purple-100 dark:bg-purple-950/80 text-purple-600 dark:text-purple-400 flex items-center justify-center">
              <Bot className="h-5 w-5" />
            </div>
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100 text-sm">
              AI SSE Streaming & Quotas
            </h3>
            <p className="text-xs text-neutral-500 dark:text-neutral-400 leading-relaxed">
              Provider-agnostic streaming (OpenAI & Gemini) with atomic quota deduction and 402 responses.
            </p>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="h-16 border-t border-neutral-200/80 dark:border-neutral-800/80 px-6 max-w-7xl w-full mx-auto flex items-center justify-between text-xs text-neutral-400">
        <span>© 2026 FastAPI SaaS Boilerplate. All rights reserved.</span>
        <div className="flex items-center gap-4">
          <a href="http://localhost:8000/docs" className="hover:text-neutral-600 dark:hover:text-neutral-200">
            API Docs
          </a>
          <a href="http://localhost:8000/health" className="hover:text-neutral-600 dark:hover:text-neutral-200">
            Health Check
          </a>
        </div>
      </footer>
    </div>
  );
}
