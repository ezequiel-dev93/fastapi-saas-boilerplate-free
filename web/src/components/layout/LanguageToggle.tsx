"use client";

import { useTranslation } from "@/core/i18n/context";
import { Button } from "@/components/ui/button";
import { Globe } from "lucide-react";

export function LanguageToggle() {
  const { locale, setLocale } = useTranslation();

  const toggleLanguage = () => {
    setLocale(locale === "en" ? "es" : "en");
  };

  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={toggleLanguage}
      className="text-xs font-semibold px-2.5 h-8 gap-1.5 text-neutral-600 dark:text-neutral-400"
      title={locale === "en" ? "Cambiar a Español" : "Switch to English"}
    >
      <Globe className="h-3.5 w-3.5" />
      <span>{locale.toUpperCase()}</span>
    </Button>
  );
}
