import { CircuitBoard, Cpu, Gauge, type LucideIcon } from "lucide-react";
import Badge from "../../components/Badge";
import Button from "../../components/Button";
import { buttonClassName } from "../../components/Button/buttonClassName";
import Card from "../../components/Card";
import { isHttpUrl } from "../../utils/isHttpUrl";
import PrefetchLink from "../../components/PrefetchLink";
import type { Hardware, HardwareCategory, Loan } from "../../types/hardware";
import {
  HARDWARE_CATEGORY_LABELS,
  HARDWARE_STATUS_LABELS,
  HARDWARE_STATUS_TONES,
} from "../../utils/hardwareLabels";
import { cardActionId } from "./cardActionId";

const CATEGORY_ICONS: Record<HardwareCategory, LucideIcon> = {
  MEASUREMENT: Gauge,
  MICROCONTROLLER: Cpu,
  COMPONENT: CircuitBoard,
};

interface HardwareCardProps {
  item: Hardware;
  // The viewer's pending or approved loan for this item, if any.
  activeLoan: Loan | undefined;
  onRequest: () => void;
}

// The action matches what the backend would allow, so nobody fills in a
// request that is bound to be refused.
function CardAction({ item, activeLoan, onRequest }: HardwareCardProps) {
  if (activeLoan) {
    return (
      <PrefetchLink id={cardActionId(item.id)} to="/loans" className={buttonClassName("secondary", "w-full")}>
        {activeLoan.status === "PENDING" ? "Requested · view in My Loans" : "On loan to you · My Loans"}
      </PrefetchLink>
    );
  }
  if (item.status === "MAINTENANCE") {
    return <p className="py-3 text-center text-sm text-white/50">Can't be borrowed while under maintenance.</p>;
  }
  if (item.available_quantity < 1) {
    return <p className="py-3 text-center text-sm text-white/50">None available right now.</p>;
  }
  return (
    <Button onClick={onRequest} className="w-full">
      Request loan
    </Button>
  );
}

export function HardwareCard(props: HardwareCardProps) {
  const { item } = props;
  const Icon = CATEGORY_ICONS[item.category];

  return (
    <Card as="article" className="flex h-full flex-col gap-4">
      {isHttpUrl(item.image_url) && (
        <img
          src={item.image_url}
          alt=""
          width={480}
          height={270}
          loading="lazy"
          decoding="async"
          className="-mx-5 -mt-5 aspect-video w-[calc(100%+2.5rem)] max-w-none rounded-t-2xl object-cover"
        />
      )}
      <div className="flex items-start gap-3">
        <span
          aria-hidden="true"
          className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-sees-glass text-sees-mint"
        >
          <Icon className="size-5" />
        </span>
        <div className="min-w-0">
          <h2 className="text-lg font-semibold wrap-anywhere text-white">{item.name}</h2>
          <p className="text-sm text-white/50">{HARDWARE_CATEGORY_LABELS[item.category]}</p>
        </div>
      </div>

      {item.description && <p className="line-clamp-3 text-sm wrap-anywhere text-white/70">{item.description}</p>}

      <div className="mt-auto space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2 text-sm">
          <span className="text-white/80">
            <span className="font-semibold text-white">{item.available_quantity}</span> of {item.quantity} available
          </span>
          <Badge tone={HARDWARE_STATUS_TONES[item.status]}>{HARDWARE_STATUS_LABELS[item.status]}</Badge>
        </div>
        <p className="font-mono text-xs wrap-anywhere text-white/40">Serial {item.serial_number}</p>
        <CardAction {...props} />
      </div>
    </Card>
  );
}
