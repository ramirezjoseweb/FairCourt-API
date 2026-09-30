export function getCommunitySlug(): string | null {
  const pathMatch = window.location.pathname.match(/^\/c\/([^/]+)/);
  return pathMatch ? decodeURIComponent(pathMatch[1]).trim().toLowerCase() : null;
}
