"use client";

import { ThemeToggle } from "@/components/theme-toggle";
import { UserMenu } from "@/components/app-shell/user-menu";

import { EstablishmentSwitcher } from "./establishment-switcher";
import { MobileNav } from "./mobile-nav";
import { NotificationBell } from "./notification-bell";

export function Topbar() {
  return (
    <header className="flex h-16 items-center justify-between gap-3 border-b border-border bg-card px-4 sm:px-6">
      <div className="flex items-center gap-2">
        <MobileNav />
        <EstablishmentSwitcher />
      </div>
      <div className="flex items-center gap-2">
        <NotificationBell />
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
