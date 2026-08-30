"use client";

import { useState } from "react";
import { List } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle } from "@/components/ui/sheet";
import { SidebarNavContent } from "@/components/app-shell/sidebar";

export function MobileNav() {
  const [open, setOpen] = useState(false);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Ouvrir le menu" onClick={() => setOpen(true)}>
        <List className="size-5" />
      </Button>
      <SheetContent side="left" className="w-72 p-0 sm:max-w-none">
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <SidebarNavContent onNavigate={() => setOpen(false)} />
      </SheetContent>
    </Sheet>
  );
}
