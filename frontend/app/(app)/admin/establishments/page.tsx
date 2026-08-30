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
import { PageHeader } from "@/components/page-header";
import {
  createEstablishment,
  createEstablishmentService,
  createRoomsBulk,
  deleteRoom,
  fetchEstablishments,
  fetchEstablishmentServices,
  fetchOtaMappings,
  fetchRooms,
  updateEstablishment,
  updateRoom,
  upsertOtaMapping,
  type Room,
  type RoomCreateInput,
} from "@/lib/api-clients/establishment";
import { useSessionStore } from "@/store/session-store";

// Taxonomie canonique (D5 / Workflow K) — cf. establishment-service
// domain/models.py:CANONICAL_ROOM_CATEGORIES.
const ROOM_CATEGORIES = [
  "Chambre Standard",
  "Chambre Deluxe",
  "Suite Junior",
  "Suite Royale",
  "Riad Entier",
];

// Doit correspondre exactement au CHECK constraint chk_establishment_services_category
// (establishment-service/app/domain/models.py) — toute autre valeur fait échouer
// l'insertion en base avec une erreur 500 non gérée.
const SERVICE_CATEGORIES = [
  { value: "Hammam", label: "Hammam / SPA" },
  { value: "Transfert", label: "Transfert" },
  { value: "Excursion", label: "Excursion" },
  { value: "Diner", label: "Dîner" },
  { value: "Cours_Cuisine", label: "Cours de cuisine" },
  { value: "Autre", label: "Autre" },
];
const OTA_NAMES = ["booking_com", "expedia", "airbnb", "direct_website"];

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

export default function EstablishmentsAdminPage() {
  const queryClient = useQueryClient();
  const isSuperAdmin = Boolean(useSessionStore((s) => s.claims)?.is_super_admin);
  const { data: establishments } = useQuery({
    queryKey: ["establishments"],
    queryFn: fetchEstablishments,
  });

  const [selectedEstablishmentId, setSelectedEstablishmentId] = useState<string>("");
  const [pendingRooms, setPendingRooms] = useState<RoomCreateInput[]>([]);
  const [draftRoom, setDraftRoom] = useState<RoomCreateInput>({
    numero: "",
    categorie: ROOM_CATEGORIES[0],
    floor: 0,
    capacity_adults: 2,
    capacity_children: 0,
  });
  const [editingRoom, setEditingRoom] = useState<Room | null>(null);

  const selectedEstablishment = (establishments ?? []).find((e) => e.id === selectedEstablishmentId);

  const { data: rooms } = useQuery({
    queryKey: ["establishment-rooms", selectedEstablishmentId],
    queryFn: () => fetchRooms(selectedEstablishmentId),
    enabled: Boolean(selectedEstablishmentId),
  });

  const { data: services } = useQuery({
    queryKey: ["establishment-services", selectedEstablishmentId],
    queryFn: () => fetchEstablishmentServices(selectedEstablishmentId),
    enabled: Boolean(selectedEstablishmentId),
  });

  const { data: otaMappings } = useQuery({
    queryKey: ["ota-mappings", selectedEstablishmentId],
    queryFn: () => fetchOtaMappings(selectedEstablishmentId),
    enabled: Boolean(selectedEstablishmentId),
  });

  const createEstablishmentMutation = useMutation({
    mutationFn: createEstablishment,
    onSuccess: (establishment) => {
      queryClient.invalidateQueries({ queryKey: ["establishments"] });
      setSelectedEstablishmentId(establishment.id);
      toast.success(`Établissement "${establishment.name}" créé`);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const updateEstablishmentMutation = useMutation({
    mutationFn: (input: { name?: string; address?: string; phone?: string; email?: string; is_active?: boolean }) =>
      updateEstablishment(selectedEstablishmentId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishments"] });
      toast.success("Établissement mis à jour");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const bulkRoomsMutation = useMutation({
    mutationFn: ({ id, rooms: r }: { id: string; rooms: RoomCreateInput[] }) => createRoomsBulk(id, r),
    onSuccess: () => {
      setPendingRooms([]);
      queryClient.invalidateQueries({ queryKey: ["establishment-rooms", selectedEstablishmentId] });
      toast.success("Chambres importées");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const updateRoomMutation = useMutation({
    mutationFn: ({ roomId, input }: { roomId: string; input: Partial<RoomCreateInput> }) =>
      updateRoom(selectedEstablishmentId, roomId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishment-rooms", selectedEstablishmentId] });
      toast.success("Chambre mise à jour");
      setEditingRoom(null);
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const deleteRoomMutation = useMutation({
    mutationFn: (roomId: string) => deleteRoom(selectedEstablishmentId, roomId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishment-rooms", selectedEstablishmentId] });
      toast.success("Chambre désactivée");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const createServiceMutation = useMutation({
    mutationFn: (input: { code: string; label: string; prix_ht: number; tva_rate: number; category: string }) =>
      createEstablishmentService(selectedEstablishmentId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["establishment-services", selectedEstablishmentId] });
      toast.success("Service ajouté");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  const upsertOtaMappingMutation = useMutation({
    mutationFn: (input: {
      ota_name: string;
      ota_property_id: string;
      ota_room_type_id?: string;
      internal_room_category?: string;
    }) => upsertOtaMapping(selectedEstablishmentId, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ota-mappings", selectedEstablishmentId] });
      toast.success("Mapping OTA enregistré");
    },
    onError: (error: Error) => toast.error(error.message),
  });

  function handleCreateEstablishment(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    createEstablishmentMutation.mutate({
      name: String(formData.get("name")),
      address: String(formData.get("address") || ""),
      city: String(formData.get("city") || "Marrakech"),
      country: String(formData.get("country") || "Maroc"),
      phone: String(formData.get("phone") || ""),
      email: String(formData.get("email") || ""),
      total_rooms: Number(formData.get("total_rooms")),
    });
    e.currentTarget.reset();
  }

  function addDraftRoom() {
    if (!draftRoom.numero) return;
    setPendingRooms((prev) => [...prev, draftRoom]);
    setDraftRoom({ ...draftRoom, numero: "" });
  }

  return (
    <div className="space-y-6">
      <PageHeader title="Établissements" description="Riads gérés, chambres, services et canaux OTA" />

      {isSuperAdmin && (
        <Card className="shadow-card">
          <CardHeader>
            <CardTitle>Nouvel établissement (Workflow K)</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleCreateEstablishment} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label>Nom</Label>
                <Input name="name" required placeholder="Riad Yasmine" />
              </div>
              <div>
                <Label>Nombre de chambres</Label>
                <Input name="total_rooms" type="number" min={1} required />
              </div>
              <div>
                <Label>Adresse</Label>
                <Input name="address" />
              </div>
              <div>
                <Label>Ville</Label>
                <Input name="city" defaultValue="Marrakech" />
              </div>
              <div>
                <Label>Téléphone</Label>
                <Input name="phone" />
              </div>
              <div>
                <Label>Email</Label>
                <Input name="email" type="email" />
              </div>
              <div className="sm:col-span-2">
                <Button type="submit" disabled={createEstablishmentMutation.isPending}>
                  Créer l&apos;établissement
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      <div>
        <Label>Établissement</Label>
        <Select value={selectedEstablishmentId} onValueChange={setSelectedEstablishmentId}>
          <SelectTrigger className="w-full sm:w-80">
            <SelectValue placeholder="Choisir un établissement" />
          </SelectTrigger>
          <SelectContent>
            {(establishments ?? []).map((est) => (
              <SelectItem key={est.id} value={est.id}>
                {est.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {!selectedEstablishmentId ? (
        <EmptyState title="Aucun établissement sélectionné" description="Choisissez un établissement ci-dessus pour gérer ses chambres, services et canaux." />
      ) : (
        <Tabs defaultValue="rooms" className="space-y-4">
          <div className="overflow-x-auto pb-1">
            <TabsList>
              <TabsTrigger value="rooms">Chambres</TabsTrigger>
              <TabsTrigger value="services">Services</TabsTrigger>
              <TabsTrigger value="ota">Canaux OTA</TabsTrigger>
              <TabsTrigger value="settings">Paramètres</TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="rooms" className="space-y-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Import de chambres</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label>Ajout manuel</Label>
                  <div className="grid grid-cols-2 gap-2 sm:grid-cols-6">
                    <div>
                      <Label htmlFor="draft-numero" className="text-xs font-normal text-muted-foreground">
                        Numéro
                      </Label>
                      <Input
                        id="draft-numero"
                        placeholder="Numéro"
                        value={draftRoom.numero}
                        onChange={(e) => setDraftRoom({ ...draftRoom, numero: e.target.value })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="draft-categorie" className="text-xs font-normal text-muted-foreground">
                        Catégorie
                      </Label>
                      <Select
                        value={draftRoom.categorie}
                        onValueChange={(v) => setDraftRoom({ ...draftRoom, categorie: v })}
                      >
                        <SelectTrigger id="draft-categorie">
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
                      <Label htmlFor="draft-floor" className="text-xs font-normal text-muted-foreground">
                        Étage
                      </Label>
                      <Input
                        id="draft-floor"
                        type="number"
                        placeholder="Étage"
                        value={draftRoom.floor}
                        onChange={(e) => setDraftRoom({ ...draftRoom, floor: Number(e.target.value) })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="draft-adultes" className="text-xs font-normal text-muted-foreground">
                        Adultes
                      </Label>
                      <Input
                        id="draft-adultes"
                        type="number"
                        placeholder="Adultes"
                        value={draftRoom.capacity_adults}
                        onChange={(e) => setDraftRoom({ ...draftRoom, capacity_adults: Number(e.target.value) })}
                      />
                    </div>
                    <div>
                      <Label htmlFor="draft-enfants" className="text-xs font-normal text-muted-foreground">
                        Enfants
                      </Label>
                      <Input
                        id="draft-enfants"
                        type="number"
                        placeholder="Enfants"
                        value={draftRoom.capacity_children}
                        onChange={(e) => setDraftRoom({ ...draftRoom, capacity_children: Number(e.target.value) })}
                      />
                    </div>
                    <Button variant="outline" onClick={addDraftRoom} className="self-end">
                      Ajouter à la liste
                    </Button>
                  </div>
                </div>

                {pendingRooms.length > 0 && (
                  <div className="space-y-2">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Numéro</TableHead>
                          <TableHead>Catégorie</TableHead>
                          <TableHead>Étage</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {pendingRooms.map((room, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{room.numero}</TableCell>
                            <TableCell>{room.categorie}</TableCell>
                            <TableCell>{room.floor}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                    <Button
                      disabled={bulkRoomsMutation.isPending}
                      onClick={() => bulkRoomsMutation.mutate({ id: selectedEstablishmentId, rooms: pendingRooms })}
                    >
                      Importer {pendingRooms.length} chambre(s)
                    </Button>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Chambres existantes ({(rooms ?? []).length})</CardTitle>
              </CardHeader>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Numéro</TableHead>
                    <TableHead>Catégorie</TableHead>
                    <TableHead>Étage</TableHead>
                    <TableHead>Capacité</TableHead>
                    <TableHead>Statut</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!rooms?.length ? (
                    <TableRow>
                      <TableCell colSpan={6} className="p-0">
                        <EmptyState className="border-none" title="Aucune chambre" description="Importez ou ajoutez des chambres ci-dessus." />
                      </TableCell>
                    </TableRow>
                  ) : (
                    rooms.map((room) =>
                      editingRoom?.id === room.id ? (
                        <InlineEditRow key={room.id} colSpan={6}>
                          <form
                            className="flex flex-wrap items-end gap-2"
                            onSubmit={(e) => {
                              e.preventDefault();
                              const fd = new FormData(e.currentTarget);
                              updateRoomMutation.mutate({
                                roomId: room.id,
                                input: {
                                  numero: String(fd.get("numero")),
                                  categorie: String(fd.get("categorie")),
                                  floor: Number(fd.get("floor")),
                                },
                              });
                            }}
                          >
                            <Input name="numero" defaultValue={room.numero} className="w-24" />
                            <Select name="categorie" defaultValue={room.categorie}>
                              <SelectTrigger className="w-44">
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
                            <Input name="floor" type="number" defaultValue={room.floor} className="w-20" />
                            <Button type="submit" size="sm" disabled={updateRoomMutation.isPending}>
                              Enregistrer
                            </Button>
                            <Button type="button" size="sm" variant="ghost" onClick={() => setEditingRoom(null)}>
                              Annuler
                            </Button>
                          </form>
                        </InlineEditRow>
                      ) : (
                        <TableRow key={room.id}>
                          <TableCell className="font-medium">{room.numero}</TableCell>
                          <TableCell>{room.categorie}</TableCell>
                          <TableCell>{room.floor}</TableCell>
                          <TableCell>
                            {room.capacity_adults}A + {room.capacity_children}E
                          </TableCell>
                          <TableCell>
                            <ActiveBadge active={room.is_active} />
                          </TableCell>
                          <TableCell className="flex justify-end gap-2">
                            <Button size="sm" variant="outline" onClick={() => setEditingRoom(room)}>
                              Modifier
                            </Button>
                            <Button
                              size="sm"
                              variant="ghost"
                              disabled={deleteRoomMutation.isPending}
                              onClick={() => deleteRoomMutation.mutate(room.id)}
                            >
                              Désactiver
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

          <TabsContent value="services" className="space-y-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Nouveau service (restaurant, transport, activité...)</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  className="grid grid-cols-1 gap-4 sm:grid-cols-3"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const fd = new FormData(e.currentTarget);
                    createServiceMutation.mutate({
                      code: String(fd.get("code")),
                      label: String(fd.get("label")),
                      prix_ht: Number(fd.get("prix_ht")),
                      tva_rate: 20,
                      category: String(fd.get("category")),
                    });
                    e.currentTarget.reset();
                  }}
                >
                  <div>
                    <Label>Code</Label>
                    <Input name="code" required placeholder="TRANSFER_AEROPORT" />
                  </div>
                  <div>
                    <Label>Libellé</Label>
                    <Input name="label" required />
                  </div>
                  <div>
                    <Label>Catégorie</Label>
                    <Select name="category" defaultValue={SERVICE_CATEGORIES[0].value}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {SERVICE_CATEGORIES.map((c) => (
                          <SelectItem key={c.value} value={c.value}>
                            {c.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Prix HT</Label>
                    <Input name="prix_ht" type="number" step="0.01" min={0.01} required />
                  </div>
                  <Button type="submit" disabled={createServiceMutation.isPending}>
                    Ajouter
                  </Button>
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
                    <TableHead>Prix TTC</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!services?.length ? (
                    <TableRow>
                      <TableCell colSpan={4} className="p-0">
                        <EmptyState className="border-none" title="Aucun service" description="Ajoutez un service ci-dessus." />
                      </TableCell>
                    </TableRow>
                  ) : (
                    services.map((s) => (
                      <TableRow key={s.id}>
                        <TableCell className="font-mono text-xs">{s.code}</TableCell>
                        <TableCell>{s.label}</TableCell>
                        <TableCell>{s.category}</TableCell>
                        <TableCell>{s.prix_ttc.toFixed(2)}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          <TabsContent value="ota" className="space-y-4">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Nouveau mapping OTA</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  className="grid grid-cols-1 gap-4 sm:grid-cols-4"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const fd = new FormData(e.currentTarget);
                    upsertOtaMappingMutation.mutate({
                      ota_name: String(fd.get("ota_name")),
                      ota_property_id: String(fd.get("ota_property_id")),
                      ota_room_type_id: String(fd.get("ota_room_type_id") || "") || undefined,
                      internal_room_category: String(fd.get("internal_room_category") || "") || undefined,
                    });
                    e.currentTarget.reset();
                  }}
                >
                  <div>
                    <Label>OTA</Label>
                    <Select name="ota_name" defaultValue={OTA_NAMES[0]}>
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {OTA_NAMES.map((o) => (
                          <SelectItem key={o} value={o}>
                            {o}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Property ID (OTA)</Label>
                    <Input name="ota_property_id" required />
                  </div>
                  <div>
                    <Label>Room type ID (OTA)</Label>
                    <Input name="ota_room_type_id" />
                  </div>
                  <div>
                    <Label>Catégorie interne</Label>
                    <Select name="internal_room_category">
                      <SelectTrigger>
                        <SelectValue placeholder="Optionnel" />
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
                  <Button type="submit" disabled={upsertOtaMappingMutation.isPending}>
                    Enregistrer
                  </Button>
                </form>
              </CardContent>
            </Card>
            <Card className="shadow-card">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>OTA</TableHead>
                    <TableHead>Property ID</TableHead>
                    <TableHead>Room type ID</TableHead>
                    <TableHead>Catégorie interne</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {!otaMappings?.length ? (
                    <TableRow>
                      <TableCell colSpan={4} className="p-0">
                        <EmptyState className="border-none" title="Aucun mapping" description="Ajoutez un mapping OTA ci-dessus." />
                      </TableCell>
                    </TableRow>
                  ) : (
                    otaMappings.map((m) => (
                      <TableRow key={m.id}>
                        <TableCell>
                          <Badge variant="outline">{m.ota_name}</Badge>
                        </TableCell>
                        <TableCell>{m.ota_property_id}</TableCell>
                        <TableCell>{m.ota_room_type_id ?? "—"}</TableCell>
                        <TableCell>{m.internal_room_category ?? "—"}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </Card>
          </TabsContent>

          <TabsContent value="settings">
            <Card className="shadow-card">
              <CardHeader>
                <CardTitle>Paramètres de l&apos;établissement</CardTitle>
              </CardHeader>
              <CardContent>
                <form
                  className="grid grid-cols-1 gap-4 sm:grid-cols-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    const fd = new FormData(e.currentTarget);
                    updateEstablishmentMutation.mutate({
                      name: String(fd.get("name")),
                      address: String(fd.get("address") || ""),
                      phone: String(fd.get("phone") || ""),
                      email: String(fd.get("email") || ""),
                      is_active: fd.get("is_active") === "on",
                    });
                  }}
                >
                  <div>
                    <Label>Nom</Label>
                    <Input name="name" defaultValue={selectedEstablishment?.name} required />
                  </div>
                  <div>
                    <Label>Adresse</Label>
                    <Input name="address" defaultValue={selectedEstablishment?.address ?? ""} />
                  </div>
                  <div>
                    <Label>Téléphone</Label>
                    <Input name="phone" defaultValue={selectedEstablishment?.phone ?? ""} />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input name="email" type="email" defaultValue={selectedEstablishment?.email ?? ""} />
                  </div>
                  <div className="flex items-center gap-2 sm:col-span-2">
                    <input
                      id="is_active"
                      name="is_active"
                      type="checkbox"
                      className="size-4 accent-primary"
                      defaultChecked={selectedEstablishment?.is_active}
                    />
                    <Label htmlFor="is_active">Établissement actif</Label>
                  </div>
                  <div className="sm:col-span-2">
                    <Button type="submit" disabled={updateEstablishmentMutation.isPending}>
                      Enregistrer
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}
    </div>
  );
}
