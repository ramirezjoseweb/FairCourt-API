import { adminApiRequest } from "./client";

export type AdminTokenResponse = {
  access_token: string;
  token_type: string;
  expires_at: string;
};

export type AdminMe = {
  id: number;
  email: string;
  role: "platform_admin";
};

export type CommunitySummary = {
  id: number;
  slug: string;
  name: string;
  timezone: string;
  is_active: boolean;
  household_count: number;
  facility_count: number;
};

export type CommunityPolicy = {
  community_id: number;
  booking_window_days: number;
  max_active_reservations_per_day: number;
  max_active_reservations_per_week: number;
  cancellation_limit_hours: number;
  checkin_window_minutes: number;
  max_strikes: number;
  suspension_days: number;
  max_active_waitlists_per_week: number;
  prime_time_start_hour: number;
  prime_time_end_hour: number;
  cooldown_days: number;
  unlock_voting_enabled: boolean;
  unlock_voting_hours: number;
  unlock_min_yes_votes: number;
};

export type BasicPolicyInput = Pick<
  CommunityPolicy,
  | "booking_window_days"
  | "max_active_reservations_per_day"
  | "max_active_reservations_per_week"
  | "cancellation_limit_hours"
>;

export type AdminFacility = {
  id: number;
  community_id: number;
  slug: string;
  name: string;
  category: string;
  description: string | null;
  icon: string;
  priority: number;
  is_active: boolean;
  is_reservable: boolean;
  opening_hour: number;
  closing_hour: number;
  slot_duration_minutes: number;
};

export type AdminFacilityInput = Omit<
  AdminFacility,
  "id" | "community_id"
>;

export type AdminAuditEntry = {
  id: number;
  event: string;
  household_id?: number | null;
  user_id?: number | null;
  reservation_id?: number | null;
  metadata_json?: string | null;
  created_at: string;
};

export function requestAdminOtp(email: string) {
  return adminApiRequest<{ message: string }>("/admin/auth/request-otp", {
    method: "POST",
    body: JSON.stringify({ email }),
  });
}

export function verifyAdminOtp(email: string, otp: string) {
  return adminApiRequest<AdminTokenResponse>("/admin/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ email, otp }),
  });
}

export function getAdminMe() {
  return adminApiRequest<AdminMe>("/admin/me");
}

export function getAdminCommunities() {
  return adminApiRequest<CommunitySummary[]>("/admin/communities");
}

export function selectAdminCommunity(communityId: number) {
  return adminApiRequest<CommunitySummary>(
    `/admin/communities/${communityId}/select`,
    { method: "POST" },
  );
}

export function getAdminCommunityPolicy(communityId: number) {
  return adminApiRequest<CommunityPolicy>(
    `/admin/communities/${communityId}/policy`,
  );
}

export function updateAdminBasicPolicy(
  communityId: number,
  policy: BasicPolicyInput,
) {
  return adminApiRequest<CommunityPolicy>(
    `/admin/communities/${communityId}/policy/basic`,
    { method: "PUT", body: JSON.stringify(policy) },
  );
}

export function getAdminFacilities(communityId: number) {
  return adminApiRequest<AdminFacility[]>(
    `/admin/communities/${communityId}/facilities`,
  );
}

export function createAdminFacility(
  communityId: number,
  facility: AdminFacilityInput,
) {
  return adminApiRequest<AdminFacility>(
    `/admin/communities/${communityId}/facilities`,
    { method: "POST", body: JSON.stringify(facility) },
  );
}

export function updateAdminFacility(
  communityId: number,
  facilityId: number,
  facility: AdminFacilityInput,
) {
  return adminApiRequest<AdminFacility>(
    `/admin/communities/${communityId}/facilities/${facilityId}`,
    { method: "PUT", body: JSON.stringify(facility) },
  );
}

export function getAdminCommunityAudit(communityId: number) {
  return adminApiRequest<AdminAuditEntry[]>(
    `/admin/communities/${communityId}/audit`,
  );
}
