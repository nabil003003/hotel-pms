"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import {
  fetchNotifications,
  markNotificationRead,
  sendMessage,
  STAFF_ROLES,
  STAFF_ROLE_LABELS,
  type Notification,
} from "@/lib/api-clients/notification";
import { reportDownloadUrl } from "@/lib/api-clients/night-audit";
import { useSessionStore } from "@/store/session-store";

const CHANNEL_LABELS: Record<string, string> = { email: "Email", push: "Push", sms: "SMS", message: "Message" };

const EVENT_TYPE_LABELS: Record<string, string> = {
  "booking.created": "Réservation créée",
  "booking.checked_in": "Check-in effectué",
  "booking.checked_out": "Check-out effectué",
  "booking.cancelled": "Réservation annulée",
  "room.incident_reported": "Incident chambre signalé",
  "channel.sync_failed": "Échec de synchronisation OTA",
  "audit.discrepancy_detected": "Écart détecté (night audit)",
  "audit.report_ready": "Rapport de clôture disponible",
  "message.direct": "Message direct",
};

const EVENT_TYPES = Object.keys(EVENT_TYPE_LABELS);

export default function NotificationsPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const claims = useSessionStore((s) => s.claims);
  const queryClient = useQueryClient();
  const [eventTypeFilter, setEventTypeFilter] = useState<string>("all");
  const [detailTarget, setDetailTarget] = useState<Notification | null>(null);
  const [composeOpen, setComposeOpen] = useState(false);
  const [composeRole, setComposeRole] = useState<string>("receptionniste");
  const [composeSubject, setComposeSubject] = useState("");
  const [composeBody, setComposeBody] = useState("");

  const canSendMessage = Boolean(claims?.is_super_admin || claims?.roles.some((r) => ["manager", "admin"].includes(r)));

  const { data: notifications, isLoading } = useQuery({
    queryKey: ["notifications", establishmentId, eventTypeFilter],
    queryFn: () => fetchNotifications(establishmentId as string, eventTypeFilter === "all" ? undefined : eventTypeFilter),
    enabled: Boolean(establishmentId),
  });

  const readMutation = useMutation({
    mutationFn: markNotificationRead,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
      queryClient.invalidateQueries({ queryKey: ["my-notifications"] });
    },
  });

  const sendMutation = useMutation({
    mutationFn: () => sendMessage(establishmentId as string, composeRole, composeSubject, composeBody),
    onSuccess: () => {
      toast.success("Message envoyé");
      setComposeOpen(false);
      setComposeSubject("");
      setComposeBody("");
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
    onError: (err: Error) => toast.error(err.message),
  });

  function openDetail(n: Notification) {
    setDetailTarget(n);
    if (!n.read_at) readMutation.mutate(n.id);
  }

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour voir ses notifications." />;
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <PageHeader
          title="Notifications"
          description="Journal des notifications (livraison email/SMS/push simulée en développement — les messages entre utilisateurs, eux, sont réels et restent dans l'application)."
        />
        {canSendMessage && <Button onClick={() => setComposeOpen(true)}>Nouveau message</Button>}
      </div>

      <Select value={eventTypeFilter} onValueChange={setEventTypeFilter}>
        <SelectTrigger className="w-64">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Tous les événements</SelectItem>
          {EVENT_TYPES.map((e) => (
            <SelectItem key={e} value={e}>
              {EVENT_TYPE_LABELS[e]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Card className="shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Événement</TableHead>
              <TableHead>Canal</TableHead>
              <TableHead>Destinataire</TableHead>
              <TableHead>Sujet</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Créée le</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRowsSkeleton rows={5} columns={6} />
            ) : (notifications ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState className="border-none" title="Aucune notification" description="Aucun événement ne correspond au filtre sélectionné." />
                </TableCell>
              </TableRow>
            ) : (
              notifications!.map((n) => (
                <TableRow key={n.id} className="cursor-pointer" onClick={() => openDetail(n)}>
                  <TableCell className="text-xs">
                    <span className={n.read_at ? undefined : "font-semibold text-foreground"}>
                      {!n.read_at && <span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-status-info align-middle" />}
                      {EVENT_TYPE_LABELS[n.event_type] ?? n.event_type}
                    </span>
                  </TableCell>
                  <TableCell>{CHANNEL_LABELS[n.channel] ?? n.channel}</TableCell>
                  <TableCell>{STAFF_ROLE_LABELS[n.recipient_role] ?? n.recipient_role}</TableCell>
                  <TableCell>{n.subject}</TableCell>
                  <TableCell>
                    <Badge variant={n.status === "sent" ? "default" : "outline"}>{n.status}</Badge>
                  </TableCell>
                  <TableCell className="text-xs text-muted-foreground">
                    {new Date(n.created_at).toLocaleString("fr-FR")}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </Card>

      <Dialog open={Boolean(detailTarget)} onOpenChange={(open) => !open && setDetailTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{detailTarget?.subject}</DialogTitle>
          </DialogHeader>
          {detailTarget && (
            <div className="space-y-2 text-sm">
              <p>
                <span className="text-muted-foreground">Événement :</span> {EVENT_TYPE_LABELS[detailTarget.event_type] ?? detailTarget.event_type}
              </p>
              <p>
                <span className="text-muted-foreground">Canal :</span> {CHANNEL_LABELS[detailTarget.channel]}
              </p>
              <p>
                <span className="text-muted-foreground">Destinataire :</span>{" "}
                {STAFF_ROLE_LABELS[detailTarget.recipient_role] ?? detailTarget.recipient_role}
              </p>
              {typeof detailTarget.payload.sender_email === "string" && (
                <p>
                  <span className="text-muted-foreground">De :</span> {detailTarget.payload.sender_email}
                </p>
              )}
              <p>
                <span className="text-muted-foreground">Statut :</span> {detailTarget.status}
              </p>
              <p className="rounded-lg border border-border p-2">{detailTarget.body}</p>

              {detailTarget.event_type === "audit.report_ready" &&
                Array.isArray(detailTarget.payload.report_filenames) &&
                typeof detailTarget.payload.establishment_id === "string" &&
                typeof detailTarget.payload.business_date === "string" && (
                  <ul className="space-y-1 rounded-lg border border-border p-2 text-xs">
                    {(detailTarget.payload.report_filenames as string[]).map((name) => (
                      <li key={name}>
                        <a
                          href={reportDownloadUrl(
                            detailTarget.payload.establishment_id as string,
                            detailTarget.payload.business_date as string,
                            name
                          )}
                          download={name}
                          className="text-foreground underline underline-offset-2 hover:text-status-success"
                        >
                          {name}
                        </a>
                      </li>
                    ))}
                  </ul>
                )}

              <p className="text-xs text-muted-foreground">
                Créée le {new Date(detailTarget.created_at).toLocaleString("fr-FR")}
                {detailTarget.sent_at ? ` — envoyée le ${new Date(detailTarget.sent_at).toLocaleString("fr-FR")}` : ""}
                {detailTarget.read_at ? ` — lue le ${new Date(detailTarget.read_at).toLocaleString("fr-FR")}` : ""}
              </p>
            </div>
          )}
        </DialogContent>
      </Dialog>

      <Dialog open={composeOpen} onOpenChange={setComposeOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouveau message</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div>
              <Label>Destinataire</Label>
              <Select value={composeRole} onValueChange={setComposeRole}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {STAFF_ROLES.map((r) => (
                    <SelectItem key={r} value={r}>
                      {STAFF_ROLE_LABELS[r]}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Sujet</Label>
              <Input value={composeSubject} onChange={(e) => setComposeSubject(e.target.value)} />
            </div>
            <div>
              <Label>Message</Label>
              <Textarea value={composeBody} onChange={(e) => setComposeBody(e.target.value)} rows={4} />
            </div>
            <Button
              className="w-full"
              disabled={!composeSubject || !composeBody || sendMutation.isPending}
              onClick={() => sendMutation.mutate()}
            >
              Envoyer
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
