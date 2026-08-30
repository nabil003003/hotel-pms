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
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { EmptyState } from "@/components/empty-state";
import { InlineEditRow } from "@/components/inline-edit-row";
import { TableRowsSkeleton } from "@/components/loading-state";
import { PageHeader } from "@/components/page-header";
import { fetchPartners } from "@/lib/api-clients/partner";
import {
  calculateRate,
  createExtra,
  createPackage,
  createPartnerRate,
  createRateGridEntry,
  createSeason,
  createTax,
  fetchExtras,
  fetchPackages,
  fetchPartnerRates,
  fetchRateGrid,
  fetchSeasons,
  fetchTaxes,
  updateExtra,
  updatePackage,
  updateRateGridEntry,
  updateSeason,
  updateTax,
  type RateCalculateResult,
  type RateGridEntry,
  type Season,
} from "@/lib/api-clients/pricing";
import { useSessionStore } from "@/store/session-store";

const ROOM_CATEGORIES = [
  "Chambre Standard",
  "Chambre Deluxe",
  "Suite Junior",
  "Suite Royale",
  "Riad Entier",
];

function ActiveBadge({ active }: { active: boolean }) {
  return (
    <Badge
      variant="outline"
      className={active ? "border-status-success/30 bg-status-success/10 text-status-success" : "text-muted-foreground"}
    >
      {active ? "Active" : "Inactive"}
    </Badge>
  );
}

export default function PricingAdminPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const queryClient = useQueryClient();
  const [editingRate, setEditingRate] = useState<RateGridEntry | null>(null);
  const [calcResult, setCalcResult] = useState<RateCalculateResult | null>(null);

  const { data: seasons, isLoading: seasonsLoading } = useQuery({
    queryKey: ["seasons", establishmentId],
    queryFn: () => fetchSeasons(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
  const { data: rateGrid, isLoading: rateGridLoading } = useQuery({
    queryKey: ["rate-grid", establishmentId],
    queryFn: () => fetchRateGrid(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
  const { data: taxes, isLoading: taxesLoading } = useQuery({
    queryKey: ["taxes", establishmentId],
    queryFn: () => fetchTaxes(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
  const { data: extras, isLoading: extrasLoading } = useQuery({
    queryKey: ["extras", establishmentId],
    queryFn: () => fetchExtras(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
  const { data: partnerRates, isLoading: partnerRatesLoading } = useQuery({
    queryKey: ["partner-rates", establishmentId],
    queryFn: () => fetchPartnerRates(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
  const { data: packages, isLoading: packagesLoading } = useQuery({
    queryKey: ["packages", establishmentId],
    queryFn: () => fetchPackages(establishmentId as string),
    enabled: Boolean(establishmentId),
  });
  const { data: partners } = useQuery({
    queryKey: ["partners", establishmentId],
    queryFn: () => fetchPartners(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const seasonMutation = useMutation({
    mutationFn: (input: { label: string; date_debut: string; date_fin: string }) =>
      createSeason(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["seasons", establishmentId] });
      toast.success("Saison créée");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const toggleSeasonMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateSeason(establishmentId as string, id, { is_active }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["seasons", establishmentId] });
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const rateGridMutation = useMutation({
    mutationFn: (input: {
      room_category: string;
      season_id: string;
      regime: string;
      prix_ttc: number;
      prix_ht: number;
      tva_rate: number;
    }) => createRateGridEntry(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rate-grid", establishmentId] });
      toast.success("Tarif ajouté");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const editRateMutation = useMutation({
    mutationFn: ({ id, prix_ht, prix_ttc }: { id: string; prix_ht: number; prix_ttc: number }) =>
      updateRateGridEntry(establishmentId as string, id, { prix_ht, prix_ttc }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["rate-grid", establishmentId] });
      setEditingRate(null);
      toast.success("Tarif mis à jour");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const taxMutation = useMutation({
    mutationFn: (input: { type: string; taux_ou_montant: number; mode_calcul: string }) =>
      createTax(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["taxes", establishmentId] });
      toast.success("Taxe ajoutée");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const toggleTaxMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateTax(establishmentId as string, id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["taxes", establishmentId] }),
    onError: (error: Error) => toast.error(error.message),
  });

  const extraMutation = useMutation({
    mutationFn: (input: { categorie: string; libelle: string; prix_ht: number; tva_rate: number }) =>
      createExtra(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["extras", establishmentId] });
      toast.success("Extra ajouté au catalogue");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const toggleExtraMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateExtra(establishmentId as string, id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["extras", establishmentId] }),
    onError: (error: Error) => toast.error(error.message),
  });

  const partnerRateMutation = useMutation({
    mutationFn: (input: {
      partner_id: string;
      season_id: string;
      room_category: string;
      regime: string;
      tarif_negocie: number;
      commission_pct: number;
    }) => createPartnerRate(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partner-rates", establishmentId] });
      toast.success("Tarif négocié ajouté");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const packageMutation = useMutation({
    mutationFn: (input: { label: string; description?: string; prix_global_ttc: number; ventilation: Record<string, number> }) =>
      createPackage(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["packages", establishmentId] });
      toast.success("Forfait créé");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const togglePackageMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updatePackage(establishmentId as string, id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["packages", establishmentId] }),
    onError: (error: Error) => toast.error(error.message),
  });

  const calcMutation = useMutation({
    mutationFn: (input: { room_category: string; regime: string; date_from: string; date_to: string }) =>
      calculateRate({ establishment_id: establishmentId as string, ...input }),
    onSuccess: (result) => setCalcResult(result),
    onError: (error: Error) => toast.error(error.message),
  });

  const partnerLabel = (id: string) => partners?.find((p) => p.id === id)?.nom ?? id.slice(0, 8);
  const seasonLabel = (id: string) => seasons?.find((s) => s.id === id)?.label ?? id.slice(0, 8);

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour gérer sa tarification." />;
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Tarification" description="Saisons, grille tarifaire, taxes, extras, tarifs négociés et forfaits" />

      <Tabs defaultValue="seasons" className="space-y-4">
        <div className="overflow-x-auto pb-1">
          <TabsList>
            <TabsTrigger value="seasons">Saisons</TabsTrigger>
            <TabsTrigger value="rate-grid">Grille tarifaire</TabsTrigger>
            <TabsTrigger value="taxes">Taxes</TabsTrigger>
            <TabsTrigger value="extras">Extras</TabsTrigger>
            <TabsTrigger value="partner-rates">Tarifs négociés</TabsTrigger>
            <TabsTrigger value="packages">Forfaits</TabsTrigger>
            <TabsTrigger value="calculator">Calculateur</TabsTrigger>
          </TabsList>
        </div>

        <TabsContent value="seasons" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Nouvelle saison</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  seasonMutation.mutate({
                    label: String(fd.get("label")),
                    date_debut: String(fd.get("date_debut")),
                    date_fin: String(fd.get("date_fin")),
                  });
                  e.currentTarget.reset();
                }}
              >
                <div>
                  <Label>Libellé</Label>
                  <Input name="label" required placeholder="Haute saison 2026" />
                </div>
                <div>
                  <Label>Début</Label>
                  <Input name="date_debut" type="date" required />
                </div>
                <div>
                  <Label>Fin</Label>
                  <Input name="date_fin" type="date" required />
                </div>
                <Button type="submit" disabled={seasonMutation.isPending}>
                  Ajouter
                </Button>
              </form>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Libellé</TableHead>
                  <TableHead>Début</TableHead>
                  <TableHead>Fin</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {seasonsLoading ? (
                  <TableRowsSkeleton rows={3} columns={5} />
                ) : !seasons?.length ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-0">
                      <EmptyState className="border-none" title="Aucune saison" description="Créez votre première saison ci-dessus." />
                    </TableCell>
                  </TableRow>
                ) : (
                  seasons.map((s) => (
                    <TableRow key={s.id}>
                      <TableCell>{s.label}</TableCell>
                      <TableCell>{s.date_debut}</TableCell>
                      <TableCell>{s.date_fin}</TableCell>
                      <TableCell>
                        <ActiveBadge active={s.is_active} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={toggleSeasonMutation.isPending}
                          onClick={() => toggleSeasonMutation.mutate({ id: s.id, is_active: !s.is_active })}
                        >
                          {s.is_active ? "Désactiver" : "Activer"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="rate-grid" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Nouveau tarif</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  rateGridMutation.mutate({
                    room_category: String(fd.get("room_category")),
                    season_id: String(fd.get("season_id")),
                    regime: String(fd.get("regime")),
                    prix_ht: Number(fd.get("prix_ht")),
                    prix_ttc: Number(fd.get("prix_ttc")),
                    tva_rate: 10,
                  });
                  e.currentTarget.reset();
                }}
              >
                <div>
                  <Label>Catégorie</Label>
                  <Select name="room_category" defaultValue={ROOM_CATEGORIES[0]}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROOM_CATEGORIES.map((c) => (
                        <SelectItem key={c} value={c}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Saison</Label>
                  <Select name="season_id">
                    <SelectTrigger>
                      <SelectValue placeholder="Choisir" />
                    </SelectTrigger>
                    <SelectContent>
                      {(seasons ?? []).map((s: Season) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Régime</Label>
                  <Select name="regime" defaultValue="BB">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BB">BB</SelectItem>
                      <SelectItem value="DP">DP</SelectItem>
                      <SelectItem value="PC">PC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Prix HT / nuit</Label>
                  <Input name="prix_ht" type="number" step="0.01" min={0.01} required />
                </div>
                <div>
                  <Label>Prix TTC / nuit</Label>
                  <Input name="prix_ttc" type="number" step="0.01" min={0.01} required />
                </div>
                <Button type="submit" disabled={rateGridMutation.isPending || !seasons?.length}>
                  Ajouter
                </Button>
              </form>
              {!seasons?.length && (
                <p className="mt-2 text-xs text-muted-foreground">Créez d&apos;abord une saison.</p>
              )}
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Catégorie</TableHead>
                  <TableHead>Régime</TableHead>
                  <TableHead>Prix HT</TableHead>
                  <TableHead>Prix TTC</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rateGridLoading ? (
                  <TableRowsSkeleton rows={3} columns={5} />
                ) : !rateGrid?.length ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-0">
                      <EmptyState className="border-none" title="Aucun tarif" description="Ajoutez une entrée de grille tarifaire ci-dessus." />
                    </TableCell>
                  </TableRow>
                ) : (
                  rateGrid.map((r) =>
                    editingRate?.id === r.id ? (
                      <InlineEditRow key={r.id} colSpan={5}>
                        <form
                          className="flex flex-wrap items-end gap-2"
                          onSubmit={(e) => {
                            e.preventDefault();
                            const fd = new FormData(e.currentTarget);
                            editRateMutation.mutate({
                              id: r.id,
                              prix_ht: Number(fd.get("prix_ht")),
                              prix_ttc: Number(fd.get("prix_ttc")),
                            });
                          }}
                        >
                          <Input name="prix_ht" type="number" step="0.01" defaultValue={r.prix_ht} className="w-28" />
                          <Input name="prix_ttc" type="number" step="0.01" defaultValue={r.prix_ttc} className="w-28" />
                          <Button type="submit" size="sm" disabled={editRateMutation.isPending}>
                            Enregistrer
                          </Button>
                          <Button type="button" size="sm" variant="ghost" onClick={() => setEditingRate(null)}>
                            Annuler
                          </Button>
                        </form>
                      </InlineEditRow>
                    ) : (
                      <TableRow key={r.id}>
                        <TableCell>{r.room_category}</TableCell>
                        <TableCell>{r.regime}</TableCell>
                        <TableCell>{r.prix_ht.toFixed(2)}</TableCell>
                        <TableCell>{r.prix_ttc.toFixed(2)}</TableCell>
                        <TableCell className="text-right">
                          <Button size="sm" variant="ghost" onClick={() => setEditingRate(r)}>
                            Modifier
                          </Button>
                        </TableCell>
                      </TableRow>
                    )
                  )
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="taxes" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Nouvelle taxe</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  const type = String(fd.get("type"));
                  taxMutation.mutate({
                    type,
                    taux_ou_montant: Number(fd.get("taux_ou_montant")),
                    mode_calcul: type === "TS" || type === "TPT" ? "FIXED_PER_PAX" : "PERCENTAGE",
                  });
                  e.currentTarget.reset();
                }}
              >
                <div>
                  <Label>Type</Label>
                  <Select name="type" defaultValue="TS">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="TVA_HEBERGEMENT">TVA Hébergement</SelectItem>
                      <SelectItem value="TVA_AUTRE">TVA Autre</SelectItem>
                      <SelectItem value="TS">Taxe de séjour (TS)</SelectItem>
                      <SelectItem value="TPT">Taxe promotion touristique (TPT)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Taux / montant</Label>
                  <Input name="taux_ou_montant" type="number" step="0.01" required />
                </div>
                <Button type="submit" disabled={taxMutation.isPending}>
                  Ajouter
                </Button>
              </form>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Type</TableHead>
                  <TableHead>Mode</TableHead>
                  <TableHead>Taux / montant</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {taxesLoading ? (
                  <TableRowsSkeleton rows={3} columns={5} />
                ) : !taxes?.length ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-0">
                      <EmptyState className="border-none" title="Aucune taxe" description="Ajoutez une taxe ci-dessus." />
                    </TableCell>
                  </TableRow>
                ) : (
                  taxes.map((t) => (
                    <TableRow key={t.id}>
                      <TableCell>{t.type}</TableCell>
                      <TableCell>{t.mode_calcul}</TableCell>
                      <TableCell>{t.taux_ou_montant}</TableCell>
                      <TableCell>
                        <ActiveBadge active={t.is_active} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={toggleTaxMutation.isPending}
                          onClick={() => toggleTaxMutation.mutate({ id: t.id, is_active: !t.is_active })}
                        >
                          {t.is_active ? "Désactiver" : "Activer"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="extras" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Nouvel extra</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  extraMutation.mutate({
                    categorie: String(fd.get("categorie")),
                    libelle: String(fd.get("libelle")),
                    prix_ht: Number(fd.get("prix_ht")),
                    tva_rate: 20,
                  });
                  e.currentTarget.reset();
                }}
              >
                <div>
                  <Label>Catégorie</Label>
                  <Select name="categorie" defaultValue="SPA">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {["Restaurant", "Bar", "SPA", "Activités", "Autre"].map((c) => (
                        <SelectItem key={c} value={c}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Libellé</Label>
                  <Input name="libelle" required />
                </div>
                <div>
                  <Label>Prix HT</Label>
                  <Input name="prix_ht" type="number" step="0.01" min={0.01} required />
                </div>
                <Button type="submit" disabled={extraMutation.isPending}>
                  Ajouter
                </Button>
              </form>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Catégorie</TableHead>
                  <TableHead>Libellé</TableHead>
                  <TableHead>Prix HT</TableHead>
                  <TableHead>Prix TTC</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {extrasLoading ? (
                  <TableRowsSkeleton rows={3} columns={5} />
                ) : !extras?.length ? (
                  <TableRow>
                    <TableCell colSpan={5} className="p-0">
                      <EmptyState className="border-none" title="Aucun extra" description="Ajoutez un extra au catalogue ci-dessus." />
                    </TableCell>
                  </TableRow>
                ) : (
                  extras.map((e) => (
                    <TableRow key={e.id}>
                      <TableCell>{e.categorie}</TableCell>
                      <TableCell>{e.libelle}</TableCell>
                      <TableCell>{e.prix_ht.toFixed(2)}</TableCell>
                      <TableCell>{e.prix_ttc.toFixed(2)}</TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={toggleExtraMutation.isPending}
                          onClick={() => toggleExtraMutation.mutate({ id: e.id, is_active: !e.is_active })}
                        >
                          {e.is_active ? "Désactiver" : "Activer"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="partner-rates" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Nouveau tarif négocié (Workflow B)</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  partnerRateMutation.mutate({
                    partner_id: String(fd.get("partner_id")),
                    season_id: String(fd.get("season_id")),
                    room_category: String(fd.get("room_category")),
                    regime: String(fd.get("regime")),
                    tarif_negocie: Number(fd.get("tarif_negocie")),
                    commission_pct: Number(fd.get("commission_pct") || 0),
                  });
                  e.currentTarget.reset();
                }}
              >
                <div>
                  <Label>Partenaire</Label>
                  <Select name="partner_id">
                    <SelectTrigger>
                      <SelectValue placeholder="Choisir" />
                    </SelectTrigger>
                    <SelectContent>
                      {(partners ?? []).map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.nom}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Saison</Label>
                  <Select name="season_id">
                    <SelectTrigger>
                      <SelectValue placeholder="Choisir" />
                    </SelectTrigger>
                    <SelectContent>
                      {(seasons ?? []).map((s) => (
                        <SelectItem key={s.id} value={s.id}>
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Catégorie</Label>
                  <Select name="room_category" defaultValue={ROOM_CATEGORIES[0]}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROOM_CATEGORIES.map((c) => (
                        <SelectItem key={c} value={c}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Régime</Label>
                  <Select name="regime" defaultValue="BB">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BB">BB</SelectItem>
                      <SelectItem value="DP">DP</SelectItem>
                      <SelectItem value="PC">PC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Tarif négocié / nuit</Label>
                  <Input name="tarif_negocie" type="number" step="0.01" min={0.01} required />
                </div>
                <div>
                  <Label>Commission (%)</Label>
                  <Input name="commission_pct" type="number" step="0.01" min={0} defaultValue={0} />
                </div>
                <Button
                  type="submit"
                  disabled={partnerRateMutation.isPending || !partners?.length || !seasons?.length}
                >
                  Ajouter
                </Button>
              </form>
              {!partners?.length && (
                <p className="mt-2 text-xs text-muted-foreground">
                  Créez d&apos;abord un partenaire (page Partenaires).
                </p>
              )}
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Partenaire</TableHead>
                  <TableHead>Saison</TableHead>
                  <TableHead>Catégorie</TableHead>
                  <TableHead>Régime</TableHead>
                  <TableHead>Tarif négocié</TableHead>
                  <TableHead>Commission</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {partnerRatesLoading ? (
                  <TableRowsSkeleton rows={3} columns={6} />
                ) : !partnerRates?.length ? (
                  <TableRow>
                    <TableCell colSpan={6} className="p-0">
                      <EmptyState className="border-none" title="Aucun tarif négocié" description="Ajoutez un tarif négocié ci-dessus." />
                    </TableCell>
                  </TableRow>
                ) : (
                  partnerRates.map((r) => (
                    <TableRow key={r.id}>
                      <TableCell>{partnerLabel(r.partner_id)}</TableCell>
                      <TableCell>{seasonLabel(r.season_id)}</TableCell>
                      <TableCell>{r.room_category}</TableCell>
                      <TableCell>{r.regime}</TableCell>
                      <TableCell>{r.tarif_negocie.toFixed(2)}</TableCell>
                      <TableCell>{r.commission_pct}%</TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="packages" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Nouveau forfait</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-3"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  let ventilation: Record<string, number> = {};
                  try {
                    ventilation = JSON.parse(String(fd.get("ventilation") || "{}"));
                  } catch {
                    toast.error("Ventilation invalide — attendu un JSON, ex: {\"HEB\": 800, \"PDJ\": 100}");
                    return;
                  }
                  packageMutation.mutate({
                    label: String(fd.get("label")),
                    description: String(fd.get("description") || "") || undefined,
                    prix_global_ttc: Number(fd.get("prix_global_ttc")),
                    ventilation,
                  });
                  e.currentTarget.reset();
                }}
              >
                <div>
                  <Label>Libellé</Label>
                  <Input name="label" required placeholder="Séjour Romance 3 nuits" />
                </div>
                <div>
                  <Label>Prix global TTC</Label>
                  <Input name="prix_global_ttc" type="number" step="0.01" min={0.01} required />
                </div>
                <Button type="submit" disabled={packageMutation.isPending}>
                  Créer
                </Button>
                <div className="sm:col-span-3">
                  <Label>Ventilation comptable (JSON poste→montant)</Label>
                  <Input name="ventilation" placeholder='{"HEB": 800, "SPA": 200}' />
                </div>
                <div className="sm:col-span-3">
                  <Label>Description</Label>
                  <Input name="description" />
                </div>
              </form>
            </CardContent>
          </Card>
          <Card className="shadow-card">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Libellé</TableHead>
                  <TableHead>Prix TTC</TableHead>
                  <TableHead>Statut</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {packagesLoading ? (
                  <TableRowsSkeleton rows={3} columns={4} />
                ) : !packages?.length ? (
                  <TableRow>
                    <TableCell colSpan={4} className="p-0">
                      <EmptyState className="border-none" title="Aucun forfait" description="Créez votre premier forfait ci-dessus." />
                    </TableCell>
                  </TableRow>
                ) : (
                  packages.map((p) => (
                    <TableRow key={p.id}>
                      <TableCell>{p.label}</TableCell>
                      <TableCell>{p.prix_global_ttc.toFixed(2)}</TableCell>
                      <TableCell>
                        <ActiveBadge active={p.is_active} />
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={togglePackageMutation.isPending}
                          onClick={() => togglePackageMutation.mutate({ id: p.id, is_active: !p.is_active })}
                        >
                          {p.is_active ? "Désactiver" : "Activer"}
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>

        <TabsContent value="calculator" className="space-y-4">
          <Card className="shadow-card">
            <CardHeader>
              <CardTitle>Calculateur de tarif (Workflow A)</CardTitle>
            </CardHeader>
            <CardContent>
              <form
                className="grid grid-cols-1 items-end gap-3 sm:grid-cols-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  const fd = new FormData(e.currentTarget);
                  calcMutation.mutate({
                    room_category: String(fd.get("room_category")),
                    regime: String(fd.get("regime")),
                    date_from: String(fd.get("date_from")),
                    date_to: String(fd.get("date_to")),
                  });
                }}
              >
                <div>
                  <Label>Catégorie</Label>
                  <Select name="room_category" defaultValue={ROOM_CATEGORIES[0]}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {ROOM_CATEGORIES.map((c) => (
                        <SelectItem key={c} value={c}>
                          {c}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Régime</Label>
                  <Select name="regime" defaultValue="BB">
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="BB">BB</SelectItem>
                      <SelectItem value="DP">DP</SelectItem>
                      <SelectItem value="PC">PC</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Arrivée</Label>
                  <Input name="date_from" type="date" required />
                </div>
                <div>
                  <Label>Départ</Label>
                  <Input name="date_to" type="date" required />
                </div>
                <div className="sm:col-span-4">
                  <Button type="submit" disabled={calcMutation.isPending}>
                    Calculer
                  </Button>
                </div>
              </form>

              {calcResult && (
                <div className="mt-4 space-y-2">
                  <p className="font-display text-lg font-semibold text-foreground">Total TTC : {calcResult.total_ttc.toFixed(2)} MAD</p>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Date</TableHead>
                        <TableHead>Prix TTC</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {calcResult.nights.map((n) => (
                        <TableRow key={n.date}>
                          <TableCell>{n.date}</TableCell>
                          <TableCell>{n.prix_ttc.toFixed(2)}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
