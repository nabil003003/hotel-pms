"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { toast } from "sonner";
import { CheckCircle, Info, WarningCircle } from "@phosphor-icons/react";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
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
import { CardSkeleton, TableRowsSkeleton } from "@/components/loading-state";
import { PageHeader } from "@/components/page-header";
import { elevate } from "@/lib/api-clients/auth-gateway";
import { fetchRooms, type Room } from "@/lib/api-clients/establishment";
import { fetchBusinessDate } from "@/lib/api-clients/night-audit";
import { fetchPartners } from "@/lib/api-clients/partner";
import { addDaysIso } from "@/lib/date-utils";
import {
  cancelBooking,
  checkAvailability,
  createBooking,
  createCustomer,
  createMarketSegment,
  fetchBookings,
  fetchCustomers,
  fetchMarketSegments,
  shiftRoom,
  updateBookingStatus,
  updateCustomer,
  updateMarketSegment,
  type Booking,
  type BookingCreateInput,
  type Customer,
} from "@/lib/api-clients/reservation";
import { useSessionStore } from "@/store/session-store";
import { usePlanningWebSocket } from "@/hooks/use-planning-websocket";
import { PlanningGrid, type ShiftBookingParams } from "@/components/planning-grid/planning-grid";

const ROOM_CATEGORIES = [
  "Chambre Standard",
  "Chambre Deluxe",
  "Suite Junior",
  "Suite Royale",
  "Riad Entier",
];

// Le formulaire walk-in (Workflow A) n'expose que le segment de marché, pas
// le `source` réel de la réservation (reservation-service en dérive pourtant
// le statut auto-confirmé, `services.py:385` — `source.startswith("ota_")`) :
// on dérive donc `source` du segment choisi plutôt que de le figer sur
// "walk_in" quel que soit le segment sélectionné.
const SOURCE_BY_SEGMENT_CATEGORY: Record<string, string> = {
  DIRECT: "walk_in",
  OTA: "ota_booking",
  PARTENAIRES: "b2b_agency",
};

const STATUS_LABELS: Record<string, string> = {
  status_option: "Option",
  status_confirmed: "Confirmée",
  status_voucher: "Voucher",
  status_checked_in: "En séjour",
  status_checked_out: "Terminée",
  status_no_show: "No-show",
  status_cancelled: "Annulée",
};

const ALL_STATUSES = Object.keys(STATUS_LABELS);
const CANCELLABLE = new Set(["status_option", "status_confirmed", "status_voucher"]);
const ACTIVE_FOR_SHIFT = new Set(["status_option", "status_confirmed", "status_voucher", "status_checked_in"]);

export default function ReservationsPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour gérer ses réservations." />;
  }

  return <ReservationsContent establishmentId={establishmentId} />;
}

function ReservationsContent({ establishmentId }: { establishmentId: string }) {
  // Idem front-office : la date métier peut avoir avancé au-delà de la date
  // calendaire du navigateur après une clôture night-audit. Fixer les
  // valeurs par défaut sur `new Date()` fait proposer une arrivée sur une
  // journée déjà verrouillée (rejetée par reservation-service).
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
      <PageHeader title="Réservations" description="Planning, disponibilité, segments de marché et clients" />

      <Tabs defaultValue="planning" className="space-y-4">
        <TabsList>
          <TabsTrigger value="planning">Planning</TabsTrigger>
          <TabsTrigger value="availability">Disponibilité</TabsTrigger>
          <TabsTrigger value="segments">Segments</TabsTrigger>
          <TabsTrigger value="customers">Clients</TabsTrigger>
        </TabsList>

        <TabsContent value="planning">
          <PlanningTab establishmentId={establishmentId} businessDate={businessDate} />
        </TabsContent>
        <TabsContent value="availability">
          <AvailabilityTab establishmentId={establishmentId} businessDate={businessDate} />
        </TabsContent>
        <TabsContent value="segments">
          <SegmentsTab establishmentId={establishmentId} />
        </TabsContent>
        <TabsContent value="customers">
          <CustomersTab establishmentId={establishmentId} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ------------------------------------------------------------- Planning ---

function PlanningTab({ establishmentId, businessDate }: { establishmentId: string; businessDate: string }) {
  const queryClient = useQueryClient();
  usePlanningWebSocket(establishmentId);

  const [fromDate, setFromDate] = useState(businessDate);
  const [toDate, setToDate] = useState(addDaysIso(businessDate, 14));
  const [viewMode, setViewMode] = useState<"grid" | "table">("table");
  const [createOpen, setCreateOpen] = useState(false);
  const [shiftTarget, setShiftTarget] = useState<Booking | null>(null);
  const [elevationToken, setElevationToken] = useState<string | null>(null);
  const [createSegmentId, setCreateSegmentId] = useState<string | undefined>(undefined);

  const { data: bookings, isLoading } = useQuery({
    queryKey: ["bookings", establishmentId, fromDate, toDate],
    queryFn: () => fetchBookings(establishmentId, fromDate, toDate),
    enabled: Boolean(establishmentId),
  });

  const { data: segments } = useQuery({
    queryKey: ["market-segments", establishmentId],
    queryFn: () => fetchMarketSegments(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const { data: rooms } = useQuery({
    queryKey: ["establishment-rooms", establishmentId],
    queryFn: () => fetchRooms(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const { data: customers } = useQuery({
    queryKey: ["customers", establishmentId],
    queryFn: () => fetchCustomers(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const { data: partners } = useQuery({
    queryKey: ["partners", establishmentId],
    queryFn: () => fetchPartners(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const customersById = useMemo(
    () => new Map((customers ?? []).map((c) => [c.id, c])),
    [customers]
  );
  const roomsById = useMemo(() => new Map((rooms ?? []).map((r) => [r.id, r])), [rooms]);

  const createSegmentCategory = (segments ?? []).find((s) => s.id === createSegmentId)?.category;
  const createRequiresPartner = createSegmentCategory === "PARTENAIRES";

  const createMutation = useMutation({
    mutationFn: createBooking,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      toast.success("Réservation créée");
      setCreateOpen(false);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const cancelMutation = useMutation({
    mutationFn: ({ id, reason }: { id: string; reason: string }) => cancelBooking(id, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      toast.success("Réservation annulée");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const statusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) => updateBookingStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      toast.success("Statut mis à jour");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const elevateMutation = useMutation({
    mutationFn: () => elevate(establishmentId),
    onSuccess: (result) => {
      setElevationToken(result.token);
      toast.success("Autorisation manager obtenue (valide temporairement)");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const shiftMutation = useMutation({
    mutationFn: ({ bookingId, input }: { bookingId: string; input: Parameters<typeof shiftRoom>[1] }) =>
      shiftRoom(bookingId, input),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["bookings", establishmentId] });
      toast.success(`Chambre changée — delta ${result.delta.toFixed(2)} MAD`);
      setShiftTarget(null);
      setElevationToken(null);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  function handleCreate(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const segmentId = String(fd.get("market_segment_id"));
    const segmentCategory = (segments ?? []).find((s) => s.id === segmentId)?.category ?? "DIRECT";
    const requiresPartner = segmentCategory === "PARTENAIRES";
    const partnerId = String(fd.get("partner_id") || "");
    if (requiresPartner && !partnerId) {
      toast.error("Choisissez un partenaire pour une réservation Agences & TO.");
      return;
    }
    const input: BookingCreateInput = {
      establishment_id: establishmentId,
      market_segment_id: segmentId,
      room_category: String(fd.get("room_category")),
      check_in_date: String(fd.get("check_in_date")),
      check_out_date: String(fd.get("check_out_date")),
      regime: String(fd.get("regime")),
      taxes_payment_mode: String(fd.get("taxes_payment_mode")),
      adults: Number(fd.get("adults")),
      children: Number(fd.get("children") || 0),
      customer: {
        first_name: String(fd.get("first_name")),
        last_name: String(fd.get("last_name")),
        email: String(fd.get("email") || "") || undefined,
        phone: String(fd.get("phone") || "") || undefined,
      },
      source: SOURCE_BY_SEGMENT_CATEGORY[segmentCategory] ?? "walk_in",
      deposit_paid: fd.get("deposit_paid") === "on",
      partner_id: requiresPartner ? partnerId : undefined,
    };
    createMutation.mutate(input);
  }

  const currentRoom = (rooms ?? []).find((r) => r.id === shiftTarget?.room_id);

  function handleShiftSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (!shiftTarget) return;
    const fd = new FormData(e.currentTarget);
    const newRoomId = String(fd.get("new_room_id") || "");
    if (!newRoomId) {
      toast.error("Veuillez choisir une nouvelle chambre.");
      return;
    }
    const newRoom = (rooms ?? []).find((r) => r.id === newRoomId);
    const sameCategory = Boolean(currentRoom && newRoom && currentRoom.categorie === newRoom.categorie);
    shiftMutation.mutate({
      bookingId: shiftTarget.id,
      input: {
        new_room_id: newRoomId,
        new_room_category: newRoom?.categorie,
        same_category: sameCategory,
        reason: String(fd.get("reason") || "") || undefined,
        elevation_token: sameCategory ? undefined : elevationToken ?? undefined,
      },
    });
  }

  function handleGridShift(params: ShiftBookingParams) {
    const origRoom = (rooms ?? []).find((r) => r.id === params.booking.room_id);
    const targetRoom = (rooms ?? []).find((r) => r.id === params.targetRoomId);
    const sameCategory = Boolean(origRoom && targetRoom && origRoom.categorie === targetRoom.categorie);

    if (!sameCategory && !elevationToken) {
      toast.error("Changement de catégorie nécessitant une élévation manager. Demandez l'autorisation via le dialogue de déplacement.");
      setShiftTarget(params.booking);
      return;
    }

    shiftMutation.mutate({
      bookingId: params.booking.id,
      input: {
        new_room_id: params.targetRoomId,
        new_room_category: targetRoom?.categorie,
        new_check_in_date: params.targetCheckInDate,
        new_check_out_date: params.targetCheckOutDate,
        same_category: sameCategory,
        reason: "Glisser-déposer sur la grille planning",
        elevation_token: sameCategory ? undefined : elevationToken ?? undefined,
      },
    });
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <Label>Du</Label>
            <Input type="date" value={fromDate} onChange={(e) => setFromDate(e.target.value)} />
          </div>
          <div>
            <Label>Au</Label>
            <Input type="date" value={toDate} onChange={(e) => setToDate(e.target.value)} />
          </div>

          <div className="flex items-center gap-1 rounded-lg border border-border bg-muted/40 p-1">
            <Button
              type="button"
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("grid")}
            >
              Vue Grille
            </Button>
            <Button
              type="button"
              variant={viewMode === "table" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("table")}
            >
              Vue Tableau
            </Button>
          </div>
        </div>

        <Dialog open={createOpen} onOpenChange={setCreateOpen}>
          <DialogTrigger asChild>
            <Button>Nouvelle réservation (walk-in)</Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl">
            <DialogHeader>
              <DialogTitle>Nouvelle réservation — Workflow A</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div className="sm:col-span-2">
                <Label>Segment de marché</Label>
                <Select
                  name="market_segment_id"
                  value={createSegmentId ?? segments?.[0]?.id}
                  onValueChange={setCreateSegmentId}
                >
                  <SelectTrigger className="w-full">
                    <SelectValue placeholder="Choisir" />
                  </SelectTrigger>
                  <SelectContent>
                    {(segments ?? []).map((s) => (
                      <SelectItem key={s.id} value={s.id}>
                        {s.label} ({s.category})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {createRequiresPartner && (
                <div className="sm:col-span-2">
                  <Label>Partenaire (agence / TO)</Label>
                  <Select name="partner_id" defaultValue={partners?.[0]?.id}>
                    <SelectTrigger className="w-full">
                      <SelectValue placeholder="Choisir un partenaire" />
                    </SelectTrigger>
                    <SelectContent>
                      {(partners ?? []).map((p) => (
                        <SelectItem key={p.id} value={p.id}>
                          {p.nom} ({p.type})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  {(partners ?? []).length === 0 && (
                    <p className="mt-1 text-xs text-status-warning">
                      Aucun partenaire actif pour cet établissement — créez-en un dans l&apos;onglet Partenaires avant de continuer.
                    </p>
                  )}
                </div>
              )}
              <div>
                <Label>Catégorie de chambre</Label>
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
                <Label htmlFor="check_in_date">Arrivée</Label>
                <Input id="check_in_date" name="check_in_date" type="date" required defaultValue={businessDate} />
              </div>
              <div>
                <Label htmlFor="check_out_date">Départ</Label>
                <Input id="check_out_date" name="check_out_date" type="date" required defaultValue={addDaysIso(businessDate, 1)} />
              </div>
              <div>
                <Label>Régime</Label>
                <Select name="regime" defaultValue="BB">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="BB">BB (Petit-déjeuner)</SelectItem>
                    <SelectItem value="DP">DP (Demi-pension)</SelectItem>
                    <SelectItem value="PC">PC (Pension complète)</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Paiement taxes</Label>
                <Select name="taxes_payment_mode" defaultValue="on_site">
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="on_site">Sur place</SelectItem>
                    <SelectItem value="at_booking">À la réservation</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="adults">Adultes</Label>
                <Input id="adults" name="adults" type="number" min={1} defaultValue={2} required />
              </div>
              <div>
                <Label htmlFor="children">Enfants</Label>
                <Input id="children" name="children" type="number" min={0} defaultValue={0} />
              </div>
              <div>
                <Label htmlFor="first_name">Prénom client</Label>
                <Input id="first_name" name="first_name" required />
              </div>
              <div>
                <Label htmlFor="last_name">Nom client</Label>
                <Input id="last_name" name="last_name" required />
              </div>
              <div>
                <Label htmlFor="email">Email</Label>
                <Input id="email" name="email" type="email" />
              </div>
              <div>
                <Label htmlFor="phone">Téléphone</Label>
                <Input id="phone" name="phone" />
              </div>
              <div className="flex items-center gap-2 sm:col-span-2">
                <input id="deposit_paid" name="deposit_paid" type="checkbox" className="size-4 accent-primary" />
                <Label htmlFor="deposit_paid">Acompte encaissé (confirme directement la réservation)</Label>
              </div>
              <DialogFooter className="sm:col-span-2">
                <Button type="submit" disabled={createMutation.isPending}>
                  Créer la réservation
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {segments && segments.length === 0 && (
        <Alert>
          <Info />
          <AlertDescription>Aucun segment de marché configuré pour cet établissement.</AlertDescription>
        </Alert>
      )}

      {viewMode === "grid" ? (
        isLoading ? (
          <CardSkeleton className="h-96" />
        ) : (
          <PlanningGrid
            rooms={rooms ?? []}
            bookings={bookings ?? []}
            customers={customers ?? []}
            fromDate={fromDate}
            toDate={toDate}
            businessDate={businessDate}
            onShiftBooking={handleGridShift}
            onBookingClick={(b) => setShiftTarget(b)}
          />
        )
      ) : (
        <Card className="shadow-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Arrivée</TableHead>
                <TableHead>Départ</TableHead>
                <TableHead>Client</TableHead>
                <TableHead>Chambre</TableHead>
                <TableHead>Statut</TableHead>
                <TableHead>Régime</TableHead>
                <TableHead>Pax</TableHead>
                <TableHead>Montant</TableHead>
                <TableHead>Source</TableHead>
                <TableHead className="text-center">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {isLoading ? (
                <TableRowsSkeleton rows={5} columns={10} />
              ) : (bookings ?? []).length === 0 ? (
                <TableRow>
                  <TableCell colSpan={10} className="p-0">
                    <EmptyState className="border-none" title="Aucune réservation" description="Aucune réservation sur cette période." />
                  </TableCell>
                </TableRow>
              ) : (
                (bookings as Booking[]).map((booking) => {
                  const customer = customersById.get(booking.customer_id);
                  const room = roomsById.get(booking.room_id);
                  return (
                  <TableRow key={booking.id}>
                    <TableCell>{booking.check_in_date}</TableCell>
                    <TableCell>{booking.check_out_date}</TableCell>
                    <TableCell>
                      {customer ? `${customer.first_name} ${customer.last_name}` : booking.customer_id.slice(0, 8)}
                    </TableCell>
                    <TableCell>
                      {room ? `${room.numero} — ${room.categorie}` : booking.room_id.slice(0, 8)}
                    </TableCell>
                    <TableCell>
                      <Select
                        value={booking.status}
                        onValueChange={(v) => statusMutation.mutate({ id: booking.id, status: v })}
                      >
                        <SelectTrigger className="h-7 w-36 text-xs">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {ALL_STATUSES.map((s) => (
                            <SelectItem key={s} value={s}>
                              {STATUS_LABELS[s]}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell>{booking.regime}</TableCell>
                    <TableCell>
                      {booking.adults}A{booking.children > 0 ? ` + ${booking.children}E` : ""}
                    </TableCell>
                    <TableCell>{booking.total_amount != null ? `${booking.total_amount} MAD` : "—"}</TableCell>
                    <TableCell>{booking.source}</TableCell>
                    <TableCell className="text-center space-x-2">
                      {ACTIVE_FOR_SHIFT.has(booking.status) && (
                        <Button size="sm" variant="outline" onClick={() => setShiftTarget(booking)}>
                          Changer chambre
                        </Button>
                      )}
                      {CANCELLABLE.has(booking.status) && (
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={cancelMutation.isPending}
                          onClick={() =>
                            cancelMutation.mutate({ id: booking.id, reason: "Annulée depuis le back-office" })
                          }
                        >
                          Annuler
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                  );
                })
              )}
            </TableBody>
          </Table>
        </Card>
      )}

      {/* Room shift / upsell — Workflow F */}
      <Dialog
        open={Boolean(shiftTarget)}
        onOpenChange={(open) => {
          if (!open) {
            setShiftTarget(null);
            setElevationToken(null);
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Changer de chambre — Workflow F</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleShiftSubmit} className="space-y-3">
            <p className="text-sm text-muted-foreground">
              Chambre actuelle : {currentRoom ? `${currentRoom.numero} (${currentRoom.categorie})` : "—"}
            </p>
            <div>
              <Label>Nouvelle chambre</Label>
              <Select name="new_room_id">
                <SelectTrigger>
                  <SelectValue placeholder="Choisir" />
                </SelectTrigger>
                <SelectContent>
                  {(rooms ?? [])
                    .filter((r) => r.id !== shiftTarget?.room_id)
                    .map((r: Room) => (
                      <SelectItem key={r.id} value={r.id}>
                        {r.numero} — {r.categorie}
                      </SelectItem>
                    ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Motif</Label>
              <Input name="reason" placeholder="Surclassement commercial, panne technique..." />
            </div>
            <Alert>
              <Info />
              <AlertDescription className="space-y-2">
                <p>
                  Un changement vers une catégorie différente (upsell) nécessite une autorisation manager. Si le
                  bouton ci-dessous échoue, un compte manager/admin doit l&apos;obtenir.
                </p>
                <div className="flex items-center gap-2">
                  <Button
                    type="button"
                    size="sm"
                    variant="outline"
                    disabled={elevateMutation.isPending}
                    onClick={() => elevateMutation.mutate()}
                  >
                    Obtenir un jeton manager
                  </Button>
                  {elevationToken && (
                    <Badge className="border-status-success/30 bg-status-success/10 text-status-success" variant="outline">
                      Jeton obtenu
                    </Badge>
                  )}
                </div>
              </AlertDescription>
            </Alert>
            <DialogFooter>
              <Button type="submit" disabled={shiftMutation.isPending}>
                Confirmer le changement
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

// ---------------------------------------------------------- Availability ---

function AvailabilityTab({ establishmentId, businessDate }: { establishmentId: string; businessDate: string }) {
  const [result, setResult] = useState<{ available: boolean; conflicting_booking_id: string | null } | null>(null);
  const { data: rooms } = useQuery({
    queryKey: ["establishment-rooms", establishmentId],
    queryFn: () => fetchRooms(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const checkMutation = useMutation({
    mutationFn: checkAvailability,
    onSuccess: setResult,
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <Card className="shadow-card max-w-xl">
      <CardHeader>
        <CardTitle>Vérifier la disponibilité d&apos;une chambre</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <form
          className="grid grid-cols-1 gap-4 sm:grid-cols-2"
          onSubmit={(e) => {
            e.preventDefault();
            const fd = new FormData(e.currentTarget);
            checkMutation.mutate({
              establishment_id: establishmentId,
              room_id: String(fd.get("room_id")),
              check_in_date: String(fd.get("check_in_date")),
              check_out_date: String(fd.get("check_out_date")),
            });
          }}
        >
          <div className="sm:col-span-2">
            <Label>Chambre</Label>
            <Select name="room_id">
              <SelectTrigger>
                <SelectValue placeholder="Choisir une chambre" />
              </SelectTrigger>
              <SelectContent>
                {(rooms ?? []).map((r) => (
                  <SelectItem key={r.id} value={r.id}>
                    {r.numero} — {r.categorie}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div>
            <Label>Arrivée</Label>
            <Input name="check_in_date" type="date" required defaultValue={businessDate} />
          </div>
          <div>
            <Label>Départ</Label>
            <Input name="check_out_date" type="date" required defaultValue={addDaysIso(businessDate, 1)} />
          </div>
          <div className="sm:col-span-2">
            <Button type="submit" disabled={checkMutation.isPending}>
              Vérifier
            </Button>
          </div>
        </form>
        {result && (
          <Alert
            className={
              result.available
                ? "border-status-success/30 bg-status-success/5"
                : "border-destructive/30 bg-destructive/5"
            }
          >
            {result.available ? (
              <CheckCircle className="text-status-success" weight="fill" />
            ) : (
              <WarningCircle className="text-destructive" weight="fill" />
            )}
            <AlertDescription className="text-foreground">
              {result.available
                ? "Chambre disponible sur cette période."
                : `Indisponible — conflit avec la réservation ${result.conflicting_booking_id?.slice(0, 8)}…`}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}

// -------------------------------------------------------------- Segments ---

function SegmentsTab({ establishmentId }: { establishmentId: string }) {
  const queryClient = useQueryClient();
  const { data: segments } = useQuery({
    queryKey: ["market-segments", establishmentId],
    queryFn: () => fetchMarketSegments(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const createMutation = useMutation({
    mutationFn: (input: { code: string; label: string; category: string; color: string }) =>
      createMarketSegment(establishmentId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["market-segments", establishmentId] });
      toast.success("Segment créé");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      updateMarketSegment(establishmentId, id, { is_active }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["market-segments", establishmentId] }),
    onError: (error: Error) => toast.error(error.message),
  });

  return (
    <div className="space-y-4">
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Nouveau segment de marché</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid grid-cols-2 items-end gap-2 sm:grid-cols-4"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              createMutation.mutate({
                code: String(fd.get("code")),
                label: String(fd.get("label")),
                category: String(fd.get("category")),
                color: String(fd.get("color")),
              });
              e.currentTarget.reset();
            }}
          >
            <div>
              <Label>Code</Label>
              <Input name="code" required placeholder="CORPORATE" />
            </div>
            <div>
              <Label>Libellé</Label>
              <Input name="label" required />
            </div>
            <div>
              <Label>Catégorie</Label>
              <Select name="category" defaultValue="DIRECT">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="DIRECT">Direct</SelectItem>
                  <SelectItem value="OTA">OTA</SelectItem>
                  <SelectItem value="PARTENAIRES">Partenaires</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Couleur</Label>
              <Input name="color" type="color" defaultValue="#4f46e5" className="h-9 p-1" />
            </div>
            <div className="col-span-2 sm:col-span-4">
              <Button type="submit" disabled={createMutation.isPending}>
                Ajouter
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
      <Card className="shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Code</TableHead>
              <TableHead>Libellé</TableHead>
              <TableHead>Catégorie</TableHead>
              <TableHead>Couleur</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-center">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {!segments?.length ? (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState className="border-none" title="Aucun segment" description="Créez votre premier segment de marché ci-dessus." />
                </TableCell>
              </TableRow>
            ) : (
              segments.map((s) => (
                <TableRow key={s.id}>
                  <TableCell className="font-mono text-xs">{s.code}</TableCell>
                  <TableCell>{s.label}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{s.category}</Badge>
                  </TableCell>
                  <TableCell>
                    <span className="inline-block size-4 rounded-full border border-border" style={{ backgroundColor: s.color }} />
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant="outline"
                      className={s.is_active ? "border-status-success/30 bg-status-success/10 text-status-success" : "text-muted-foreground"}
                    >
                      {s.is_active ? "Actif" : "Inactif"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-center">
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={toggleMutation.isPending}
                      onClick={() => toggleMutation.mutate({ id: s.id, is_active: !s.is_active })}
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
    </div>
  );
}

// -------------------------------------------------------------- Customers -

function CustomersTab({ establishmentId }: { establishmentId: string }) {
  const queryClient = useQueryClient();
  const [search, setSearch] = useState("");
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);

  const { data: customers, isLoading } = useQuery({
    queryKey: ["customers", establishmentId],
    queryFn: () => fetchCustomers(establishmentId),
    enabled: Boolean(establishmentId),
  });

  const createMutation = useMutation({
    mutationFn: (input: { first_name: string; last_name: string; email?: string; phone?: string; is_vip?: boolean }) =>
      createCustomer(establishmentId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers", establishmentId] });
      toast.success("Client créé");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Parameters<typeof updateCustomer>[2] }) =>
      updateCustomer(establishmentId, id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers", establishmentId] });
      toast.success("Client mis à jour");
      setEditingCustomer(null);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const filtered = useMemo(() => {
    if (!customers) return [];
    const q = search.toLowerCase();
    return customers.filter(
      (c) =>
        c.first_name.toLowerCase().includes(q) ||
        c.last_name.toLowerCase().includes(q) ||
        (c.email ?? "").toLowerCase().includes(q)
    );
  }, [customers, search]);

  return (
    <div className="space-y-4">
      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Nouveau client</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid grid-cols-2 items-end gap-2 sm:grid-cols-5"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              createMutation.mutate({
                first_name: String(fd.get("first_name")),
                last_name: String(fd.get("last_name")),
                email: String(fd.get("email") || "") || undefined,
                phone: String(fd.get("phone") || "") || undefined,
              });
              e.currentTarget.reset();
            }}
          >
            <div>
              <Label>Prénom</Label>
              <Input name="first_name" required />
            </div>
            <div>
              <Label>Nom</Label>
              <Input name="last_name" required />
            </div>
            <div>
              <Label>Email</Label>
              <Input name="email" type="email" />
            </div>
            <div>
              <Label>Téléphone</Label>
              <Input name="phone" />
            </div>
            <Button type="submit" disabled={createMutation.isPending}>
              Créer
            </Button>
          </form>
        </CardContent>
      </Card>

      <Input placeholder="Rechercher un client..." value={search} onChange={(e) => setSearch(e.target.value)} className="max-w-xs" />

      <Card className="shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Email</TableHead>
              <TableHead>Téléphone</TableHead>
              <TableHead>VIP</TableHead>
              <TableHead className="text-center">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRowsSkeleton rows={4} columns={5} />
            ) : filtered.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="p-0">
                  <EmptyState className="border-none" title="Aucun client" description="Aucun client ne correspond à votre recherche." />
                </TableCell>
              </TableRow>
            ) : (
              filtered.map((c) =>
                editingCustomer?.id === c.id ? (
                  <InlineEditRow key={c.id} colSpan={5}>
                    <form
                      className="flex flex-wrap items-end gap-2"
                      onSubmit={(e) => {
                        e.preventDefault();
                        const fd = new FormData(e.currentTarget);
                        updateMutation.mutate({
                          id: c.id,
                          input: {
                            first_name: String(fd.get("first_name")),
                            last_name: String(fd.get("last_name")),
                            email: String(fd.get("email") || "") || undefined,
                            phone: String(fd.get("phone") || "") || undefined,
                            is_vip: fd.get("is_vip") === "on",
                          },
                        });
                      }}
                    >
                      <div>
                        <Label className="text-xs">Prénom</Label>
                        <Input name="first_name" defaultValue={c.first_name} className="w-32" />
                      </div>
                      <div>
                        <Label className="text-xs">Nom</Label>
                        <Input name="last_name" defaultValue={c.last_name} className="w-32" />
                      </div>
                      <div>
                        <Label className="text-xs">Email</Label>
                        <Input name="email" defaultValue={c.email ?? ""} className="w-44" />
                      </div>
                      <div>
                        <Label className="text-xs">Téléphone</Label>
                        <Input name="phone" defaultValue={c.phone ?? ""} className="w-32" />
                      </div>
                      <label className="flex items-center gap-1 pb-2 text-sm">
                        <input type="checkbox" name="is_vip" defaultChecked={c.is_vip} className="accent-primary" /> VIP
                      </label>
                      <div className="ml-auto flex gap-2 pb-0.5">
                        <Button type="submit" size="sm" disabled={updateMutation.isPending}>
                          Enregistrer
                        </Button>
                        <Button type="button" size="sm" variant="ghost" onClick={() => setEditingCustomer(null)}>
                          Annuler
                        </Button>
                      </div>
                    </form>
                  </InlineEditRow>
                ) : (
                  <TableRow key={c.id}>
                    <TableCell className="font-medium">
                      {c.first_name} {c.last_name}
                    </TableCell>
                    <TableCell>{c.email ?? "—"}</TableCell>
                    <TableCell>{c.phone ?? "—"}</TableCell>
                    <TableCell>{c.is_vip ? "Oui" : "Non"}</TableCell>
                    <TableCell className="text-center">
                      <Button size="sm" variant="outline" onClick={() => setEditingCustomer(c)}>
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
    </div>
  );
}
