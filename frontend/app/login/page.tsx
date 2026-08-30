import { ShieldCheck, SquaresFour, WarningCircle } from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";

const ERROR_MESSAGES: Record<string, string> = {
  missing_pkce_state: "Session de connexion expirée, veuillez réessayer.",
  token_exchange_failed: "Échec de l'authentification. Veuillez réessayer.",
};

// Motif zellige/moucharabieh (losanges + étoile à 8 branches) — tuilable, inspiré des riads de Marrakech.
const ZELLIGE_PATTERN_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" width="72" height="72" viewBox="0 0 72 72">
  <g fill="none" stroke="#fdf3e7" stroke-width="1" stroke-opacity="0.4">
    <path d="M0 36 L36 0 L72 36 L36 72 Z" />
    <path d="M36 10 L50 24 L36 38 L22 24 Z" stroke-opacity="0.55" />
    <path d="M0 0 L14 14 M72 0 L58 14 M0 72 L14 58 M72 72 L58 58" stroke-opacity="0.3" />
  </g>
</svg>`.trim();

const ZELLIGE_PATTERN_URL = `url("data:image/svg+xml,${encodeURIComponent(ZELLIGE_PATTERN_SVG)}")`;

export default function LoginPage({
  searchParams,
}: {
  searchParams: { error?: string };
}) {
  const errorMessage = searchParams.error ? ERROR_MESSAGES[searchParams.error] : null;

  return (
    <div className="grid min-h-screen lg:grid-cols-2">
      <div className="relative hidden flex-col justify-between overflow-hidden bg-primary p-10 text-primary-foreground lg:flex">
        <div
          className="pointer-events-none absolute inset-0 opacity-70"
          style={{ backgroundImage: ZELLIGE_PATTERN_URL, backgroundSize: "72px 72px" }}
        />
        <div
          className="pointer-events-none absolute inset-0 opacity-40"
          style={{
            backgroundImage:
              "radial-gradient(circle at 15% 20%, hsl(var(--primary-foreground) / 0.18), transparent 45%), radial-gradient(circle at 85% 85%, hsl(var(--primary-foreground) / 0.14), transparent 40%)",
          }}
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "linear-gradient(to top, hsl(var(--primary)) 5%, transparent 55%), linear-gradient(to bottom, hsl(var(--primary)) 0%, transparent 30%)",
          }}
        />
        <div className="relative flex items-center gap-2">
          <SquaresFour className="size-6" weight="fill" />
          <span className="text-lg font-semibold">AMH Hospitality</span>
        </div>
        <div className="relative flex flex-col gap-3">
          <p className="font-display text-3xl font-medium leading-tight">
            La gestion hôtelière, avec l&rsquo;élégance des Riads de Marrakech.
          </p>
          <p className="max-w-md text-sm text-primary-foreground/80">
            Réservations, front office, housekeeping et analytics réunis dans un seul système,
            pensé pour vos équipes.
          </p>
        </div>
      </div>

      <div className="flex items-center justify-center bg-background px-4 py-16">
        <div className="w-full max-w-sm">
          <div className="mb-8 flex flex-col items-center gap-1 text-center lg:items-start lg:text-left">
            <div className="mb-2 flex items-center gap-2 lg:hidden">
              <SquaresFour className="size-6 text-primary" weight="fill" />
              <span className="text-lg font-semibold text-foreground">AMH Hospitality</span>
            </div>
            <h1 className="font-display text-2xl font-semibold text-foreground">Bon retour</h1>
            <p className="text-sm text-muted-foreground">Connexion sécurisée à votre espace de gestion</p>
          </div>

          {errorMessage ? (
            <div className="mb-5 flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/5 px-3 py-2.5 text-sm text-destructive">
              <WarningCircle className="mt-0.5 size-4 shrink-0" />
              <span>{errorMessage}</span>
            </div>
          ) : null}

          <Button asChild size="lg" className="w-full">
            <a href="/login/qr">Se connecter</a>
          </Button>

          <p className="mt-6 flex items-center justify-center gap-1.5 text-xs text-muted-foreground lg:justify-start">
            <ShieldCheck className="size-4" weight="fill" />
            Authentification Keycloak (WebAuthn / Passkeys pris en charge)
          </p>
        </div>
      </div>
    </div>
  );
}
