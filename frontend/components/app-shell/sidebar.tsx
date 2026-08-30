"use client";

import {
  Bell,
  Buildings,
  CalendarCheck,
  ChartLine,
  ClockCounterClockwise,
  DoorOpen,
  House,
  Icon,
  Plugs,
  SquaresFour,
  Tag,
  UserCircleGear,
  UsersThree,
} from "@phosphor-icons/react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";
import { useSessionStore } from "@/store/session-store";

export interface NavItem {
  href: string;
  label: string;
  icon: Icon;
  /** Rôles autorisés en plus de is_super_admin ; omis = accessible à tout utilisateur authentifié. */
  requiresRoles?: string[];
}

/**
 * Un item par service front-office-facing implémenté (Sprint 1 à 6) — pas
 * d'items menant vers des pages inexistantes (voir l'écart relevé dans
 * dashboard.html : "Avis"/"Inventaire" sans aucune route). Gating par rôle
 * aligné sur les `require_roles(...)` des endpoints backend correspondants.
 */
export const NAV_ITEMS: NavItem[] = [
  { href: "/reservations", label: "Réservations", icon: CalendarCheck, requiresRoles: ["receptionniste", "manager", "admin"] },
  { href: "/front-office", label: "Front Office", icon: DoorOpen, requiresRoles: ["receptionniste", "manager", "admin"] },
  { href: "/housekeeping", label: "Housekeeping", icon: House },
  { href: "/analytics", label: "Analytics", icon: ChartLine, requiresRoles: ["comptable", "manager", "admin"] },
  { href: "/night-audit", label: "Night Audit", icon: ClockCounterClockwise, requiresRoles: ["manager", "admin"] },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/admin/establishments", label: "Établissements", icon: Buildings, requiresRoles: ["admin"] },
  { href: "/admin/users", label: "Utilisateurs", icon: UserCircleGear, requiresRoles: ["admin"] },
  { href: "/admin/pricing", label: "Tarification", icon: Tag, requiresRoles: ["manager", "admin"] },
  { href: "/admin/partners", label: "Partenaires", icon: UsersThree, requiresRoles: ["manager", "admin"] },
  { href: "/admin/channels", label: "Canaux OTA", icon: Plugs, requiresRoles: ["manager", "admin"] },
];

function NavLink({ item, active, onNavigate }: { item: NavItem; active: boolean; onNavigate?: () => void }) {
  const ItemIcon = item.icon;
  return (
    <Link
      href={item.href}
      onClick={onNavigate}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      <ItemIcon className="size-5" weight={active ? "fill" : "regular"} />
      {item.label}
    </Link>
  );
}

export function canSeeNavItem(item: NavItem, claims: { is_super_admin: boolean; roles: string[] } | null): boolean {
  if (claims?.is_super_admin) return true;
  if (!item.requiresRoles) return true;
  return Boolean(claims?.roles.some((r) => item.requiresRoles!.includes(r)));
}

/** Nav content shared by the fixed desktop sidebar and the mobile Sheet drawer. */
export function SidebarNavContent({ onNavigate }: { onNavigate?: () => void }) {
  const pathname = usePathname();
  const claims = useSessionStore((s) => s.claims);

  const visible = NAV_ITEMS.filter((item) => canSeeNavItem(item, claims));
  const operations = visible.filter((item) => !item.href.startsWith("/admin"));
  const administration = visible.filter((item) => item.href.startsWith("/admin"));

  return (
    <>
      <div className="flex items-center gap-2 border-b border-border px-6 py-5">
        <SquaresFour className="size-6 text-primary" weight="fill" />
        <span className="font-display text-lg font-semibold text-foreground">AMH Hospitality</span>
      </div>

      <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
        <div className="space-y-1">
          {operations.map((item) => (
            <NavLink key={item.href} item={item} active={pathname.startsWith(item.href)} onNavigate={onNavigate} />
          ))}
        </div>

        {administration.length > 0 ? (
          <div className="space-y-1">
            <p className="px-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground/70">
              Administration
            </p>
            {administration.map((item) => (
              <NavLink key={item.href} item={item} active={pathname.startsWith(item.href)} onNavigate={onNavigate} />
            ))}
          </div>
        ) : null}
      </nav>
    </>
  );
}

export function Sidebar() {
  return (
    <aside className="hidden h-screen w-64 flex-col border-r border-border bg-card lg:flex">
      <SidebarNavContent />
    </aside>
  );
}
