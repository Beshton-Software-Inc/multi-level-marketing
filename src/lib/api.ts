import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const apiClient = axios.create({ baseURL: BASE_URL })

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('wwl_mlm_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

apiClient.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('wwl_mlm_token')
      localStorage.removeItem('wwl_mlm_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Types ──────────────────────────────────────────────

export interface AffiliateUser {
  id: number
  name: string
  email: string
  referral_code: string
  referred_by_id: number | null
  status: string
  total_earnings: string
  is_admin: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user: AffiliateUser
}

export interface AffiliateStats {
  direct_referrals: number
  team_size: number
  total_earnings: string
  pending_earnings: string
  this_month_earnings: string
}

export interface Commission {
  id: number
  earner_id: number
  source_id: number | null
  source_name: string | null
  amount: string
  tier: number
  description: string | null
  status: string
  created_at: string
}

export interface TeamMember {
  id: number
  name: string
  email: string
  referral_code: string
  status: string
  total_earnings: string
  created_at: string
  depth: number
  direct_referrals: number
}

export interface PayoutRequest {
  id: number
  affiliate_id: number
  affiliate_name?: string
  affiliate_email?: string
  amount: string
  status: string
  payment_method: string | null
  payment_details: string | null
  admin_notes: string | null
  created_at: string
  processed_at: string | null
}

export interface AdminStats {
  total_affiliates: number
  active_affiliates: number
  total_commissions: string
  pending_payouts_amount: string
  pending_payouts_count: number
}

export interface SimulatedCommission {
  earner_name: string
  earner_email: string
  tier: number
  amount: string
}

export interface SimulateSubscriptionResult {
  message: string
  buyer_name: string
  buyer_email: string
  subscription_amount: string
  commissions: SimulatedCommission[]
}

// ── Auth API ───────────────────────────────────────────

export const authApi = {
  register: (data: { name: string; email: string; password: string; referral_code?: string }) =>
    apiClient.post<TokenResponse>('/api/auth/register', data).then((r) => r.data),
  login: (data: { email: string; password: string }) =>
    apiClient.post<TokenResponse>('/api/auth/login', data).then((r) => r.data),
}

// ── Affiliate API ──────────────────────────────────────

export const affiliateApi = {
  getMe: () => apiClient.get<AffiliateUser>('/api/affiliate/me').then((r) => r.data),
  getStats: () => apiClient.get<AffiliateStats>('/api/affiliate/stats').then((r) => r.data),
  getTeam: () => apiClient.get<{ members: TeamMember[] }>('/api/affiliate/team').then((r) => r.data),
  getEarnings: () =>
    apiClient.get<{ earnings: Commission[] }>('/api/affiliate/earnings').then((r) => r.data),
  requestPayout: (data: { amount: number; payment_method: string; payment_details: string }) =>
    apiClient.post<PayoutRequest>('/api/affiliate/payout', data).then((r) => r.data),
  getPayouts: () =>
    apiClient.get<{ payouts: PayoutRequest[] }>('/api/affiliate/payouts').then((r) => r.data),
}

// ── Admin API ──────────────────────────────────────────

export const adminApi = {
  getStats: () => apiClient.get<AdminStats>('/api/admin/stats').then((r) => r.data),
  getAffiliates: () =>
    apiClient.get<{ affiliates: AffiliateUser[] }>('/api/admin/affiliates').then((r) => r.data),
  getPayouts: () =>
    apiClient.get<{ payouts: PayoutRequest[] }>('/api/admin/payouts').then((r) => r.data),
  updatePayout: (id: number, data: { status: string; admin_notes?: string }) =>
    apiClient.put<PayoutRequest>(`/api/admin/payouts/${id}`, data).then((r) => r.data),
  addCommission: (data: { affiliate_email: string; amount: number; description: string }) =>
    apiClient.post('/api/admin/commission', data).then((r) => r.data),
  simulateSubscription: (data: { affiliate_email: string; subscription_amount: number }) =>
    apiClient.post<SimulateSubscriptionResult>('/api/admin/simulate-subscription', data).then((r) => r.data),
}
