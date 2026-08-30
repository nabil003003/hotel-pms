import { CheckCircle } from "@phosphor-icons/react/dist/ssr";

export default function LinkPhoneSuccessPage() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-background px-4 text-center">
      <CheckCircle className="size-16 text-primary" weight="fill" />
      <h1 className="font-display text-xl font-semibold text-foreground">Téléphone lié avec succès</h1>
      <p className="max-w-xs text-sm text-muted-foreground">
        Votre empreinte digitale est enregistrée. Retournez à votre ordinateur : il vous amène
        automatiquement à votre tableau de bord.
      </p>
    </div>
  );
}
