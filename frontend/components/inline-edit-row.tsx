import { TableCell, TableRow } from "@/components/ui/table";
import { cn } from "@/lib/utils";

interface InlineEditRowProps {
  colSpan: number;
  children: React.ReactNode;
  className?: string;
}

/**
 * Styled container for the "form replaces the row" pattern used across
 * establishments/partners/pricing/reservations-customers tables. Each page
 * keeps owning its own editing state and save/cancel mutations — this only
 * standardizes the visual shell around the swapped-in form.
 */
export function InlineEditRow({ colSpan, children, className }: InlineEditRowProps) {
  return (
    <TableRow className="bg-accent/40 hover:bg-accent/40">
      <TableCell colSpan={colSpan} className="p-4">
        <div className={cn("flex flex-wrap items-end gap-3", className)}>{children}</div>
      </TableCell>
    </TableRow>
  );
}
