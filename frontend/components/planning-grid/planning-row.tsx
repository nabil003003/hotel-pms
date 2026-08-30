"use client";

import { useMemo } from "react";
import type { Room } from "@/lib/api-clients/establishment";
import type { Booking, Customer } from "@/lib/api-clients/reservation";
import { barGeometry, ROOM_COL_WIDTH, ROW_HEIGHT } from "./geometry";
import { PlanningCell } from "./planning-cell";
import { PlanningBar } from "./planning-bar";

interface PlanningRowProps {
  room: Room;
  days: string[];
  dayIndexByIso: Map<string, number>;
  bookings: Booking[];
  customersById: Map<string, Customer>;
  todayIso: string;
  activeForShift: Set<string>;
  onBookingClick?: (booking: Booking) => void;
}

export function PlanningRow({
  room,
  days,
  dayIndexByIso,
  bookings,
  customersById,
  todayIso,
  activeForShift,
  onBookingClick,
}: PlanningRowProps) {
  const visibleBookings = useMemo(() => {
    return bookings.map((b) => {
      const geom = barGeometry(b.check_in_date, b.check_out_date, days, dayIndexByIso);
      return { booking: b, geom };
    }).filter((item): item is { booking: Booking; geom: NonNullable<typeof item.geom> } => item.geom !== null);
  }, [bookings, days, dayIndexByIso]);

  return (
    <div className="flex" style={{ height: `${ROW_HEIGHT}px` }}>
      {/* Sticky Room Header Column */}
      <div
        style={{ width: `${ROOM_COL_WIDTH}px`, height: `${ROW_HEIGHT}px` }}
        className="sticky left-0 z-20 flex flex-col justify-center border-b border-r border-border bg-card px-3 shadow-[2px_0_5px_-2px_rgba(0,0,0,0.05)]"
      >
        <div className="flex items-center justify-between">
          <span className="font-semibold text-sm text-foreground">{room.numero}</span>
          <span className="text-[10px] text-muted-foreground font-mono">Étage {room.floor}</span>
        </div>
        <span className="truncate text-[11px] text-muted-foreground">{room.categorie}</span>
      </div>

      {/* Grid Cells & Overlay Booking Bars Track */}
      <div className="relative flex">
        {days.map((dateIso) => (
          <PlanningCell
            key={dateIso}
            roomId={room.id}
            dateIso={dateIso}
            isToday={dateIso === todayIso}
          />
        ))}

        {visibleBookings.map(({ booking, geom }) => {
          const customer = customersById.get(booking.customer_id);
          const customerName = customer
            ? `${customer.first_name} ${customer.last_name}`
            : undefined;
          const isDraggable = activeForShift.has(booking.status);

          return (
            <PlanningBar
              key={booking.id}
              booking={booking}
              customerName={customerName}
              geom={geom}
              isDraggable={isDraggable}
              onClick={() => onBookingClick?.(booking)}
            />
          );
        })}
      </div>
    </div>
  );
}
