"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/empty-state";
import { TableRowsSkeleton } from "@/components/loading-state";
import { PageHeader } from "@/components/page-header";
import { fetchConnections, fetchPerformance, upsertConnection } from "@/lib/api-clients/channel-manager";
import { useSessionStore } from "@/store/session-store";

function currentMonthIso() {
  return new Date().toISOString().slice(0, 7);
}

const OTAS = [
  { value: "booking_com", label: "Booking.com" },
  { value: "expedia", label: "Expedia" },
  { value: "airbnb", label: "Airbnb" },
  { value: "direct_website", label: "Site direct" },
];

export default function ChannelsAdminPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const queryClient = useQueryClient();
  const [period, setPeriod] = useState(currentMonthIso());

  const { data: connections, isLoading } = useQuery({
    queryKey: ["channel-connections", establishmentId],
    queryFn: () => fetchConnections(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const { data: performance } = useQuery({
    queryKey: ["channel-performance", establishmentId, period],
    queryFn: () => fetchPerformance(establishmentId as string, period),
    enabled: Boolean(establishmentId),
  });

  const connectMutation = useMutation({
    mutationFn: (otaName: string) =>
      upsertConnection(establishmentId as string, {
        ota_name: otaName,
        is_active: true,
        two_way_sync_enabled: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["channel-connections", establishmentId] });
      toast.success("Connexion OTA activée");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour gérer ses canaux OTA." />;
  }

  const connectedOtas = new Set((connections ?? []).map((c) => c.ota_name));

  return (
    <div className="space-y-6">
      <PageHeader title="Canaux OTA" description="Connexions et performance de synchronisation" />

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Connecter un canal OTA</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-wrap items-end gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              connectMutation.mutate(String(fd.get("ota_name")));
            }}
          >
            <Select name="ota_name" defaultValue={OTAS[0].value}>
              <SelectTrigger className="w-56">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {OTAS.map((o) => (
                  <SelectItem key={o.value} value={o.value}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button type="submit" disabled={connectMutation.isPending}>
              Connecter
            </Button>
          </form>
          {connectedOtas.size < OTAS.length && (
            <p className="mt-2 text-xs text-muted-foreground">
              Non connectés : {OTAS.filter((o) => !connectedOtas.has(o.value)).map((o) => o.label).join(", ")}
            </p>
          )}
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Canal</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Sync bidirectionnelle</TableHead>
              <TableHead>Dernière synchro</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRowsSkeleton rows={3} columns={4} />
            ) : (connections ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="p-0">
                  <EmptyState className="border-none" title="Aucun canal connecté" description="Connectez un premier canal OTA ci-dessus." />
                </TableCell>
              </TableRow>
            ) : (
              (connections ?? []).map((c) => (
                <TableRow key={c.id}>
                  <TableCell className="font-medium">
                    {OTAS.find((o) => o.value === c.ota_name)?.label ?? c.ota_name}
                  </TableCell>
                  <TableCell>
                    <Badge variant={c.is_active ? "default" : "outline"}>
                      {c.is_active ? "Actif" : "Inactif"}
                    </Badge>
                  </TableCell>
                  <TableCell>{c.two_way_sync_enabled ? "Oui" : "Non"}</TableCell>
                  <TableCell>{c.last_sync_at ?? "Jamais"}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Card className="shadow-card">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
          <CardTitle>Performance de synchronisation</CardTitle>
          <div>
            <Label>Période</Label>
            <Input type="month" value={period} onChange={(e) => setPeriod(e.target.value)} />
          </div>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>OTA</TableHead>
              <TableHead>Détail</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!performance || Object.keys(performance.by_ota).length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="p-0">
                  <EmptyState className="border-none" title="Aucune donnée" description="Aucune synchronisation enregistrée pour cette période." />
                </TableCell>
              </TableRow>
            ) : (
              Object.entries(performance.by_ota).map(([ota, stats]) => (
                <TableRow key={ota}>
                  <TableCell className="font-medium">
                    {OTAS.find((o) => o.value === ota)?.label ?? ota}
                  </TableCell>
                  <TableCell>
                    {Object.entries(stats)
                      .map(([k, v]) => `${k}: ${v}`)
                      .join(" · ")}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
