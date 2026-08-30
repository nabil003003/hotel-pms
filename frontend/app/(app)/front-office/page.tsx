"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
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
import { CardSkeleton } from "@/components/loading-state";
import { PageHeader } from "@/components/page-header";
import { StatTile } from "@/components/stat-tile";
import {
  addCharge,
  addPayment,
  checkIn,
  checkOut,
  fetchDailyCaDetail,
  fetchDailyCredits,
  fetchDailyDebits,
  fetchDailyEncashments,
  fetchDebtors,
  fetchDepartures,
  fetchDiscrepancy,
  fetchFoliosForBooking,
} from "@/lib/api-clients/front-office";
import { fetchRooms } from "@/lib/api-clients/establishment";
import { fetchBusinessDate } from "@/lib/api-clients/night-audit";
import { fetchExtras } from "@/lib/api-clients/pricing";
import { fetchBookings, fetchBookingsByCheckInDate, fetchCustomers, type Booking } from "@/lib/api-clients/reservation";
import { useSessionStore } from "@/store/session-store";

const POSTES = ["HEB", "PDJ", "RES", "BAR", "SPA", "ACT", "TS", "TPT", "REM", "HAM", "TRF", "DIN", "EXC"];

const POSTE_LABELS: Record<string, string> = {
  HEB: "Hébergement",
  PDJ: "Petit-déjeuner",
  RES: "Restaurant",
  BAR: "Bar",
  SPA: "Spa",
  ACT: "Activités",
  TS: "Taxe de séjour",
  TPT: "Taxe promotion touristique",
  REM: "Remise",
  HAM: "Hammam",
  TRF: "Transfert",
  DIN: "Dîner",
  EXC: "Excursion",
};
const PAYMENT_MODES = ["CB", "ESP", "CHQ", "Virement", "Débiteur"];

const PAYMENT_MODE_LABELS: Record<string, string> = {
  CB: "Carte bancaire",
  ESP: "Espèces",
  CHQ: "Chèque",
  Virement: "Virement",
  Débiteur: "Débiteur (facturé à l'agence)",
};

export default function FrontOfficePage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour accéder au front office." />;
  }

  return <FrontOfficeContent establishmentId={establishmentId} />;
}

function FrontOfficeContent({ establishmentId }: { establishmentId: string }) {
  // La date métier (night-audit) peut être en avance sur la date calendaire du
  // navigateur dès qu'une clôture a eu lieu : "Arrivées du jour" et les
  // rapports doivent se baser sur elle, pas sur `new Date()`, sous peine de
  // filtrer sur une journée déjà clôturée/verrouillée côté back-end.
  const { data: businessDateData } = useQuery({
    queryKey: ["business-date", establishmentId],
    queryFn: () => fetchBusinessDate(establishmentId),
    enabled: Boolean(establishmentId),
  });

  if (!businessDateData) {
    return <CardSkeleton className="h-64" />;
  }

  const businessDate = businessDateData.business_date;

  return (
    <div className="space-y-4">
      <PageHeader title="Front Office" description="Arrivées, séjours en cours, folios et rapports journaliers" />

      <Tabs defaultValue="operations" className="space-y-4">
        <TabsList>
          <TabsTrigger value="operations">Opérations</TabsTrigger>
          <TabsTrigger value="reports">Rapports</TabsTrigger>
        </TabsList>
        <TabsContent value="operations">
          <OperationsTab establishmentId={establishmentId} businessDate={businessDate} />
        </TabsContent>
        <TabsContent value="reports">
          <ReportsTab establishmentId={establishmentId} businessDate={businessDate} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function OperationsTab({ establishmentId, businessDate }: { establishmentId: string; businessDate: string }) {
  const queryClient = useQueryClient();
  const [selectedBookingId, setSelectedBookingId] = useState<string | null>(null);
  const [useCatalog, setUseCatalog] = useState(false);

  const { data: arrivals } = useQuery({
    queryKey: ["bookings", establishmentId, "arrivals", businessDate],
    queryFn: async () => {
      const confirmed = await fetchBookingsByCheckInDate(establishmentId, businessDate, "status_confirmed");
      const voucher = await fetchBookingsByCheckInDate(establishmentId, businessDate, "status_voucher");
      return [...confirmed, ...voucher];
    },
    enabled: Boolean(establishmentId),
  });

  const { data: inHouse } = useQuery({
    queryKey: ["bookings", establishmentId, "in-house"],
    queryFn: () => fetchBookings(establishmentId, "2000-01-01", "2100-01-01", "status_checked_in"),
    enabled: Boolean(establishmentId),
  });

  const { data: folios } = useQuery({
    queryKey: ["folios", selectedBookingId],
    queryFn: () => fetchFoliosForBooking(selectedBookingId as string),
    enabled: Boolean(selectedBookingId),
  });

  const { data: extras } = useQuery({
    queryKey: ["extras", establishmentId],
    queryFn: () => fetchExtras(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const { data: customers } = useQuery({
    queryKey: ["customers", establishmentId],
    queryFn: () => fetchCustomers(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const { data: rooms } = useQuery({
    queryKey: ["establishment-rooms", establishmentId],
    queryFn: () => fetchRooms(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const customersById = useMemo(
    () => new Map((customers ?? []).map((c) => [c.id, c])),
    [customers]
  );
  const roomsById = useMemo(() => new Map((rooms ?? []).map((r) => [r.id, r])), [rooms]);

  const checkInMutation = useMutation({
    mutationFn: (bookingId: string) => checkIn(establishmentId, bookingId),
    onSuccess: (_, bookingId) => {
      queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      setSelectedBookingId(bookingId);
      toast.success("Check-in effectué");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const checkOutMutation = useMutation({
    mutationFn: (bookingId: string) => checkOut(establishmentId, bookingId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      queryClient.invalidateQueries({ queryKey: ["folios", selectedBookingId] });
      toast.success("Check-out effectué");
      setSelectedBookingId(null);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const chargeMutation = useMutation({
    mutationFn: ({ folioId, ...input }: { folioId: string } & Parameters<typeof addCharge>[1]) =>
      addCharge(folioId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folios", selectedBookingId] });
      toast.success("Charge ajoutée");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const paymentMutation = useMutation({
    mutationFn: ({ folioId, mode, montant }: { folioId: string; mode: string; montant: number }) =>
      addPayment(folioId, { mode, montant }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["folios", selectedBookingId] });
      toast.success("Paiement enregistré");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  function handleAddCharge(e: React.FormEvent<HTMLFormElement>, folioId: string) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const catalogItemId = String(fd.get("catalog_item_id") || "");
    chargeMutation.mutate({
      folioId,
      poste_comptable: String(fd.get("poste_comptable")),
      libelle: String(fd.get("libelle")),
      quantity: Number(fd.get("quantity") || 1),
      unit_price_ht: catalogItemId ? undefined : Number(fd.get("unit_price_ht")),
      catalog_item_id: catalogItemId || undefined,
    });
    e.currentTarget.reset();
    setUseCatalog(false);
  }

  function handleAddPayment(e: React.FormEvent<HTMLFormElement>, folioId: string) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    paymentMutation.mutate({
      folioId,
      mode: String(fd.get("mode")),
      montant: Number(fd.get("montant")),
    });
    e.currentTarget.reset();
  }

  const folioA = (folios ?? []).find((f) => f.type === "A" && f.status === "open");

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <div className="space-y-6 lg:col-span-1">
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Arrivées du jour</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(arrivals ?? []).length === 0 ? (
              <EmptyState className="border-none py-6" title="Aucune arrivée" description="Aucune arrivée prévue aujourd'hui." />
            ) : (
              (arrivals ?? []).map((booking: Booking) => {
                const customer = customersById.get(booking.customer_id);
                const room = roomsById.get(booking.room_id);
                return (
                <div key={booking.id} className="flex items-center justify-between rounded-lg border border-border p-2">
                  <div className="text-sm">
                    <p className="font-medium text-foreground">
                      {customer ? `${customer.first_name} ${customer.last_name}` : "Client inconnu"}
                    </p>
                    <p className="text-muted-foreground">
                      {room ? `${room.numero} — ${room.categorie}` : "Chambre inconnue"} · {booking.adults} adulte(s)
                    </p>
                  </div>
                  <Button
                    size="sm"
                    disabled={checkInMutation.isPending}
                    onClick={() => checkInMutation.mutate(booking.id)}
                  >
                    Check-in
                  </Button>
                </div>
                );
              })
            )}
          </CardContent>
        </Card>

        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>En séjour</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {(inHouse ?? []).length === 0 ? (
              <EmptyState className="border-none py-6" title="Aucun séjour" description="Aucun séjour en cours." />
            ) : (
              (inHouse ?? []).map((booking: Booking) => {
                const customer = customersById.get(booking.customer_id);
                const room = roomsById.get(booking.room_id);
                return (
                <button
                  key={booking.id}
                  onClick={() => setSelectedBookingId(booking.id)}
                  className={`flex w-full items-center justify-between rounded-lg border p-2 text-left text-sm transition-colors hover:bg-muted ${
                    selectedBookingId === booking.id ? "border-primary bg-primary/5" : "border-border"
                  }`}
                >
                  <span className="font-medium text-foreground">
                    {customer ? `${customer.first_name} ${customer.last_name}` : "Client inconnu"}
                    {room ? ` — ${room.numero}` : ""}
                  </span>
                  <Badge variant="outline">{booking.check_out_date}</Badge>
                </button>
                );
              })
            )}
          </CardContent>
        </Card>
      </div>

      <div className="space-y-6 lg:col-span-2">
        {!selectedBookingId ? (
          <EmptyState title="Aucun séjour sélectionné" description="Sélectionnez un séjour en cours à gauche pour voir son folio." />
        ) : !folioA ? (
          <EmptyState title="Chargement du folio" description="Le folio de ce séjour est en cours de chargement." />
        ) : (
          <>
            <Card className="shadow-card">
              <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-3">
                <CardTitle>Folio A — solde {folioA.balance.toFixed(2)} MAD</CardTitle>
                <Button
                  disabled={folioA.balance !== 0 || checkOutMutation.isPending}
                  onClick={() => checkOutMutation.mutate(selectedBookingId)}
                >
                  Check-out
                </Button>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <p>Total charges : {folioA.total_charges.toFixed(2)} MAD</p>
                  <p>Total encaissé : {folioA.total_payments.toFixed(2)} MAD</p>
                </div>
                {folioA.balance !== 0 && (
                  <p className="text-xs text-status-warning">
                    Le solde doit être à 0 exactement pour autoriser le check-out.
                  </p>
                )}
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Ajouter une charge (Workflow E)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <label className="flex items-center gap-2 text-sm">
                  <input type="checkbox" checked={useCatalog} onChange={(e) => setUseCatalog(e.target.checked)} className="accent-primary" />
                  Depuis le catalogue extras (prix catalogue fait foi)
                </label>
                <form
                  onSubmit={(e) => handleAddCharge(e, folioA.id)}
                  className="grid grid-cols-2 items-end gap-2 sm:grid-cols-4"
                >
                  <div>
                    <Label>Poste</Label>
                    <Select name="poste_comptable" defaultValue="RES">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {POSTES.map((p) => (
                          <SelectItem key={p} value={p}>
                            {POSTE_LABELS[p]} ({p})
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  {useCatalog ? (
                    <div className="col-span-2">
                      <Label>Article catalogue</Label>
                      <Select name="catalog_item_id">
                        <SelectTrigger>
                          <SelectValue placeholder="Choisir" />
                        </SelectTrigger>
                        <SelectContent>
                          {(extras ?? []).map((item) => (
                            <SelectItem key={item.id} value={item.id}>
                              {item.libelle} — {item.prix_ht.toFixed(2)} HT
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  ) : (
                    <div className="col-span-2">
                      <Label htmlFor="libelle">Libellé</Label>
                      <Input id="libelle" name="libelle" required={!useCatalog} />
                    </div>
                  )}
                  <div>
                    <Label htmlFor="quantity">Qté</Label>
                    <Input id="quantity" name="quantity" type="number" min={1} defaultValue={1} />
                  </div>
                  {!useCatalog && (
                    <div>
                      <Label htmlFor="unit_price_ht">Prix unitaire HT</Label>
                      <Input id="unit_price_ht" name="unit_price_ht" type="number" step="0.01" min={0} required />
                    </div>
                  )}
                  {useCatalog && <input type="hidden" name="libelle" value="Extra catalogue" />}
                  <Button type="submit" disabled={chargeMutation.isPending}>
                    Ajouter
                  </Button>
                </form>
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Encaisser un paiement</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  key={folioA.version}
                  onSubmit={(e) => handleAddPayment(e, folioA.id)}
                  className="grid grid-cols-2 items-end gap-2 sm:grid-cols-4"
                >
                  <div>
                    <Label>Mode</Label>
                    <Select name="mode" defaultValue="CB">
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {PAYMENT_MODES.map((m) => (
                          <SelectItem key={m} value={m}>
                            {PAYMENT_MODE_LABELS[m]}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="montant">Montant</Label>
                    <Input
                      id="montant"
                      name="montant"
                      type="number"
                      step="0.01"
                      min={0.01}
                      defaultValue={folioA.balance > 0 ? folioA.balance.toFixed(2) : undefined}
                      required
                    />
                  </div>
                  <Button type="submit" disabled={paymentMutation.isPending}>
                    Encaisser
                  </Button>
                </form>
              </CardContent>
            </Card>

            {(folios ?? [])
              .filter((f) => f.type === "B")
              .map((folioB) => (
                <Card key={folioB.id} className="shadow-card">
                  <CardHeader>
                    <CardTitle>Folio B (tiers) — solde {folioB.balance.toFixed(2)} MAD</CardTitle>
                  </CardHeader>
                </Card>
              ))}
          </>
        )}
      </div>
    </div>
  );
}

function ReportsTab({ establishmentId, businessDate }: { establishmentId: string; businessDate: string }) {
  const [date, setDate] = useState(businessDate);

  const { data: debits } = useQuery({
    queryKey: ["report-debits", establishmentId, date],
    queryFn: () => fetchDailyDebits(establishmentId, date),
  });
  const { data: credits } = useQuery({
    queryKey: ["report-credits", establishmentId, date],
    queryFn: () => fetchDailyCredits(establishmentId, date),
  });
  const { data: caDetail } = useQuery({
    queryKey: ["report-ca-detail", establishmentId, date],
    queryFn: () => fetchDailyCaDetail(establishmentId, date),
  });
  const { data: encashments } = useQuery({
    queryKey: ["report-encashments", establishmentId, date],
    queryFn: () => fetchDailyEncashments(establishmentId, date),
  });
  const { data: debtors } = useQuery({
    queryKey: ["report-debtors", establishmentId],
    queryFn: () => fetchDebtors(establishmentId),
  });
  const { data: departures } = useQuery({
    queryKey: ["report-departures", establishmentId, date],
    queryFn: () => fetchDepartures(establishmentId, date),
  });
  const { data: discrepancy } = useQuery({
    queryKey: ["report-discrepancy", establishmentId, date],
    queryFn: () => fetchDiscrepancy(establishmentId, date),
  });

  return (
    <div className="space-y-6">
      <div>
        <Label>Date métier</Label>
        <Input type="date" value={date} onChange={(e) => setDate(e.target.value)} className="w-48" />
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <StatTile label="Total débits" value={debits?.total_debits.toFixed(2) ?? "—"} />
        <StatTile label="Total crédits" value={credits?.total_credits.toFixed(2) ?? "—"} />
        <StatTile
          label="Écart"
          value={debits && credits ? (debits.total_debits - credits.total_credits).toFixed(2) : "—"}
        />
      </div>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>CA détaillé par poste</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Poste</TableHead>
              <TableHead>HT</TableHead>
              <TableHead>TVA</TableHead>
              <TableHead>TTC</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(caDetail?.lines ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={4} className="p-0">
                  <EmptyState className="border-none" title="Aucune donnée" description="Aucune ligne de CA pour cette date." />
                </TableCell>
              </TableRow>
            ) : (
              caDetail!.lines.map((l) => (
                <TableRow key={l.poste_comptable}>
                  <TableCell>{POSTE_LABELS[l.poste_comptable] ?? l.poste_comptable}</TableCell>
                  <TableCell>{l.montant_ht.toFixed(2)}</TableCell>
                  <TableCell>{l.tva_amount.toFixed(2)}</TableCell>
                  <TableCell>{l.montant_ttc.toFixed(2)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Encaissements par mode</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Mode</TableHead>
              <TableHead>Total</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(encashments?.lines ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="p-0">
                  <EmptyState className="border-none" title="Aucune donnée" description="Aucun encaissement pour cette date." />
                </TableCell>
              </TableRow>
            ) : (
              encashments!.lines.map((l) => (
                <TableRow key={l.mode}>
                  <TableCell>{PAYMENT_MODE_LABELS[l.mode] ?? l.mode}</TableCell>
                  <TableCell>{l.total.toFixed(2)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Départs attendus J+1</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Réservation</TableHead>
              <TableHead>Solde</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(departures?.departures ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="p-0">
                  <EmptyState className="border-none" title="Aucun départ" description="Aucun départ prévu." />
                </TableCell>
              </TableRow>
            ) : (
              departures!.departures.map((d) => (
                <TableRow key={d.folio_id}>
                  <TableCell>{d.booking_id.slice(0, 8)}…</TableCell>
                  <TableCell>{d.balance.toFixed(2)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Soldes débiteurs (Folio B ouverts)</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Réservation</TableHead>
              <TableHead>Solde</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(debtors ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={2} className="p-0">
                  <EmptyState className="border-none" title="Aucun débiteur" description="Aucun solde débiteur ouvert." />
                </TableCell>
              </TableRow>
            ) : (
              debtors!.map((d) => (
                <TableRow key={d.folio_id}>
                  <TableCell>{d.booking_id.slice(0, 8)}…</TableCell>
                  <TableCell>{d.balance.toFixed(2)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Folios en écart (pré-audit)</CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Réservation</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Solde</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {(discrepancy ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={3} className="p-0">
                  <EmptyState className="border-none" title="Journée équilibrée" description="Aucun écart détecté." />
                </TableCell>
              </TableRow>
            ) : (
              discrepancy!.map((d) => (
                <TableRow key={d.folio_id}>
                  <TableCell>{d.booking_id.slice(0, 8)}…</TableCell>
                  <TableCell>{d.type}</TableCell>
                  <TableCell>{d.balance.toFixed(2)}</TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>
    </div>
  );
}
