"use client";

import { Toaster as SonnerToaster } from "sonner";
import { useTheme } from "next-themes";

export function Toaster() {
  const { theme = "system" } = useTheme();

  return (
    <SonnerToaster
      theme={theme as "light" | "dark" | "system"}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white dark:group-[.toaster]:bg-neutral-900 group-[.toaster]:text-neutral-900 dark:group-[.toaster]:text-neutral-100 group-[.toaster]:border-neutral-200 dark:group-[.toaster]:border-neutral-800 group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-neutral-500 dark:group-[.toast]:text-neutral-400",
          actionButton:
            "group-[.toast]:bg-indigo-600 group-[.toast]:text-white dark:group-[.toast]:bg-indigo-500",
          cancelButton:
            "group-[.toast]:bg-neutral-100 group-[.toast]:text-neutral-600 dark:group-[.toast]:bg-neutral-800 dark:group-[.toast]:text-neutral-300",
        },
      }}
    />
  );
}
