"use client";

import React from "react";
import { ThemeToggle } from "./ThemeToggle";
import { LanguageToggle } from "./LanguageToggle";
import { useTranslation } from "@/core/i18n/context";

export function Header() {
  const { t } = useTranslation();

  return (
    <header className="h-16 border-b border-border bg-card/85 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-40">
      <div className="flex items-center gap-4">
        <h2 className="text-sm font-semibold text-foreground">
          {t.nav.overview}
        </h2>
      </div>

      <div className="flex items-center gap-2">
        <LanguageToggle />
        <ThemeToggle />
      </div>
    </header>
  );
}
