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
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold tracking-tight text-foreground">
            {t.overview.welcome},{" "}
            <span className="text-primary dark:text-accent">
              {user?.first_name || user?.email?.split("@")[0] || "User"}
            </span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            {t.overview.liteSubtitle}
          </p>
        </div>
      </div>

      {/* Quick Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {/* Card 1: User Profile */}
        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t.overview.accountStatus}
            </CardTitle>
            <div className="h-9 w-9 rounded-xl bg-accent/20 text-foreground dark:text-accent flex items-center justify-center border border-accent/30">
              <User className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold tracking-tight text-foreground">
                {t.overview.active}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {t.overview.activeDesc}
            </p>
          </CardContent>
        </Card>

        {/* Card 2: Security */}
        <Card>
          <CardHeader className="pb-3 flex flex-row items-center justify-between space-y-0">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {t.overview.security}
            </CardTitle>
            <div className="h-9 w-9 rounded-xl bg-accent-secondary/20 text-foreground dark:text-accent-secondary flex items-center justify-center border border-accent-secondary/30">
              <ShieldCheck className="h-4 w-4" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold tracking-tight text-foreground">
                {t.overview.secured}
              </span>
            </div>
            <p className="text-xs text-muted-foreground">
              {t.overview.securedDesc}
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
