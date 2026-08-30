"use client";

import { ClockCounterClockwise, MagnifyingGlass, Warning } from "@phosphor-icons/react";
import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
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
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { EmptyState } from "@/components/empty-state";
import { PageHeader } from "@/components/page-header";
import { StatTile } from "@/components/stat-tile";
import { TableRowsSkeleton } from "@/components/loading-state";
import { RoomStatusBadge } from "@/components/status-badge";
import { useRoomStatusMutation } from "@/hooks/use-room-status-mutation";
import { useRooms } from "@/hooks/use-rooms";
import { useRoomsWebSocket } from "@/hooks/use-rooms-websocket";
import {
  fetchRoomHistory,
  fetchRoomIncidents,
  reportIncident,
  type Room,
} from "@/lib/api-clients/housekeeping";
import { useSessionStore } from "@/store/session-store";

const NEXT_STATUS: Record<string, string> = {
  Sale: "Nettoyage",
  Nettoyage: "Propre",
  Propre: "Contrôlée",
  Contrôlée: "Bloquée",
  Bloquée: "Propre",
};

const NEXT_ACTION_LABEL: Record<string, string> = {
  Sale: "Commencer nettoyage",
  Nettoyage: "Marquer propre",
  Propre: "Marquer contrôlée",
  Contrôlée: "Bloquer",
  Bloquée: "Débloquer",
};

// Motifs transcrits verbatim du CHECK constraint (§5.4) — 'Panne' reste le
// code stable en base, affiché "Problème technique" (D5 / housekeeping.html).
const BLOCK_REASONS: { code: string; label: string }[] = [
  { code: "Day Use", label: "Day Use" },
  { code: "Panne", label: "Problème technique" },
  { code: "Départ tardif", label: "Départ tardif" },
  { code: "Travaux", label: "Travaux" },
];

const INCIDENT_TYPES = ["Panne technique", "Manque de linge", "Problème sanitaire", "Autre"];

const UNBLOCK_ROLES = ["gouvernante", "manager", "admin"];

const STATUS_DOT: Record<string, string> = {
  Sale: "bg-status-neutral",
  Nettoyage: "bg-status-warning",
  Propre: "bg-status-success",
  Contrôlée: "bg-status-info",
  Bloquée: "bg-status-danger",
};

export default function HousekeepingPage() {
  const activeEstablishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const claims = useSessionStore((s) => s.claims);
  const { data: rooms, isLoading } = useRooms(activeEstablishmentId);
  const statusMutation = useRoomStatusMutation(activeEstablishmentId);
  useRoomsWebSocket(activeEstablishmentId);

  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [blockTarget, setBlockTarget] = useState<Room | null>(null);
  const [blockReason, setBlockReason] = useState<string>("");
  const [incidentTarget, setIncidentTarget] = useState<Room | null>(null);
  const [incidentType, setIncidentType] = useState<string>("");
  const [incidentDescription, setIncidentDescription] = useState("");
  const [detailTarget, setDetailTarget] = useState<Room | null>(null);

  const { data: roomHistory } = useQuery({
    queryKey: ["room-history", detailTarget?.id],
    queryFn: () => fetchRoomHistory(detailTarget!.id),
    enabled: Boolean(detailTarget),
  });
  const { data: roomIncidents } = useQuery({
    queryKey: ["room-incidents", detailTarget?.id],
    queryFn: () => fetchRoomIncidents(detailTarget!.id),
    enabled: Boolean(detailTarget),
  });

  const canUnblock = Boolean(
    claims?.is_super_admin || claims?.roles.some((r) => UNBLOCK_ROLES.includes(r))
  );

  const filteredRooms = useMemo(() => {
    if (!rooms) return [];
    return rooms.filter((room) => {
      const matchesSearch = room.numero.toLowerCase().includes(search.toLowerCase());
      const matchesStatus = statusFilter === "all" || room.statut === statusFilter;
      return matchesSearch && matchesStatus;
    });
  }, [rooms, search, statusFilter]);

  const stats = useMemo(() => {
    const counts: Record<string, number> = {
      Sale: 0,
      Nettoyage: 0,
      Propre: 0,
      Contrôlée: 0,
      Bloquée: 0,
    };
    (rooms ?? []).forEach((room) => {
      counts[room.statut] = (counts[room.statut] ?? 0) + 1;
    });
    return counts;
  }, [rooms]);

  function handleAction(room: Room) {
    const nextStatus = NEXT_STATUS[room.statut];
    if (nextStatus === "Bloquée") {
      setBlockTarget(room);
      return;
    }
    if (room.statut === "Bloquée" && !canUnblock) {
      return; // bouton non affiché normalement, garde-fou défensif
    }
    statusMutation.mutate({ roomId: room.id, newStatus: nextStatus });
  }

  function confirmBlock() {
    if (!blockTarget || !blockReason) return;
    statusMutation.mutate(
      { roomId: blockTarget.id, newStatus: "Bloquée", reason: blockReason },
      { onSuccess: () => setBlockTarget(null) }
    );
    setBlockReason("");
  }

  async function confirmIncident() {
    if (!incidentTarget || !incidentType) return;
    await reportIncident(incidentTarget.id, incidentType, incidentDescription || undefined);
    setIncidentTarget(null);
    setIncidentType("");
    setIncidentDescription("");
  }

  if (!activeEstablishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour voir son état des chambres." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Housekeeping" description="État des chambres en temps réel" />

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
        {(["Sale", "Nettoyage", "Propre", "Contrôlée", "Bloquée"] as const).map((status) => (
          <StatTile
            key={status}
            label={
              <span className="flex items-center gap-1.5">
                <span className={`size-1.5 rounded-full ${STATUS_DOT[status]}`} />
                {status}
              </span>
            }
            value={stats[status]}
          />
        ))}
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <div className="relative max-w-xs flex-1">
          <MagnifyingGlass className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Rechercher une chambre..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-8"
          />
        </div>
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-48">
            <SelectValue placeholder="Statut" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Tous les statuts</SelectItem>
            {["Sale", "Nettoyage", "Propre", "Contrôlée", "Bloquée"].map((s) => (
              <SelectItem key={s} value={s}>
                {s}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Card className="shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Chambre</TableHead>
              <TableHead>Catégorie</TableHead>
              <TableHead>Étage</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Motif blocage</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRowsSkeleton rows={5} columns={6} />
            ) : filteredRooms.length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState
                    className="border-none"
                    title="Aucune chambre"
                    description="Aucune chambre ne correspond à votre recherche ou au filtre sélectionné."
                  />
                </TableCell>
              </TableRow>
            ) : (
              filteredRooms.map((room) => {
                const isUnblockAction = room.statut === "Bloquée";
                const actionHidden = isUnblockAction && !canUnblock;
                return (
                  <TableRow key={room.id}>
                    <TableCell className="font-medium">{room.numero}</TableCell>
                    <TableCell>{room.categorie}</TableCell>
                    <TableCell>{room.floor}</TableCell>
                    <TableCell>
                      <RoomStatusBadge status={room.statut} />
                    </TableCell>
                    <TableCell>
                      {room.blocked_reason ? (
                        <Badge variant="outline">{room.blocked_reason}</Badge>
                      ) : (
                        <span className="text-muted-foreground">—</span>
                      )}
                    </TableCell>
                    <TableCell className="flex justify-end gap-2">
                      {!actionHidden && (
                        <Button size="sm" variant="outline" onClick={() => handleAction(room)}>
                          {NEXT_ACTION_LABEL[room.statut]}
                        </Button>
                      )}
                      <Button size="sm" variant="ghost" onClick={() => setIncidentTarget(room)}>
                        <Warning className="size-4" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => setDetailTarget(room)}>
                        <ClockCounterClockwise className="size-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </Card>

      {/* Historique + incidents (lecture seule) */}
      <Dialog open={Boolean(detailTarget)} onOpenChange={(open) => !open && setDetailTarget(null)}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Historique — chambre {detailTarget?.numero}</DialogTitle>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="mb-2 text-sm font-medium">Changements de statut</p>
              <div className="max-h-64 space-y-2 overflow-y-auto text-sm">
                {(roomHistory ?? []).length === 0 && (
                  <p className="text-muted-foreground">Aucun historique.</p>
                )}
                {(roomHistory ?? []).map((h) => (
                  <div key={h.id} className="rounded-lg border border-border p-2">
                    <p>
                      {h.old_status ?? "—"} → <strong>{h.new_status}</strong>
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(h.changed_at).toLocaleString("fr-FR")}
                      {h.reason ? ` — ${h.reason}` : ""}
                    </p>
                  </div>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-2 text-sm font-medium">Incidents signalés</p>
              <div className="max-h-64 space-y-2 overflow-y-auto text-sm">
                {(roomIncidents ?? []).length === 0 && (
                  <p className="text-muted-foreground">Aucun incident.</p>
                )}
                {(roomIncidents ?? []).map((i) => (
                  <div key={i.id} className="rounded-lg border border-border p-2">
                    <p className="font-medium">{i.incident_type}</p>
                    {i.description && <p className="text-xs">{i.description}</p>}
                    <p className="text-xs text-muted-foreground">
                      {new Date(i.reported_at).toLocaleString("fr-FR")}
                      {i.resolved_at ? " — résolu" : " — ouvert"}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Blocage — motif obligatoire (422 REASON_REQUIRED côté backend si absent) */}
      <Dialog open={Boolean(blockTarget)} onOpenChange={(open) => !open && setBlockTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Bloquer la chambre {blockTarget?.numero}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Label>Motif du blocage</Label>
            <Select value={blockReason} onValueChange={setBlockReason}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner un motif" />
              </SelectTrigger>
              <SelectContent>
                {BLOCK_REASONS.map((reason) => (
                  <SelectItem key={reason.code} value={reason.code}>
                    {reason.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setBlockTarget(null)}>
              Annuler
            </Button>
            <Button disabled={!blockReason} onClick={confirmBlock}>
              Confirmer le blocage
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Signalement d'incident (Workflow H étape 4) */}
      <Dialog
        open={Boolean(incidentTarget)}
        onOpenChange={(open) => !open && setIncidentTarget(null)}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Signaler un problème — chambre {incidentTarget?.numero}</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <Label>Type d&apos;incident</Label>
            <Select value={incidentType} onValueChange={setIncidentType}>
              <SelectTrigger>
                <SelectValue placeholder="Sélectionner un type" />
              </SelectTrigger>
              <SelectContent>
                {INCIDENT_TYPES.map((type) => (
                  <SelectItem key={type} value={type}>
                    {type}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Label>Description (optionnel)</Label>
            <Textarea
              value={incidentDescription}
              onChange={(e) => setIncidentDescription(e.target.value)}
              placeholder="Détails..."
            />
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setIncidentTarget(null)}>
              Annuler
            </Button>
            <Button disabled={!incidentType} onClick={confirmIncident}>
              Signaler
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
