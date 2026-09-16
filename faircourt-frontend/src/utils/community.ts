const DEFAULT_COMMUNITY_SLUG = "faircourt";

export function getCommunitySlug(): string {
  const pathMatch = window.location.pathname.match(/^\/c\/([^/]+)/);
  const configured = import.meta.env.VITE_COMMUNITY_SLUG as string | undefined;
  return decodeURIComponent(
    pathMatch?.[1] ?? configured ?? DEFAULT_COMMUNITY_SLUG,
  )
    .trim()
    .toLowerCase();
}
