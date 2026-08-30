"use client";

import { useMemo, useState } from "react";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import type { Room } from "@/lib/api-clients/establishment";
import type { Booking, Customer } from "@/lib/api-clients/reservation";
import { addDaysIso } from "@/lib/date-utils";
import {
  barGeometry,
  buildDayRange,
  DAY_WIDTH,
  ROOM_COL_WIDTH,
  ROW_HEIGHT,
  sortRooms,
} from "./geometry";
import { PlanningRow } from "./planning-row";
import { PlanningBar } from "./planning-bar";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

const ACTIVE_FOR_SHIFT = new Set([
  "status_option",
  "status_confirmed",
  "status_voucher",
  "status_checked_in",
]);

function nightsBetween(a: string, b: string): number {
  return Math.round((Date.parse(`${b}T00:00:00Z`) - Date.parse(`${a}T00:00:00Z`)) / 86_400_000);
}

function formatDateHeader(isoDate: string): { weekday: string; dateStr: string } {
  const d = new Date(`${isoDate}T00:00:00Z`);
  const weekday = d.toLocaleDateString("fr-FR", { weekday: "short", timeZone: "UTC" });
  const dateStr = d.toLocaleDateString("fr-FR", { day: "2-digit", month: "2-digit", timeZone: "UTC" });
  return { weekday: weekday.replace(".", ""), dateStr };
}

export interface ShiftBookingParams {
  booking: Booking;
  targetRoomId: string;
  targetCheckInDate: string;
  targetCheckOutDate: string;
}

interface PlanningGridProps {
  rooms: Room[];
  bookings: Booking[];
  customers: Customer[];
  fromDate: string;
  toDate: string;
  businessDate: string;
  onShiftBooking: (params: ShiftBookingParams) => void;
  onBookingClick?: (booking: Booking) => void;
}

export function PlanningGrid({
  rooms,
  bookings,
  customers,
  fromDate,
  toDate,
  businessDate,
  onShiftBooking,
  onBookingClick,
}: PlanningGridProps) {
  const [activeBooking, setActiveBooking] = useState<Booking | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    })
  );

  const days = useMemo(() => buildDayRange(fromDate, toDate), [fromDate, toDate]);
  const dayIndexByIso = useMemo(
    () => new Map(days.map((d, i) => [d, i])),
    [days]
  );
  const sortedRooms = useMemo(() => sortRooms(rooms), [rooms]);

  const customersById = useMemo(
    () => new Map(customers.map((c) => [c.id, c])),
    [customers]
  );

  const bookingsByRoomId = useMemo(() => {
    const map = new Map<string, Booking[]>();
    for (const b of bookings) {
      const list = map.get(b.room_id) ?? [];
      list.push(b);
      map.set(b.room_id, list);
    }
    return map;
  }, [bookings]);

  function handleDragStart(event: DragStartEvent) {
    const booking = event.active.data.current?.booking as Booking | undefined;
    if (booking) {
      setActiveBooking(booking);
    }
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveBooking(null);
    const { active, over } = event;
    if (!over) return;

    const booking = active.data.current?.booking as Booking | undefined;
    const targetRoomId = over.data.current?.roomId as string | undefined;
    const targetCheckInDate = over.data.current?.dateIso as string | undefined;

    if (!booking || !targetRoomId || !targetCheckInDate) return;

    // Direct match: dropped on the exact same room and start date
    if (booking.room_id === targetRoomId && booking.check_in_date === targetCheckInDate) {
      return;
    }

    const nights = Math.max(1, nightsBetween(booking.check_in_date, booking.check_out_date));
    const targetCheckOutDate = addDaysIso(targetCheckInDate, nights);

    onShiftBooking({
      booking,
      targetRoomId,
      targetCheckInDate,
      targetCheckOutDate,
    });
  }

  const activeGeom = activeBooking
    ? barGeometry(activeBooking.check_in_date, activeBooking.check_out_date, days, dayIndexByIso)
    : null;

  const activeCustomer = activeBooking ? customersById.get(activeBooking.customer_id) : undefined;
  const activeCustomerName = activeCustomer
    ? `${activeCustomer.first_name} ${activeCustomer.last_name}`
    : undefined;

  return (
    <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
      <div className="w-full overflow-auto max-h-[750px] rounded-xl border border-border bg-card shadow-sm">
        <div className="min-w-max">
            {/* Header row */}
            <div className="sticky top-0 z-30 flex border-b border-border bg-muted/90 backdrop-blur-sm">
              {/* Top-left corner cell */}
              <div
                style={{ width: `${ROOM_COL_WIDTH}px` }}
                className="sticky left-0 z-40 flex items-center justify-between border-r border-border bg-muted px-3 py-2 font-semibold text-xs text-muted-foreground shadow-[2px_0_5px_-2px_rgba(0,0,0,0.1)]"
              >
                <span>Chambre</span>
                <span className="text-[10px] font-normal text-muted-foreground/80">({rooms.length})</span>
              </div>

              {/* Day headers */}
              <div className="flex">
                {days.map((dateIso) => {
                  const { weekday, dateStr } = formatDateHeader(dateIso);
                  const isToday = dateIso === businessDate;
                  return (
                    <div
                      key={dateIso}
                      style={{ width: `${DAY_WIDTH}px` }}
                      className={cn(
                        "flex flex-col items-center justify-center border-r border-border/60 py-2 text-xs font-medium border-b-2 border-b-transparent",
                        isToday && "bg-primary/10 border-b-primary font-bold text-primary"
                      )}
                    >
                      <span className="capitalize text-[10px] text-muted-foreground">{weekday}</span>
                      <span>{dateStr}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Room rows */}
            <div className="divide-y divide-border/40">
              {sortedRooms.map((room) => (
                <PlanningRow
                  key={room.id}
                  room={room}
                  days={days}
                  dayIndexByIso={dayIndexByIso}
                  bookings={bookingsByRoomId.get(room.id) ?? []}
                  customersById={customersById}
                  todayIso={businessDate}
                  activeForShift={ACTIVE_FOR_SHIFT}
                  onBookingClick={onBookingClick}
                />
              ))}

              {sortedRooms.length === 0 && (
                <div className="p-8 text-center text-sm text-muted-foreground">
                  Aucune chambre enregistrée pour cet établissement.
                </div>
              )}
            </div>
          </div>
        </div>

      {/* Floating Drag Overlay */}
      <DragOverlay>
        {activeBooking && activeGeom ? (
          <PlanningBar
            booking={activeBooking}
            customerName={activeCustomerName}
            geom={activeGeom}
            isOverlay={true}
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
