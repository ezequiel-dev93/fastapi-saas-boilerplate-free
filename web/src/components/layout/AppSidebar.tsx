"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { FEATURE_REGISTRY } from "@/core/features/registry";
import { useTranslation } from "@/core/i18n/context";
import { useAuth } from "@/core/auth/auth-context";
import { Badge } from "@/components/ui/badge";
import { Sparkles, LogOut } from "lucide-react";
import { Button } from "@/components/ui/button";

export function AppSidebar() {
  const pathname = usePathname();
  const { t } = useTranslation();
  const { user, logout } = useAuth();
  return (
    <aside className="w-64 border-r border-neutral-200 dark:border-neutral-800 bg-white dark:bg-neutral-950 flex flex-col justify-between h-screen shrink-0 sticky top-0">
      <div>
        {/* Brand / Logo */}
        <div className="h-16 flex items-center px-6 border-b border-neutral-200/80 dark:border-neutral-800/80">
          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 text-white shadow-sm shadow-indigo-500/20">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <span className="text-sm font-bold tracking-tight text-neutral-900 dark:text-neutral-100 block leading-tight">
                FastAPI SaaS
              </span>
              <span className="text-[10px] font-medium text-neutral-400 block uppercase tracking-wider">
                Lite Edition
              </span>
            </div>
          </Link>
        </div>

        {/* Navigation list */}
        <nav className="p-3 space-y-1">
          {FEATURE_REGISTRY.map((feature) => {
            const Icon = feature.icon;
            const label = t.nav[feature.titleKey] || feature.id;
            const isActive =
              pathname === feature.href ||
              (feature.href !== "/dashboard" && pathname.startsWith(feature.href));

            return (
              <Link
                key={feature.id}
                href={feature.href}
                className={`flex items-center justify-between px-3.5 py-2.5 rounded-xl text-xs font-medium transition-all group ${
                  isActive
                    ? "bg-indigo-50 dark:bg-indigo-950/60 text-indigo-600 dark:text-indigo-400 font-semibold shadow-2xs"
                    : "text-neutral-600 dark:text-neutral-400 hover:bg-neutral-100 dark:hover:bg-neutral-900 hover:text-neutral-900 dark:hover:text-neutral-100"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon
                    className={`h-4 w-4 transition-colors ${
                      isActive
                        ? "text-indigo-600 dark:text-indigo-400"
                        : "text-neutral-400 group-hover:text-neutral-700 dark:group-hover:text-neutral-300"
                    }`}
                  />
                  <span>{label}</span>
                </div>
                {feature.badge && (
                  <Badge
                    variant={feature.badge === "AI" ? "default" : "secondary"}
                    className="text-[9px] px-1.5 py-0 uppercase font-bold"
                  >
                    {feature.badge}
                  </Badge>
                )}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom section: User Profile & Logout */}
      <div className="p-3 border-t border-neutral-200 dark:border-neutral-800 space-y-2">

        <div className="flex items-center justify-between px-2 py-1.5 rounded-lg bg-neutral-50 dark:bg-neutral-900/50">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="h-8 w-8 rounded-full bg-indigo-600 text-white font-bold flex items-center justify-center text-xs shrink-0">
              {user?.email?.charAt(0).toUpperCase() || "U"}
            </div>
            <div className="min-w-0 truncate">
              <p className="text-xs font-semibold text-neutral-900 dark:text-neutral-100 truncate">
                {user?.first_name || user?.email?.split("@")[0] || "User"}
              </p>
              <p className="text-[10px] text-neutral-400 truncate">
                {user?.email || ""}
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={logout}
            title={t.nav.signOut}
            className="h-7 w-7 text-neutral-400 hover:text-rose-600"
          >
            <LogOut className="h-3.5 w-3.5" />
          </Button>
        </div>
      </div>
    </aside>
  );
}
