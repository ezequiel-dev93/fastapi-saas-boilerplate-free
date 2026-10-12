"use client";

import React from "react";
import Link from "next/link";
import {
  Terminal,
  Zap,
  Code2,
  Lock,
  Layers,
  Shield,
  ArrowRight,
  ExternalLink,
  CheckCircle2,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const GITHUB_FREE_URL = "https://github.com/ezequiel-dev93/fastapi-saas-boilerplate-free";

export default function FreeHomePage() {
  return (
    <main className="min-h-screen bg-[#111111] text-[#FFFFFF] font-sans selection:bg-[#D7FF00] selection:text-[#111111]">
      <div className="bg-gradient-to-r from-[#111111] via-[#1a1d05] to-[#111111] border-b border-[#D7FF00]/30 py-2.5 px-6 text-center text-xs">
        <span className="text-[#a0a0a0]">
          🚀 You are running the <strong className="text-[#FFFFFF]">Lite / Open Source Edition</strong>. Want Stripe, Claude 3.5 AI streaming & Multi-tenant teams?
        </span>{" "}
        <a
          href="https://your-lemonsqueezy-link.com"
          target="_blank"
          rel="noreferrer"
          className="text-[#D7FF00] font-bold underline underline-offset-2 ml-1 hover:text-[#c6eb00] inline-flex items-center gap-1"
        >
          <span>Upgrade to PRO</span>
          <ArrowRight className="h-3 w-3 inline" />
        </a>
      </div>

      <nav className="flex items-center justify-between px-6 py-6 max-w-6xl mx-auto border-b border-[#2b2b2b]">
        <div className="flex items-center gap-2.5">
          <div className="h-8 w-8 bg-[#111111] border border-[#D7FF00]/50 text-[#D7FF00] flex items-center justify-center font-bold rounded-lg shadow-sm shadow-[#D7FF00]/10">
            <Terminal className="h-4 w-4" />
          </div>
          <div>
            <span className="text-base font-bold tracking-tight block leading-none text-[#FFFFFF]">
              FastAPI SaaS
            </span>
            <span className="text-[10px] text-[#D7FF00] font-mono uppercase tracking-widest font-semibold">
              Lite Edition
            </span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <a
            href={GITHUB_FREE_URL}
            target="_blank"
            rel="noreferrer"
            className="text-xs font-mono text-[#a0a0a0] hover:text-[#FFFFFF] transition-colors hidden sm:inline-flex items-center gap-1"
          >
            <span>GitHub Repository</span>
            <ExternalLink className="h-3 w-3" />
          </a>
          <Link href="/login">
            <Button size="sm" variant="outline" className="border-[#333333] bg-[#181818] hover:bg-[#252525] text-[#FFFFFF] text-xs">
              Go to Dashboard →
            </Button>
          </Link>
        </div>
      </nav>

      <section className="max-w-5xl mx-auto px-6 py-20 text-center space-y-8">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full border border-[#D7FF00]/30 bg-[#D7FF00]/10 text-[#D7FF00] text-xs font-mono font-semibold">
          <Zap className="h-3.5 w-3.5" />
          <span>Production-Ready Python + Next.js Starter</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight max-w-3xl mx-auto leading-tight text-[#FFFFFF]">
          Clean architecture foundation for your next web application.
        </h1>

        <p className="text-base sm:text-lg text-[#a0a0a0] max-w-2xl mx-auto font-light leading-relaxed">
          The free edition gives you a modern, battle-tested stack with FastAPI 0.115+, Next.js 16, asynchronous SQLAlchemy 2.0, and instant local authentication.
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 pt-2">
          <a href={GITHUB_FREE_URL} target="_blank" rel="noreferrer">
            <Button size="lg" className="bg-[#D7FF00] hover:bg-[#c6eb00] text-[#111111] font-bold text-xs h-12 px-6 gap-2 shadow-lg shadow-[#D7FF00]/20">
              <span>Clone Free on GitHub</span>
              <ExternalLink className="h-4 w-4" />
            </Button>
          </a>
          <Link href="/login">
            <Button variant="outline" size="lg" className="border-[#333333] bg-[#181818] hover:bg-[#252525] text-[#FFFFFF] text-xs h-12 px-6">
              Test Local Auth / Dashboard
            </Button>
          </Link>
        </div>
      </section>

      <section className="py-20 border-t border-[#222222] bg-[#141414]">
        <div className="max-w-6xl mx-auto px-6">
          <div className="text-center max-w-2xl mx-auto mb-16">
            <span className="text-xs font-mono uppercase tracking-widest text-[#D7FF00] font-semibold">
              Included Features
            </span>
            <h2 className="text-3xl sm:text-4xl font-bold tracking-tight mt-2 text-[#FFFFFF]">
              What is implemented in this Free edition?
            </h2>
            <p className="text-[#a0a0a0] text-sm mt-3">
              Everything in this repository is 100% functional, without broken stubs or hidden dependencies.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="p-6 rounded-2xl bg-[#181818] border border-[#2b2b2b] space-y-3">
              <div className="h-10 w-10 rounded-xl bg-[#D7FF00]/10 text-[#D7FF00] flex items-center justify-center border border-[#D7FF00]/20">
                <Code2 className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base text-[#FFFFFF]">FastAPI Backend</h3>
              <p className="text-xs text-[#a0a0a0] leading-relaxed">
                Async SQLAlchemy 2.0 with PostgreSQL/SQLite, Alembic migrations, Pydantic v2 schemas, and health check endpoints.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#181818] border border-[#2b2b2b] space-y-3">
              <div className="h-10 w-10 rounded-xl bg-[#D7FF00]/10 text-[#D7FF00] flex items-center justify-center border border-[#D7FF00]/20">
                <Lock className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base text-[#FFFFFF]">Dev Auth & JWT</h3>
              <p className="text-xs text-[#a0a0a0] leading-relaxed">
                Local bypass login for rapid testing without cloud services, plus standard secure JWT token handlers.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#181818] border border-[#2b2b2b] space-y-3">
              <div className="h-10 w-10 rounded-xl bg-[#D7FF00]/10 text-[#D7FF00] flex items-center justify-center border border-[#D7FF00]/20">
                <Layers className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base text-[#FFFFFF]">Next.js 16 Frontend</h3>
              <p className="text-xs text-[#a0a0a0] leading-relaxed">
                App Router, Tailwind CSS styling, React Query data fetching, Zod form validation, and responsive dashboard sidebar.
              </p>
            </div>

            <div className="p-6 rounded-2xl bg-[#181818] border border-[#2b2b2b] space-y-3">
              <div className="h-10 w-10 rounded-xl bg-[#D7FF00]/10 text-[#D7FF00] flex items-center justify-center border border-[#D7FF00]/20">
                <Shield className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-base text-[#FFFFFF]">GDPR Privacy Tools</h3>
              <p className="text-xs text-[#a0a0a0] leading-relaxed">
                JSON data portability export and soft-anonymization account deletion conforming to privacy regulations.
              </p>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 border-t border-[#222222] max-w-4xl mx-auto px-6">
        <div className="p-8 rounded-2xl bg-gradient-to-b from-[#181818] to-[#121212] border border-[#D7FF00]/30 space-y-6 shadow-xl shadow-black/40">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <span className="text-xs font-mono uppercase tracking-widest text-[#D7FF00] font-semibold">
                Ready to monetize?
              </span>
              <h3 className="text-2xl font-bold mt-1 text-[#FFFFFF]">Upgrade to the PRO Edition</h3>
            </div>
            <a
              href="https://your-lemonsqueezy-link.com"
              target="_blank"
              rel="noreferrer"
            >
              <Button className="bg-[#D7FF00] hover:bg-[#c6eb00] text-[#111111] font-bold text-xs h-10 px-5 shrink-0 shadow-md shadow-[#D7FF00]/20">
                Get PRO Edition →
              </Button>
            </a>
          </div>

          <p className="text-xs text-[#a0a0a0] leading-relaxed">
            The PRO edition adds all the revenue-generating modules that take weeks to implement from scratch:
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-[#FFFFFF] pt-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#9EFF00] shrink-0" />
              <span>Stripe Subscriptions & Customer Portal</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#9EFF00] shrink-0" />
              <span>Claude 3.5 & OpenAI SSE Streaming</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#9EFF00] shrink-0" />
              <span>Multi-Tenant Organizations & Teams (RBAC)</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#9EFF00] shrink-0" />
              <span>Organization API Keys & BYOK System</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#9EFF00] shrink-0" />
              <span>AWS Cognito Enterprise Authentication</span>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-[#9EFF00] shrink-0" />
              <span>183+ Automated Tests (100% Coverage)</span>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#222222] py-8 px-6 text-center text-xs font-mono text-[#5A5A5A]">
        <p>FastAPI SaaS Boilerplate (Lite Edition) • Open Source under MIT License</p>
      </footer>
    </main>
  );
}
