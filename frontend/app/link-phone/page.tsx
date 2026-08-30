"use client";

import { useEffect, useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { ArrowClockwise, CheckCircle, DeviceMobile } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";

type Status = "loading" | "pending" | "completed" | "expired" | "error";

const POLL_INTERVAL_MS = 2000;

export default function LinkPhonePage() {
  const [status, setStatus] = useState<Status>("loading");
  const [phoneUrl, setPhoneUrl] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Compteur de génération — invalidé à chaque nouvel appel de begin() ET au
  // démontage de l'effet. Sans ça, le double-mount de React StrictMode en
  // dev crée deux sessions QR en parallèle, désynchronisant ce qui est
  // affiché de ce qui est réellement pollé ("ça marche parfois, parfois non").
  const generationRef = useRef(0);

  async function begin() {
    const generation = ++generationRef.current;
    if (pollRef.current) clearInterval(pollRef.current);
    setStatus("loading");

    const res = await fetch("/api/proxy/auth-gateway/auth/phone-link/begin", { method: "POST" });
    if (generation !== generationRef.current) return;
    if (!res.ok) {
      setStatus("error");
      return;
    }
    const { token } = await res.json();
    if (generation !== generationRef.current) return;

    setPhoneUrl(`${window.location.origin}/auth/hybrid?token=${token}`);
    setStatus("pending");

    pollRef.current = setInterval(async () => {
      if (generation !== generationRef.current) {
        if (pollRef.current) clearInterval(pollRef.current);
        return;
      }
      const statusRes = await fetch(`/api/proxy/auth-gateway/auth/phone-link/${token}/status`, {
        cache: "no-store",
      });
      if (generation !== generationRef.current || !statusRes.ok) return;
      const { status: current } = await statusRes.json();
      if (current === "completed") {
        setStatus("completed");
        if (pollRef.current) clearInterval(pollRef.current);
        // PAS de nouveau round-trip OIDC ici : le desktop a déjà une session
        // app valide (posée par son propre login, avant même le scan du QR)
        // — inutile de redemander à Keycloak. Pire, un aller-retour via
        // /api/auth/login échoue silencieusement en "vrai" login (retour à
        // l'écran mot de passe) : Keycloak invalide par défaut les AUTRES
        // sessions de l'utilisateur ("Se déconnecter des autres appareils")
        // à l'enregistrement d'un nouveau credential WebAuthn passwordless
        // sur le téléphone — ce qui tue justement le cookie SSO du desktop
        // que ce round-trip comptait réutiliser (bug réel constaté en test
        // Playwright avec authenticateur virtuel). On sait déjà que le
        // téléphone vient de lier avec succès, donc direction dashboard.
        window.setTimeout(() => {
          window.location.href = "/housekeeping";
        }, 1200);
      } else if (current === "expired") {
        setStatus("expired");
        if (pollRef.current) clearInterval(pollRef.current);
      }
    }, POLL_INTERVAL_MS);
  }

  useEffect(() => {
    begin();
    return () => {
      generationRef.current++;
      if (pollRef.current) clearInterval(pollRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="w-full max-w-sm text-center">
        <div className="mb-6 flex flex-col items-center gap-2">
          <DeviceMobile className="size-8 text-primary" weight="fill" />
          <h1 className="font-display text-2xl font-semibold text-foreground">Lier votre téléphone</h1>
          <p className="text-sm text-muted-foreground">
            Scannez ce QR code avec l&rsquo;appareil photo de votre téléphone, connectez-vous, puis liez
            votre empreinte digitale ou Face ID.
          </p>
        </div>

        <div className="mx-auto flex aspect-square w-64 items-center justify-center rounded-2xl border border-border bg-card p-4">
          {status === "loading" && <p className="text-sm text-muted-foreground">Génération du QR code…</p>}
          {status === "error" && <p className="text-sm text-destructive">Une erreur est survenue.</p>}
          {status === "expired" && <p className="text-sm text-muted-foreground">QR code expiré.</p>}
          {status === "pending" && phoneUrl && <QRCodeSVG value={phoneUrl} size={224} />}
          {status === "completed" && (
            <div className="flex flex-col items-center gap-2 text-primary">
              <CheckCircle className="size-12" weight="fill" />
              <p className="text-sm font-medium">Téléphone lié avec succès</p>
            </div>
          )}
        </div>

        {(status === "expired" || status === "error") && (
          <Button onClick={begin} variant="outline" className="mt-4 gap-2">
            <ArrowClockwise className="size-4" />
            Générer un nouveau QR code
          </Button>
        )}

        {status === "pending" && (
          <p className="mt-4 text-xs text-muted-foreground">
            En attente de confirmation sur votre téléphone… (expire dans 5 minutes)
          </p>
        )}

        <Button asChild variant="ghost" className="mt-6 text-xs text-muted-foreground">
          <a href="/housekeeping">Continuer sans lier mon téléphone</a>
        </Button>
      </div>
    </div>
  );
}
