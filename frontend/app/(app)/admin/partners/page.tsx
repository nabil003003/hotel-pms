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
import { InlineEditRow } from "@/components/inline-edit-row";
import { TableRowsSkeleton } from "@/components/loading-state";
import { PageHeader } from "@/components/page-header";
import { createPartner, deletePartner, fetchPartners, updatePartner, type Partner } from "@/lib/api-clients/partner";
import { useSessionStore } from "@/store/session-store";

function ActiveBadge({ active }: { active: boolean }) {
  return (
    <Badge
      variant="outline"
      className={active ? "border-status-success/30 bg-status-success/10 text-status-success" : "text-muted-foreground"}
    >
      {active ? "Actif" : "Inactif"}
    </Badge>
  );
}

export default function PartnersAdminPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const queryClient = useQueryClient();
  const [editingPartner, setEditingPartner] = useState<Partner | null>(null);

  const { data: partners, isLoading } = useQuery({
    queryKey: ["partners", establishmentId],
    queryFn: () => fetchPartners(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const createMutation = useMutation({
    mutationFn: (input: {
      type: string;
      nom: string;
      contact_name?: string;
      email?: string;
      phone?: string;
      payment_terms: number;
    }) => createPartner(establishmentId as string, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partners", establishmentId] });
      toast.success("Partenaire créé");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, input }: { id: string; input: Parameters<typeof updatePartner>[2] }) =>
      updatePartner(establishmentId as string, id, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partners", establishmentId] });
      toast.success("Partenaire mis à jour");
      setEditingPartner(null);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const deactivateMutation = useMutation({
    mutationFn: (id: string) => deletePartner(establishmentId as string, id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["partners", establishmentId] });
      toast.success("Partenaire désactivé");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour gérer ses partenaires." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Partenaires" description="Agences, tour-opérateurs, sociétés et OTA" />

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Nouveau partenaire (agence / TO / société / OTA)</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid grid-cols-1 gap-4 sm:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              createMutation.mutate({
                type: String(fd.get("type")),
                nom: String(fd.get("nom")),
                contact_name: String(fd.get("contact_name") || "") || undefined,
                email: String(fd.get("email") || "") || undefined,
                phone: String(fd.get("phone") || "") || undefined,
                payment_terms: Number(fd.get("payment_terms") || 30),
              });
              e.currentTarget.reset();
            }}
          >
            <div>
              <Label>Type</Label>
              <Select name="type" defaultValue="AGENCE">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="AGENCE">Agence</SelectItem>
                  <SelectItem value="TO">Tour-opérateur</SelectItem>
                  <SelectItem value="CORPORATE">Société (corporate)</SelectItem>
                  <SelectItem value="OTA">OTA</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Nom</Label>
              <Input name="nom" required placeholder="Atlas Voyages" />
            </div>
            <div>
              <Label>Contact</Label>
              <Input name="contact_name" />
            </div>
            <div>
              <Label>Email</Label>
              <Input name="email" type="email" />
            </div>
            <div>
              <Label>Téléphone</Label>
              <Input name="phone" />
            </div>
            <div>
              <Label>Délai de paiement (jours)</Label>
              <Input name="payment_terms" type="number" min={0} defaultValue={30} />
            </div>
            <div className="sm:col-span-3">
              <Button type="submit" disabled={createMutation.isPending}>
                Créer le partenaire
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Nom</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Contact</TableHead>
              <TableHead>Délai paiement</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRowsSkeleton rows={4} columns={6} />
            ) : !partners?.length ? (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState className="border-none" title="Aucun partenaire" description="Créez votre premier partenaire ci-dessus." />
                </TableCell>
              </TableRow>
            ) : (
              partners.map((p) =>
                editingPartner?.id === p.id ? (
                  <InlineEditRow key={p.id} colSpan={6}>
                    <form
                      className="flex flex-wrap items-end gap-2"
                      onSubmit={(e) => {
                        e.preventDefault();
                        const fd = new FormData(e.currentTarget);
                        updateMutation.mutate({
                          id: p.id,
                          input: {
                            nom: String(fd.get("nom")),
                            contact_name: String(fd.get("contact_name") || "") || undefined,
                            email: String(fd.get("email") || "") || undefined,
                            phone: String(fd.get("phone") || "") || undefined,
                            payment_terms: Number(fd.get("payment_terms") || p.payment_terms),
                          },
                        });
                      }}
                    >
                      <Input name="nom" defaultValue={p.nom} className="w-40" />
                      <Input name="contact_name" defaultValue={p.contact_name ?? ""} placeholder="Contact" className="w-32" />
                      <Input name="email" defaultValue={p.email ?? ""} placeholder="Email" className="w-40" />
                      <Input name="phone" defaultValue={p.phone ?? ""} placeholder="Téléphone" className="w-32" />
                      <Input name="payment_terms" type="number" defaultValue={p.payment_terms} className="w-20" />
                      <Button type="submit" size="sm" disabled={updateMutation.isPending}>
                        Enregistrer
                      </Button>
                      <Button type="button" size="sm" variant="ghost" onClick={() => setEditingPartner(null)}>
                        Annuler
                      </Button>
                    </form>
                  </InlineEditRow>
                ) : (
                  <TableRow key={p.id}>
                    <TableCell className="font-medium">{p.nom}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{p.type}</Badge>
                    </TableCell>
                    <TableCell>{p.contact_name ?? "—"}</TableCell>
                    <TableCell>{p.payment_terms}j</TableCell>
                    <TableCell>
                      <ActiveBadge active={p.is_active} />
                    </TableCell>
                    <TableCell className="text-right space-x-2">
                      <Button size="sm" variant="outline" onClick={() => setEditingPartner(p)}>
                        Modifier
                      </Button>
                      {p.is_active && (
                        <Button
                          size="sm"
                          variant="ghost"
                          disabled={deactivateMutation.isPending}
                          onClick={() => deactivateMutation.mutate(p.id)}
                        >
                          Désactiver
                        </Button>
                      )}
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
