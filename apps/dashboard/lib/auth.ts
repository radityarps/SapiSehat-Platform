export const tokenKey = 'sapisehat_agency_token';
export const sessionEventName = 'sapisehat-agency-session-changed';

export function getAgencyToken() {
  if (typeof window === 'undefined') return '';
  return localStorage.getItem(tokenKey) ?? '';
}

export function setAgencyToken(token: string) {
  if (typeof window === 'undefined') return;
  localStorage.setItem(tokenKey, token);
  document.cookie = `sapisehat_agency_token=${token}; path=/; SameSite=Lax`;
  window.dispatchEvent(new Event(sessionEventName));
}

export function clearAgencyToken() {
  if (typeof window === 'undefined') return;
  localStorage.removeItem(tokenKey);
  document.cookie = 'sapisehat_agency_token=; path=/; Max-Age=0; SameSite=Lax';
  window.dispatchEvent(new Event(sessionEventName));
}
