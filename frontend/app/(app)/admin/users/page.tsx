"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { Warning } from "@phosphor-icons/react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
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
import {
  createUser,
  deactivateEstablishmentUser,
  deleteEstablishmentUserPermanently,
  fetchEstablishmentUsers,
  updateEstablishmentUserRole,
  type EstablishmentUser,
  type UserCreateResult,
} from "@/lib/api-clients/auth-gateway";
import { fetchEstablishments } from "@/lib/api-clients/establishment";
import { useSessionStore } from "@/store/session-store";

const ROLES = ["receptionniste", "gouvernante", "femme_de_chambre", "comptable", "manager", "admin", "agence_externe"];

function formatDateTime(iso: string) {
  return new Date(iso).toLocaleString("fr-FR", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function UsersAdminPage() {
  const establishmentId = useSessionStore((s) => s.activeEstablishmentId);
  const queryClient = useQueryClient();
  const [lastCreated, setLastCreated] = useState<UserCreateResult | null>(null);
  const [editingUser, setEditingUser] = useState<EstablishmentUser | null>(null);

  const { data: establishments } = useQuery({
    queryKey: ["establishments"],
    queryFn: fetchEstablishments,
  });

  const { data: users, isLoading } = useQuery({
    queryKey: ["establishment-users", establishmentId],
    queryFn: () => fetchEstablishmentUsers(establishmentId as string),
    enabled: Boolean(establishmentId),
  });

  const createMutation = useMutation({
    mutationFn: createUser,
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: ["establishment-users", establishmentId] });
      setLastCreated(result);
      toast.success(`Utilisateur "${result.user.email}" créé`);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const updateRoleMutation = useMutation({
    mutationFn: (input: { userId: string; role: string }) =>
      updateEstablishmentUserRole(establishmentId as string, input.userId, input.role),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishment-users", establishmentId] });
      toast.success("Rôle mis à jour");
      setEditingUser(null);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const deactivateMutation = useMutation({
    mutationFn: (userId: string) => deactivateEstablishmentUser(establishmentId as string, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishment-users", establishmentId] });
      toast.success("Utilisateur désactivé");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (userId: string) => deleteEstablishmentUserPermanently(establishmentId as string, userId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishment-users", establishmentId] });
      toast.success("Utilisateur supprimé définitivement");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  if (!establishmentId) {
    return <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement dans la barre supérieure pour gérer ses utilisateurs." />;
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Utilisateurs" description="Comptes et rôles par établissement" />

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>Nouvel utilisateur</CardTitle>
        </CardHeader>
        <CardContent>
          <form
            className="grid grid-cols-1 gap-4 sm:grid-cols-3"
            onSubmit={(e) => {
              e.preventDefault();
              const fd = new FormData(e.currentTarget);
              createMutation.mutate({
                username: String(fd.get("username")),
                email: String(fd.get("email")),
                role: String(fd.get("role")),
                establishment_ids: [establishmentId],
                is_super_admin: false,
              });
              e.currentTarget.reset();
            }}
          >
            <div>
              <Label>Nom d&apos;utilisateur</Label>
              <Input name="username" required />
            </div>
            <div>
              <Label>Email</Label>
              <Input name="email" type="email" required />
            </div>
            <div>
              <Label>Rôle</Label>
              <Select name="role" defaultValue={ROLES[0]}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {ROLES.map((r) => (
                    <SelectItem key={r} value={r}>
                      {r}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="sm:col-span-3">
              <Button type="submit" disabled={createMutation.isPending}>
                Créer l&apos;utilisateur
              </Button>
            </div>
          </form>

          {lastCreated && (
            <Alert className="mt-4 border-status-warning/30 bg-status-warning/5">
              <Warning className="text-status-warning" weight="fill" />
              <AlertTitle>Mot de passe temporaire — affiché une seule fois</AlertTitle>
              <AlertDescription className="space-y-1">
                <p>
                  Pour <strong className="text-foreground">{lastCreated.user.email}</strong> :
                </p>
                <p className="font-mono text-base text-foreground">{lastCreated.temp_password}</p>
              </AlertDescription>
            </Alert>
          )}
        </CardContent>
      </Card>

      <Card className="shadow-card">
        <CardHeader>
          <CardTitle>
            Utilisateurs — {(establishments ?? []).find((e) => e.id === establishmentId)?.name ?? "établissement actif"}
          </CardTitle>
        </CardHeader>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Email</TableHead>
              <TableHead>Nom</TableHead>
              <TableHead>Poste</TableHead>
              <TableHead>Statut</TableHead>
              <TableHead>Créé le</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRowsSkeleton rows={4} columns={6} />
            ) : (users ?? []).length === 0 ? (
              <TableRow>
                <TableCell colSpan={6} className="p-0">
                  <EmptyState className="border-none" title="Aucun utilisateur" description="Créez le premier utilisateur de cet établissement ci-dessus." />
                </TableCell>
              </TableRow>
            ) : (
              users!.map((u) =>
                editingUser?.id === u.id ? (
                  <InlineEditRow key={u.id} colSpan={6}>
                    <form
                      className="flex flex-wrap items-end gap-2"
                      onSubmit={(e) => {
                        e.preventDefault();
                        const fd = new FormData(e.currentTarget);
                        updateRoleMutation.mutate({ userId: u.id, role: String(fd.get("role")) });
                      }}
                    >
                      <div>
                        <Label>Poste</Label>
                        <Select name="role" defaultValue={u.role}>
                          <SelectTrigger className="w-48">
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            {ROLES.map((r) => (
                              <SelectItem key={r} value={r}>
                                {r}
                              </SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      </div>
                      <Button type="submit" size="sm" disabled={updateRoleMutation.isPending}>
                        Enregistrer
                      </Button>
                      <Button type="button" size="sm" variant="ghost" onClick={() => setEditingUser(null)}>
                        Annuler
                      </Button>
                    </form>
                  </InlineEditRow>
                ) : (
                  <TableRow key={u.id}>
                    <TableCell>
                      <div>{u.email}</div>
                      {u.temp_password && (
                        <div className="mt-1 text-xs text-status-warning">
                          Mot de passe temporaire (pas encore changé) :{" "}
                          <span className="font-mono">{u.temp_password}</span>
                        </div>
                      )}
                    </TableCell>
                    <TableCell>{u.display_name ?? "—"}</TableCell>
                    <TableCell>{u.role}</TableCell>
                    <TableCell>
                      <Badge variant={u.is_active ? "default" : "outline"}>{u.is_active ? "Actif" : "Inactif"}</Badge>
                    </TableCell>
                    <TableCell>{formatDateTime(u.created_at)}</TableCell>
                    <TableCell className="flex justify-end gap-2">
                      <Button size="sm" variant="outline" onClick={() => setEditingUser(u)}>
                        Modifier
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        disabled={!u.is_active || deactivateMutation.isPending}
                        onClick={() => deactivateMutation.mutate(u.id)}
                      >
                        Désactiver
                      </Button>
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button size="sm" variant="ghost" className="text-status-danger hover:text-status-danger">
                            Supprimer
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Supprimer définitivement {u.email} ?</AlertDialogTitle>
                            <AlertDialogDescription>
                              Cette action supprime le compte de Keycloak et de la base de données. Impossible à
                              annuler.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Annuler</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() => deleteMutation.mutate(u.id)}
                              disabled={deleteMutation.isPending}
                            >
                              Supprimer définitivement
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
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
