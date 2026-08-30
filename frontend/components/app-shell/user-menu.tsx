"use client";

import { DeviceMobile, SignOut, User } from "@phosphor-icons/react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useSessionStore } from "@/store/session-store";

function initials(label: string): string {
  const parts = label.replace(/@.*/, "").split(/[.\s_-]+/).filter(Boolean);
  const first = parts[0]?.[0] ?? "";
  const second = parts[1]?.[0] ?? "";
  return (first + second).toUpperCase() || "?";
}

export function UserMenu() {
  const claims = useSessionStore((s) => s.claims);
  if (!claims) return null;

  const label = claims.email ?? claims.sub;

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 rounded-full transition-opacity hover:opacity-80" aria-label="Menu utilisateur">
          <Avatar size="sm">
            <AvatarFallback>{initials(label)}</AvatarFallback>
          </Avatar>
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel className="flex items-center gap-2 py-1.5">
          <User className="size-4 text-muted-foreground" />
          <span className="truncate font-normal text-foreground">{label}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <a href="/link-phone">
            <DeviceMobile className="size-4" />
            Lier mon téléphone (Face ID / empreinte)
          </a>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild variant="destructive">
          <a href="/api/auth/logout">
            <SignOut className="size-4" />
            Déconnexion
          </a>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
