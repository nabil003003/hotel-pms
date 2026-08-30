"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { CheckCircle, WarningCircle } from "@phosphor-icons/react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import {
  closeAudit,
  fetchBusinessDate,
  fetchDiscrepancyReport,
  reportDownloadUrl,
  verifyAudit,
  type CloseResult,
  type VerifyResult,
} from "@/lib/api-clients/night-audit";
import { Download } from "@phosphor-icons/react";
import { useSessionStore } from "@/store/session-store";

export default function NightAuditPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const queryClient = useQueryClient();
  const [verifyResult, setVerifyResult] = useState<VerifyResult | null>(null);
  const [closeResult, setCloseResult] = useState<CloseResult | null>(null);

  const { data: businessDate } = useQuery({
    queryKey: ["night-audit-business-date", establishmentId],
    queryFn: () => fetchBusinessDate(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const { data: discrepancyReport } = useQuery({
    queryKey: ["discrepancy-report", establishmentId, businessDate?.business_date],
    queryFn: () => fetchDiscrepancyReport(establishmentId as string, businessDate!.business_date),
    enabled: Boolean(establishmentId && businessDate && verifyResult && verifyResult.discrepancy !== 0),
  });

  const verifyMutation = useMutation({
    mutationFn: () => verifyAudit(establishmentId as string, businessDate!.business_date),
    onSuccess: (result) => {
      setVerifyResult(result);
      setCloseResult(null);
      if (result.discrepancy === 0) {
        toast.success("Vérification réussie — journée équilibrée");
      } else {
        toast.error(`Écart détecté : ${result.discrepancy} MAD`);
      }
    },
    onError: (error: Error & { discrepancy?: number }) => {
      toast.error(error.message);
      if (error.discrepancy !== undefined) {
        setVerifyResult({ token_audit: "", total_debits: 0, total_credits: 0, discrepancy: error.discrepancy, status: "error" });
      }
    },
  });

  const closeMutation = useMutation({
    mutationFn: () => closeAudit(establishmentId as string, businessDate!.business_date, verifyResult!.token_audit),
    onSuccess: (result) => {
      setCloseResult(result);
      setVerifyResult(null);
      queryClient.invalidateQueries({ queryKey: ["night-audit-business-date", establishmentId] });
      toast.success(`Clôture effectuée — nouvelle date métier ${result.new_business_date}`);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour lancer le night audit." />;
  }

  const progress = closeResult ? 100 : verifyResult ? 50 : 0;

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader title="Night Audit" description="Vérification et clôture de la journée métier" />

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Clôture journalière</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Progress value={progress} />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>1. Vérification</span>
              <span>2. Clôture</span>
            </div>
          </div>

          <p className="text-sm text-muted-foreground">
            Date métier en cours : <span className="font-semibold text-foreground">{businessDate?.business_date ?? "…"}</span>
          </p>

          <Button
            onClick={() => verifyMutation.mutate()}
            disabled={verifyMutation.isPending || !businessDate}
          >
            1. Vérifier (débits = crédits)
          </Button>

          {verifyResult && (
            <Alert variant={verifyResult.discrepancy === 0 ? "default" : "destructive"}>
              {verifyResult.discrepancy === 0 ? (
                <CheckCircle className="text-status-success" weight="fill" />
              ) : (
                <WarningCircle weight="fill" />
              )}
              <AlertTitle>
                {verifyResult.discrepancy === 0 ? "Journée équilibrée" : `Écart détecté : ${verifyResult.discrepancy.toFixed(2)} MAD`}
              </AlertTitle>
              <AlertDescription className="space-y-2">
                <p>Total débits : {verifyResult.total_debits.toFixed(2)} MAD</p>
                <p>Total crédits : {verifyResult.total_credits.toFixed(2)} MAD</p>
                {verifyResult.discrepancy === 0 && verifyResult.token_audit && (
                  <Button size="sm" onClick={() => closeMutation.mutate()} disabled={closeMutation.isPending}>
                    2. Clôturer la journée (irréversible)
                  </Button>
                )}
              </AlertDescription>
            </Alert>
          )}

          {discrepancyReport && discrepancyReport.length > 0 && (
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle className="text-sm">Folios en écart</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Type</TableHead>
                      <TableHead>Réservation</TableHead>
                      <TableHead>Solde</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {discrepancyReport.map((d) => (
                      <TableRow key={d.folio_id}>
                        <TableCell>{d.type}</TableCell>
                        <TableCell>{d.booking_id.slice(0, 8)}…</TableCell>
                        <TableCell>{d.balance.toFixed(2)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}

          {closeResult && (
            <Alert className="border-status-success/30 bg-status-success/5">
              <CheckCircle className="text-status-success" weight="fill" />
              <AlertTitle>Journée {closeResult.business_date} clôturée</AlertTitle>
              <AlertDescription className="space-y-1.5">
                <p>
                  Nouvelle date métier : <span className="font-semibold text-foreground">{closeResult.new_business_date}</span>
                </p>
                <p className="text-xs">Hash rapport : {closeResult.report_hash}</p>
                <ul className="space-y-1 text-xs">
                  {Object.keys(closeResult.report_urls).map((name) => (
                    <li key={name}>
                      <a
                        href={reportDownloadUrl(establishmentId as string, closeResult.business_date, name)}
                        download={name}
                        className="inline-flex items-center gap-1.5 text-foreground underline underline-offset-2 hover:text-status-success"
                      >
                        <Download />
                        {name}
                      </a>
                    </li>
                  ))}
                </ul>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
