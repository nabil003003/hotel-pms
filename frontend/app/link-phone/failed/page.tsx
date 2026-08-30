import { cookies } from "next/headers";
import { WarningCircle } from "@phosphor-icons/react/dist/ssr";

import { Button } from "@/components/ui/button";
import { COOKIE_PHONE_LINK_TOKEN } from "@/lib/auth/constants";

export default async function LinkPhoneFailedPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get(COOKIE_PHONE_LINK_TOKEN)?.value;

  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background px-4 text-center">
      <WarningCircle className="size-16 text-destructive" weight="fill" />
      <h1 className="font-display text-xl font-semibold text-foreground">Échec de la liaison</h1>
      <p className="max-w-xs text-sm text-muted-foreground">
        L&rsquo;enregistrement de l&rsquo;empreinte n&rsquo;a pas abouti. Vérifiez que votre téléphone
        prend en charge Face ID / empreinte, puis réessayez.
      </p>
      {token ? (
        <Button asChild className="mt-2">
          <a href={`/auth/hybrid?token=${token}`}>Réessayer</a>
        </Button>
      ) : null}
    </div>
  );
}
