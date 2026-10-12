"use client";

import React from "react";
import { useAuth } from "@/core/auth/auth-context";
import { useTranslation } from "@/core/i18n/context";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { User, ShieldCheck } from "lucide-react";

export function OverviewView() {
  const { user } = useAuth();
  const { t } = useTranslation();

  return (
    <section className="space-y-8">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
            {t.overview.welcome},{" "}
            <span className="text-indigo-600 dark:text-indigo-400">
              {user?.first_name || user?.email?.split("@")[0] || "User"}
            </span>
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            {t.overview.liteSubtitle}
          </p>
        </div>
      </div>

      <section className="grid grid-cols-1 md:grid-cols-2 gap-5">
        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
              {t.overview.accountStatus}
            </CardTitle>
            <div className="h-8 w-8 rounded-lg bg-indigo-50 dark:bg-indigo-950/80 text-indigo-600 dark:text-indigo-400 flex items-center justify-center">
              <User className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
                {t.overview.active}
              </span>
            </div>
            <p className="text-[11px] text-neutral-400">
              {t.overview.activeDesc}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-neutral-500 dark:text-neutral-400">
              {t.overview.security}
            </CardTitle>
            <div className="h-8 w-8 rounded-lg bg-emerald-50 dark:bg-emerald-950/80 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
                {t.overview.secured}
              </span>
            </div>
            <p className="text-[11px] text-neutral-400">
              {t.overview.securedDesc}
            </p>
          </CardContent>
        </Card>
      </section>
    </section>
  );
}
