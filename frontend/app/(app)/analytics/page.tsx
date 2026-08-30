"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatTile } from "@/components/stat-tile";
import {
  fetchChannelPerformance,
  fetchKpiConsolidated,
  fetchKpiMonthly,
  fetchKpiToday,
  fetchSegmentsDistribution,
  fetchSegmentsRevenue,
  fetchSegmentsTrend,
  fetchYtdCompare,
} from "@/lib/api-clients/analytics";
import { fetchMarketSegments } from "@/lib/api-clients/reservation";
import { cn } from "@/lib/utils";
import { useSessionStore } from "@/store/session-store";

function currentMonthIso() {
  return new Date().toISOString().slice(0, 7);
}

function DeltaLabel({ value }: { value: number }) {
  return (
    <span className={cn("text-xs font-medium", value >= 0 ? "text-status-success" : "text-status-danger")}>
      {value >= 0 ? "+" : ""}
      {value.toFixed(1)}%
    </span>
  );
}

export default function AnalyticsPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const claims = useSessionStore((s) => s.claims);
  const [month, setMonth] = useState(currentMonthIso());
  const [trendSegment, setTrendSegment] = useState<string>("");
  const [consolidatedMonth, setConsolidatedMonth] = useState(currentMonthIso());

  const { data: today } = useQuery({
    queryKey: ["kpi-today", establishmentId],
    queryFn: () => fetchKpiToday(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const { data: monthly } = useQuery({
    queryKey: ["kpi-monthly", establishmentId, month],
    queryFn: () => fetchKpiMonthly(establishmentId as string, month),
    enabled: Boolean(establishmentId),
  });

  const { data: segments } = useQuery({
    queryKey: ["segments-distribution", establishmentId, month],
    queryFn: () => fetchSegmentsDistribution(establishmentId as string, month),
    enabled: Boolean(establishmentId),
  });

  const { data: segmentsRevenue } = useQuery({
    queryKey: ["segments-revenue", establishmentId, month],
    queryFn: () => fetchSegmentsRevenue(establishmentId as string, month),
    enabled: Boolean(establishmentId),
  });

  const { data: marketSegments } = useQuery({
    queryKey: ["market-segments", establishmentId],
    queryFn: () => fetchMarketSegments(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const { data: trend } = useQuery({
    queryKey: ["segments-trend", establishmentId, trendSegment],
    queryFn: () => fetchSegmentsTrend(establishmentId as string, trendSegment),
    enabled: Boolean(establishmentId && trendSegment),
  });

  const { data: ytd } = useQuery({
    queryKey: ["ytd-compare", establishmentId, month],
    queryFn: () => fetchYtdCompare(establishmentId as string, Number(month.split("-")[1])),
    enabled: Boolean(establishmentId),
  });

  const { data: channelPerf } = useQuery({
    queryKey: ["channel-performance", establishmentId, month],
    queryFn: () => fetchChannelPerformance(establishmentId as string, month),
    enabled: Boolean(establishmentId),
  });

  const isSuperAdmin = Boolean(claims?.is_super_admin);
  const { data: consolidated } = useQuery({
    queryKey: ["kpi-consolidated", consolidatedMonth],
    queryFn: () => fetchKpiConsolidated(consolidatedMonth),
    enabled: isSuperAdmin,
  });

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour voir ses analyses." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Indicateurs de performance et revenus" />

      <div>
        <h2 className="mb-3 text-sm font-semibold uppercase tracking-wider text-muted-foreground">Aujourd&apos;hui</h2>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <StatTile label="Taux d'occupation" value={`${today?.occupancy_rate?.toFixed(1) ?? "—"}%`} />
          <StatTile label="ADR" value={`${today?.adr?.toFixed(2) ?? "—"} MAD`} />
          <StatTile label="RevPAR" value={`${today?.revpar?.toFixed(2) ?? "—"} MAD`} />
          <StatTile label="CA total" value={`${today?.ca_total?.toFixed(2) ?? "—"} MAD`} />
          <StatTile label="Encaissements du jour" value={`${today?.encaissements_total?.toFixed(2) ?? "—"} MAD`} />
        </div>
      </div>

      <div>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Mensuel</h2>
          <div>
            <Label>Mois</Label>
            <Input type="month" value={month} onChange={(e) => setMonth(e.target.value)} />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-5">
          <StatTile label="Taux d'occupation" value={`${monthly?.occupancy_rate?.toFixed(1) ?? "—"}%`} />
          <StatTile label="ADR" value={monthly?.adr?.toFixed(2) ?? "—"} />
          <StatTile label="RevPAR" value={monthly?.revpar?.toFixed(2) ?? "—"} />
          <StatTile label="DMS" value={`${monthly?.dms?.toFixed(1) ?? "—"} nuits`} />
          <StatTile label="CA total" value={monthly?.ca_total?.toFixed(2) ?? "—"} />
        </div>
      </div>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Répartition par segment</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Segment</TableHead>
                <TableHead>Nuitées</TableHead>
                <TableHead>% volume</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(segments?.segments ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={3} className="p-0">
                    <EmptyState className="border-none" title="Aucune donnée" description="Aucune donnée pour ce mois." />
                  </TableCell>
                </TableRow>
              ) : (
                segments?.segments.map((s) => (
                  <TableRow key={s.segment_id}>
                    <TableCell>{s.label}</TableCell>
                    <TableCell>{s.nuitees}</TableCell>
                    <TableCell>{s.pct_volume.toFixed(1)}%</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>CA par segment</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Segment</TableHead>
                <TableHead>CA brut</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {(segmentsRevenue?.segments ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={2} className="p-0">
                    <EmptyState className="border-none" title="Aucune donnée" description="Aucune donnée pour ce mois." />
                  </TableCell>
                </TableRow>
              ) : (
                segmentsRevenue?.segments.map((s) => (
                  <TableRow key={s.segment_id}>
                    <TableCell>{s.label}</TableCell>
                    <TableCell>{s.ca_brut.toFixed(2)} MAD</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
          <CardTitle>Tendance par segment (6 derniers mois)</CardTitle>
          <Select value={trendSegment} onValueChange={setTrendSegment}>
            <SelectTrigger className="w-56">
              <SelectValue placeholder="Choisir un segment" />
            </SelectTrigger>
            <SelectContent>
              {(marketSegments ?? []).map((s) => (
                <SelectItem key={s.id} value={s.code}>
                  {s.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Période</TableHead>
                <TableHead>TO</TableHead>
                <TableHead>ADR</TableHead>
                <TableHead>RevPAR</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {!trendSegment || (trend?.data ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="p-0">
                    <EmptyState
                      className="border-none"
                      title={trendSegment ? "Aucune donnée" : "Choisissez un segment"}
                      description={trendSegment ? undefined : "Sélectionnez un segment de marché ci-dessus pour voir sa tendance."}
                    />
                  </TableCell>
                </TableRow>
              ) : (
                trend?.data.map((d) => (
                  <TableRow key={d.period}>
                    <TableCell>{d.period}</TableCell>
                    <TableCell>{d.to.toFixed(1)}%</TableCell>
                    <TableCell>{d.adr.toFixed(2)}</TableCell>
                    <TableCell>{d.revpar.toFixed(2)}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {ytd && (
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Comparaison année sur année</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[
              { label: "TO", current: `${ytd.current_year.to.toFixed(1)}%`, previous: `${ytd.previous_year.to.toFixed(1)}%`, delta: ytd.deltas.to_pct },
              { label: "ADR", current: ytd.current_year.adr.toFixed(2), previous: ytd.previous_year.adr.toFixed(2), delta: ytd.deltas.adr_pct },
              { label: "CA", current: ytd.current_year.ca.toFixed(2), previous: ytd.previous_year.ca.toFixed(2), delta: ytd.deltas.ca_pct },
            ].map((row) => (
              <div key={row.label} className="rounded-xl bg-muted/50 p-4">
                <p className="text-xs font-medium text-muted-foreground">{row.label}</p>
                <p className="mt-1 flex items-baseline gap-2">
                  <span className="font-display text-xl font-semibold text-foreground">{row.current}</span>
                  <DeltaLabel value={row.delta} />
                </p>
                <p className="text-xs text-muted-foreground">vs {row.previous} l&apos;an dernier</p>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Performance par canal (analytics)</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Canal</TableHead>
              <TableHead>Réservations</TableHead>
              <TableHead>CA</TableHead>
              <TableHead>Commission</TableHead>
              <TableHead>Net</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(channelPerf?.channels ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="p-0">
                  <EmptyState className="border-none" title="Aucune donnée" description="Aucune donnée pour ce mois." />
                </TableCell>
              </TableRow>
            ) : (
              channelPerf?.channels.map((c) => (
                <TableRow key={c.channel}>
                  <TableCell>{c.channel}</TableCell>
                  <TableCell>{c.bookings_count}</TableCell>
                  <TableCell>{c.revenue.toFixed(2)}</TableCell>
                  <TableCell>{c.commission.toFixed(2)}</TableCell>
                  <TableCell>{c.net_revenue.toFixed(2)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      {isSuperAdmin && (
        <Card className="shadow-card">
          <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
            <CardTitle>KPI consolidés (tous établissements)</CardTitle>
            <Input
              type="month"
              value={consolidatedMonth}
              onChange={(e) => setConsolidatedMonth(e.target.value)}
              className="w-40"
            />
          </CardHeader>
          <CardContent className="grid grid-cols-2 gap-4">
            <StatTile label="Nuitées" value={consolidated?.nuitees ?? "—"} />
            <StatTile label="CA total" value={consolidated?.ca_total?.toFixed(2) ?? "—"} />
          </CardContent>
        </Card>
      )}
    </div>
  );
}
