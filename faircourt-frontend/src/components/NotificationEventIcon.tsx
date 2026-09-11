import { tone } from "../utils/format";
import { Icon } from "./ui";

export function NotificationEventIcon({ type }: { type: string }) {
  return (
    <span className={`event-icon event-${tone(type)}`}>
      <Icon
        name={
          type.includes("WAITLIST")
            ? "users"
            : type.includes("SUSPENDED") || type === "NO_SHOW"
              ? "alert"
              : "bell"
        }
      />
    </span>
  );
}
