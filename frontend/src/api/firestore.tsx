// Data fetching layer that uses Firestore with backend fallback
// This replaces the bucket-based storage with Firestore

import { del, get, set } from 'idb-keyval';
import { BACKEND_URL } from '../constants';
import { log, round } from '../utils';
import {
  fetchTeams,
  fetchTeamYears,
  fetchTeamYear,
  fetchTeamAllYears,
  fetchEvents,
  fetchEvent,
  fetchEventMatches,
  fetchTeamMatches,
  fetchYear,
  fetchEventRankings,
  fetchTeam,
} from '../firebase/queries';

export const version = 'v3';

// Cache helpers
async function setWithExpiry(key: string, value: any, ttl: number) {
  const now = new Date();
  try {
    await set(`${key}_expiry`, now.getTime() + 1000 * ttl);
    await set(key, value);
  } catch (e: any) {
    log('Error setting cache', e);
  }
}

async function getWithExpiry(key: string) {
  const expiry = await get(`${key}_expiry`);
  if (!expiry) return null;
  const now = new Date();
  if (now.getTime() > expiry) {
    await del(`${key}_expiry`);
    await del(key);
    return null;
  }
  return get(key);
}

// Check if Firebase is configured
function isFirebaseConfigured(): boolean {
  return !!(
    process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID &&
    process.env.NEXT_PUBLIC_FIREBASE_API_KEY
  );
}

// Generic query function with caching
async function cachedQuery<T>(
  cacheKey: string,
  firebaseQuery: () => Promise<T>,
  backendPath: string,
  expiry: number = 300 // 5 minutes default
): Promise<T | null> {
  // Check cache first
  const cached = await getWithExpiry(cacheKey);
  if (cached) {
    log(`Used Local Storage: ${cacheKey}`);
    return cached as T;
  }

  const start = performance.now();

  // Try Firestore first if configured
  if (isFirebaseConfigured()) {
    try {
      const result = await firebaseQuery();
      log(`${cacheKey} (firestore) took ${round(performance.now() - start, 0)}ms`);
      if (result && (Array.isArray(result) ? result.length > 0 : true)) {
        await setWithExpiry(cacheKey, result, expiry);
        return result;
      }
    } catch (error) {
      log(`Firestore error for ${cacheKey}, falling back to backend`, error);
    }
  }

  // Fall back to backend
  try {
    const res = await fetch(`${BACKEND_URL}${backendPath}`, {
      next: { revalidate: 0 },
    });
    log(`${backendPath} (backend) took ${round(performance.now() - start, 0)}ms`);
    if (res.ok) {
      const data = await res.json();
      await setWithExpiry(cacheKey, data, expiry);
      return data;
    }
  } catch (error) {
    log(`Backend error for ${backendPath}`, error);
  }

  return null;
}

// API Functions

export async function getAllTeams(): Promise<any[]> {
  const result = await cachedQuery(
    `teams_all_${version}`,
    fetchTeams,
    '/v3/site/teams/all',
    3600 // 1 hour cache
  );
  return result || [];
}

export async function getTeam(teamNum: number): Promise<any | null> {
  return cachedQuery(
    `team_${teamNum}_${version}`,
    () => fetchTeam(teamNum),
    `/v3/site/teams/${teamNum}`,
    3600
  );
}

export async function getYearTeamYears(
  year: number,
  limitCount?: number
): Promise<{ year: any; team_years: any[] }> {
  const cacheKey = limitCount
    ? `team_years_${year}_${limitCount}_${version}`
    : `team_years_${year}_all_${version}`;

  const backendPath = limitCount
    ? `/v3/site/team_years/${year}?limit=${limitCount}&metric=epa`
    : `/v3/site/team_years/${year}`;

  const result = await cachedQuery(
    cacheKey,
    async () => {
      const [teamYears, yearData] = await Promise.all([
        fetchTeamYears(year, limitCount),
        fetchYear(year),
      ]);
      return { year: yearData, team_years: teamYears };
    },
    backendPath,
    year === new Date().getFullYear() ? 60 : 3600
  );

  return result || { year: null, team_years: [] };
}

export async function getTeamYear(
  teamNum: number,
  year: number
): Promise<any | null> {
  return cachedQuery(
    `team_year_${teamNum}_${year}_${version}`,
    () => fetchTeamYear(teamNum, year),
    `/v3/site/team_year/${year}/${teamNum}`,
    300
  );
}

export async function getTeamAllYears(teamNum: number): Promise<any[]> {
  const result = await cachedQuery(
    `team_all_years_${teamNum}_${version}`,
    () => fetchTeamAllYears(teamNum),
    `/v3/site/teams/${teamNum}/years`,
    3600
  );
  return result || [];
}

export async function getYearEvents(year: number): Promise<any> {
  return cachedQuery(
    `events_${year}_${version}`,
    async () => {
      const [events, yearData] = await Promise.all([
        fetchEvents(year),
        fetchYear(year),
      ]);
      return { year: yearData, events };
    },
    `/v3/site/events/${year}`,
    year === new Date().getFullYear() ? 60 : 3600
  );
}

export async function getEvent(eventKey: string): Promise<any | null> {
  return cachedQuery(
    `event_${eventKey}_${version}`,
    () => fetchEvent(eventKey),
    `/v3/site/events/${eventKey}`,
    300
  );
}

export async function getEventMatches(eventKey: string): Promise<any[]> {
  const result = await cachedQuery(
    `event_matches_${eventKey}_${version}`,
    () => fetchEventMatches(eventKey),
    `/v3/site/events/${eventKey}/matches`,
    60
  );
  return result || [];
}

export async function getTeamYearMatches(
  teamNum: number,
  year: number
): Promise<any[]> {
  const result = await cachedQuery(
    `team_matches_${teamNum}_${year}_${version}`,
    () => fetchTeamMatches(teamNum, year),
    `/v3/site/team_year/${year}/${teamNum}/matches`,
    300
  );
  return result || [];
}

export async function getEventRankings(eventKey: string): Promise<any[]> {
  const result = await cachedQuery(
    `event_rankings_${eventKey}_${version}`,
    () => fetchEventRankings(eventKey),
    `/v3/site/events/${eventKey}/rankings`,
    60
  );
  return result || [];
}

// Default export for backwards compatibility
export default async function query(
  storageKey: string,
  apiPath: string,
  checkBucket: boolean,
  minLength: number,
  expiry: number
) {
  // Parse the API path to determine which function to call
  // This maintains backwards compatibility with existing code

  // Check cache first
  const cached = await getWithExpiry(storageKey);
  if (cached && (minLength === 0 || (cached as any)?.length > minLength)) {
    log(`Used Local Storage: ${storageKey}`);
    return cached;
  }

  const start = performance.now();

  // Fall back to backend API
  try {
    const res = await fetch(`${BACKEND_URL}${apiPath}`, {
      next: { revalidate: 0 },
    });
    log(`${apiPath} (backend) took ${round(performance.now() - start, 0)}ms`);
    if (res.ok) {
      const data = await res.json();
      await setWithExpiry(storageKey, data, expiry);
      return data;
    }
  } catch (error) {
    log(`Error fetching ${apiPath}`, error);
  }

  return null;
}
