import { ArrowClockwise, WarningCircle } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ErrorStateProps {
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  message = "Une erreur est survenue lors du chargement des données.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-6 py-10 text-center",
        className
      )}
    >
      <WarningCircle className="size-6 text-destructive" />
      <p className="text-sm font-medium text-destructive">{message}</p>
      {onRetry ? (
        <Button variant="outline" size="sm" onClick={onRetry} className="mt-1">
          <ArrowClockwise className="size-3.5" />
          Réessayer
        </Button>
      ) : null}
    </div>
  );
}
