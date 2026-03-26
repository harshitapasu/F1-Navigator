/**
 * API Client for F1 Navigator Backend
 * All requests include JWT token from localStorage
 */

const API_URL = process.env.NEXT_PUBLIC_API_URL || ""

function getToken(): string | null {
  if (typeof window === "undefined") return null
  return localStorage.getItem("token")
}

function getAuthHeader(): HeadersInit {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ── Auth API ────────────────────────────────────────────────────────────────

export async function signUp(email: string, password: string, name: string) {
  const res = await fetch(`${API_URL}/api/auth/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function login(email: string, password: string) {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function getMe() {
  const res = await fetch(`${API_URL}/api/auth/me`, {
    headers: getAuthHeader(),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

// ── Profile API ─────────────────────────────────────────────────────────────

export interface UserData {
  id: string
  email: string
  name: string
  university?: string
  major?: string
  degree_level?: string
  year_of_study?: string
  visa_status?: string
  country_of_origin?: string
  country_of_citizenship?: string
  graduation_date?: string
  middle_name?: string
  date_of_birth?: string
  birth_city?: string
  birth_country?: string
  sex?: string
  marital_status?: string
  phone_number?: string
  mailing_street?: string
  mailing_apt?: string
  mailing_city?: string
  mailing_state?: string
  mailing_zip?: string
  sevis_number?: string
}

export async function updateProfile(data: Partial<UserData>) {
  const res = await fetch(`${API_URL}/api/profile`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify(data),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const profileApi = { updateProfile, getMe }

// ── Chat API ────────────────────────────────────────────────────────────────

export async function chatStream(
  message: string,
  history: Array<{ role: string; content: string }> = []
): Promise<ReadableStream> {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ message, history }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.body!
}

export interface SourceItem {
  title: string
  url: string
  section: string
  category: string
}

// ── Documents API ───────────────────────────────────────────────────────────

export interface DocumentRecord {
  id: string
  name: string
  doc_type: string
  file_size: number
  created_at?: string
}

export async function listDocuments(): Promise<{ documents: DocumentRecord[] }> {
  const res = await fetch(`${API_URL}/api/documents`, {
    headers: getAuthHeader(),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function uploadDocument(
  name: string,
  doc_type: string,
  file_data: string,
  file_size: number
): Promise<DocumentRecord> {
  const res = await fetch(`${API_URL}/api/documents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ name, doc_type, file_data, file_size }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function deleteDocument(doc_id: string) {
  const res = await fetch(`${API_URL}/api/documents/${doc_id}`, {
    method: "DELETE",
    headers: getAuthHeader(),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const documentsApi = { listDocuments, uploadDocument, deleteDocument }

// ── Meetings API ────────────────────────────────────────────────────────────

export interface MeetingRecord {
  id: string
  name: string
  email: string
  preferred_date?: string
  preferred_time?: string
  topic: string
  details?: string
  status: string
  created_at?: string
}

export async function listMeetings(): Promise<{ meetings: MeetingRecord[] }> {
  const res = await fetch(`${API_URL}/api/meetings`, {
    headers: getAuthHeader(),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function createMeeting(
  name: string,
  email: string,
  preferred_date: string,
  preferred_time: string,
  topic: string,
  details: string
): Promise<MeetingRecord> {
  const res = await fetch(`${API_URL}/api/meetings`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({
      name,
      email,
      preferred_date,
      preferred_time,
      topic,
      details,
    }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const meetingsApi = { listMeetings, createMeeting }

// ── Notifications API ───────────────────────────────────────────────────────

export async function getNotificationPrefs(): Promise<{ guides: string[] }> {
  const res = await fetch(`${API_URL}/api/notifications`, {
    headers: getAuthHeader(),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export async function updateNotificationPrefs(guides: string[]) {
  const res = await fetch(`${API_URL}/api/notifications`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
    },
    body: JSON.stringify({ guides }),
  })
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const notificationsApi = {
  getNotificationPrefs,
  updateNotificationPrefs,
}

// ── News API ────────────────────────────────────────────────────────────────

export interface NewsArticle {
  id: string
  title: string
  description: string
  url: string
  source: string
  published_at: string
  impact_type: "positive" | "negative" | "neutral"
}

export async function getNews(): Promise<{ articles: NewsArticle[] }> {
  const res = await fetch(`${API_URL}/api/news`)
  if (!res.ok) throw new Error(await res.text())
  return res.json()
}

export const newsApi = { getNews }

// ── Auth API namespace ──────────────────────────────────────────────────────

export const authApi = { signUp, login, getMe }
