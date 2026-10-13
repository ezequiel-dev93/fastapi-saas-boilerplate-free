"use client";

import { useTheme } from "next-themes";
import { useState, useEffect } from "react";
import { Sun, Moon } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <Button
        variant="ghost"
        size="icon"
        className="h-9 w-9 text-muted-foreground opacity-60"
        aria-label="Toggle theme"
        disabled
      >
        <Sun className="h-4 w-4" />
      </Button>
    );
  }

  const isDark = resolvedTheme === "dark";

  const handleToggle = (e: React.MouseEvent<HTMLButtonElement>) => {
    const nextTheme = isDark ? "light" : "dark";

    // 1. Verificar si el usuario prefiere movimiento reducido
    const prefersReducedMotion =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    // 2. Si no hay soporte para View Transitions o prefiere reducir movimiento, cambio normal
    const doc = document as unknown as {
      startViewTransition?: (cb: () => void) => { ready: Promise<void> };
    };

    if (!doc.startViewTransition || prefersReducedMotion) {
      setTheme(nextTheme);
      return;
    }

    // 3. Coordenadas del botón para originar la onda expansiva
    const rect = e.currentTarget.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;

    // 4. Radio máximo necesario para alcanzar la esquina más lejana
    const maxRadius = Math.hypot(
      Math.max(x, window.innerWidth - x),
      Math.max(y, window.innerHeight - y)
    );

    // 5. Iniciar la transición de vista nativa con animación clip-path circular
    const transition = doc.startViewTransition(() => {
      setTheme(nextTheme);
    });

    transition.ready.then(() => {
      document.documentElement.animate(
        {
          clipPath: [
            `circle(0px at ${x}px ${y}px)`,
            `circle(${maxRadius}px at ${x}px ${y}px)`,
          ],
        },
        {
          duration: 450,
          easing: "cubic-bezier(0.4, 0, 0.2, 1)",
          pseudoElement: "::view-transition-new(root)",
        }
      );
    });
  };

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={handleToggle}
      title={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
      className="relative h-9 w-9 rounded-lg text-foreground hover:bg-muted/80 transition-colors overflow-hidden"
    >
      {/* Icono del Sol (animación de rotación y escalado) */}
      <Sun
        className={`h-4 w-4 text-accent transition-all duration-300 absolute ${
          isDark
            ? "rotate-0 scale-100 opacity-100"
            : "-rotate-90 scale-0 opacity-0"
        }`}
      />

      {/* Icono de la Luna (animación de rotación y escalado) */}
      <Moon
        className={`h-4 w-4 text-foreground transition-all duration-300 absolute ${
          isDark
            ? "rotate-90 scale-0 opacity-0"
            : "rotate-0 scale-100 opacity-100"
        }`}
      />

      <span className="sr-only">Cambiar tema visual</span>
    </Button>
  );
}
