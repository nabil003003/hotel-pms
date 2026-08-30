"use client";

import { useEffect, useRef, useState } from "react";
import { QRCodeSVG } from "qrcode.react";
import { ArrowClockwise, ArrowLeft, QrCode } from "@phosphor-icons/react";

import { Button } from "@/components/ui/button";

type Status = "loading" | "pending" | "claiming" | "expired" | "error";

const POLL_INTERVAL_MS = 2000;

export default function LoginQrPage() {
  const [status, setStatus] = useState<Status>("loading");
  const [phoneUrl, setPhoneUrl] = useState<string | null>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Compteur de génération — invalidé à chaque nouvel appel de begin() (bouton
  // "Nouveau QR code") ET au démontage de l'effet. Sans ça, le double-mount de
  // React StrictMode en dev crée DEUX sessions QR en parallèle : celle
  // affichée à l'écran peut être différente de celle réellement pollée,
  // symptôme observé "ça marche parfois, parfois non".
  const generationRef = useRef(0);

  async function begin() {
    const generation = ++generationRef.current;
    if (pollRef.current) clearInterval(pollRef.current);
    setStatus("loading");

    const res = await fetch("/api/auth/login-link/begin", { method: "POST" });
    if (generation !== generationRef.current) return;
    if (!res.ok) {
      setStatus("error");
      return;
    }
    const { token } = await res.json();
    if (generation !== generationRef.current) return;

    setPhoneUrl(`${window.location.origin}/auth/hybrid-login?token=${token}`);
    setStatus("pending");

    pollRef.current = setInterval(async () => {
      if (generation !== generationRef.current) {
        if (pollRef.current) clearInterval(pollRef.current);
        return;
      }
      const statusRes = await fetch(`/api/auth/login-link/${token}/status`, { cache: "no-store" });
      if (generation !== generationRef.current || !statusRes.ok) return;
      const { status: current } = await statusRes.json();
      if (current === "completed") {
        setStatus("claiming");
        if (pollRef.current) clearInterval(pollRef.current);
        window.location.href = `/api/auth/login-link-claim?token=${token}`;
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
          <QrCode className="size-8 text-primary" weight="fill" />
          <h1 className="font-display text-2xl font-semibold text-foreground">Se connecter</h1>
          <p className="text-sm text-muted-foreground">
            Scannez ce QR code avec votre téléphone pour vous connecter avec votre empreinte digitale.
          </p>
        </div>

        <div className="mx-auto flex aspect-square w-64 items-center justify-center rounded-2xl border border-border bg-card p-4">
          {status === "loading" && <p className="text-sm text-muted-foreground">Génération du QR code…</p>}
          {status === "claiming" && <p className="text-sm text-muted-foreground">Connexion…</p>}
          {status === "error" && <p className="text-sm text-destructive">Une erreur est survenue.</p>}
          {status === "expired" && <p className="text-sm text-muted-foreground">QR code expiré.</p>}
          {status === "pending" && phoneUrl && <QRCodeSVG value={phoneUrl} size={224} />}
        </div>

        {(status === "expired" || status === "error") && (
          <Button onClick={begin} variant="outline" className="mt-4 gap-2">
            <ArrowClockwise className="size-4" />
            Générer un nouveau QR code
          </Button>
        )}

        {status === "pending" && (
          <p className="mt-4 text-xs text-muted-foreground">
            En attente de confirmation sur votre téléphone… (expire dans 2 minutes)
          </p>
        )}

        <Button asChild variant="ghost" className="mt-6 gap-1.5 text-xs text-muted-foreground">
          <a href="/api/auth/login">Se connecter avec mon mot de passe</a>
        </Button>
        <div>
          <Button asChild variant="ghost" className="mt-1 gap-1.5 text-xs text-muted-foreground">
            <a href="/login">
              <ArrowLeft className="size-3" />
              Retour
            </a>
          </Button>
        </div>
      </div>
    </div>
  );
}
