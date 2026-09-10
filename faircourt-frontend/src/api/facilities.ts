import { apiRequest } from "./client";
import { loadFromCache, saveToCache } from "../utils/offlineCache";

export type Facility = {
  id: number;
  slug: string;
  name: string;
  category: string;
  description: string | null;
  icon: string;
  priority: number;
  is_reservable: boolean;
  opening_hour: number;
  closing_hour: number;
  slot_duration_minutes: number;
};

export async function getFacilities() {
  const cacheKey = "faircourt_cache_facilities";
  try {
    const data = await apiRequest<Facility[]>("/facilities");
    saveToCache(cacheKey, data);
    return data;
  } catch (error) {
    const cached = loadFromCache<Facility[]>(cacheKey);
    if (cached) return cached;
    throw error;
  }
}
