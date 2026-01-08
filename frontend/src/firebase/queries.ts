// Firestore queries for FTC Insight frontend
import {
  QueryConstraint,
  collection,
  doc,
  getDoc,
  getDocs,
  limit,
  orderBy,
  query,
  where,
} from "firebase/firestore";

import { COLLECTIONS, getDb } from "./config";

// Helper to log query timing
function logTiming(name: string, start: number) {
  console.log(`${name} took ${Math.round(performance.now() - start)}ms`);
}

// Generic document fetch
export async function fetchDocument<T>(collectionName: string, docId: string): Promise<T | null> {
  const start = performance.now();
  try {
    const db = getDb();
    const docRef = doc(db, collectionName, docId);
    const docSnap = await getDoc(docRef);
    logTiming(`fetchDocument(${collectionName}/${docId})`, start);
    return docSnap.exists() ? (docSnap.data() as T) : null;
  } catch (error) {
    console.error(`Error fetching ${collectionName}/${docId}:`, error);
    return null;
  }
}

// Generic collection fetch with filters
export async function fetchCollection<T>(
  collectionName: string,
  constraints: QueryConstraint[] = []
): Promise<T[]> {
  const start = performance.now();
  try {
    const db = getDb();
    const collectionRef = collection(db, collectionName);
    const q = query(collectionRef, ...constraints);
    const querySnapshot = await getDocs(q);
    const results = querySnapshot.docs.map((doc) => doc.data() as T);
    logTiming(`fetchCollection(${collectionName})`, start);
    return results;
  } catch (error) {
    console.error(`Error fetching ${collectionName}:`, error);
    return [];
  }
}

// Teams
export async function fetchTeams(): Promise<any[]> {
  return fetchCollection(COLLECTIONS.teams, [where("active", "==", true)]);
}

export async function fetchTeam(teamNum: number): Promise<any | null> {
  return fetchDocument(COLLECTIONS.teams, String(teamNum));
}

// Team Years
export async function fetchTeamYears(year: number, limitCount?: number): Promise<any[]> {
  const constraints: QueryConstraint[] = [where("year", "==", year), orderBy("epa", "desc")];
  if (limitCount) {
    constraints.push(limit(limitCount));
  }
  return fetchCollection(COLLECTIONS.team_years, constraints);
}

export async function fetchTeamYear(teamNum: number, year: number): Promise<any | null> {
  return fetchDocument(COLLECTIONS.team_years, `${teamNum}_${year}`);
}

export async function fetchTeamAllYears(teamNum: number): Promise<any[]> {
  return fetchCollection(COLLECTIONS.team_years, [
    where("team", "==", teamNum),
    orderBy("year", "desc"),
  ]);
}

// Events
export async function fetchEvents(year: number): Promise<any[]> {
  return fetchCollection(COLLECTIONS.events, [where("year", "==", year), orderBy("time", "asc")]);
}

export async function fetchEvent(eventKey: string): Promise<any | null> {
  return fetchDocument(COLLECTIONS.events, eventKey);
}

// Matches
export async function fetchEventMatches(eventKey: string): Promise<any[]> {
  return fetchCollection(COLLECTIONS.matches, [
    where("event", "==", eventKey),
    orderBy("time", "asc"),
  ]);
}

export async function fetchTeamMatches(teamNum: number, year: number): Promise<any[]> {
  // First get all team_events for this team/year
  const teamEvents = await fetchCollection(COLLECTIONS.team_events, [
    where("team", "==", teamNum),
    where("year", "==", year),
  ]);

  // Then fetch matches for each event where this team participated
  const allMatches: any[] = [];
  for (const te of teamEvents) {
    const eventMatches = await fetchEventMatches(te.event);
    // Filter to matches where this team played
    const teamMatches = eventMatches.filter(
      (m) =>
        m.red_1 === teamNum || m.red_2 === teamNum || m.blue_1 === teamNum || m.blue_2 === teamNum
    );
    allMatches.push(...teamMatches);
  }

  return allMatches.sort((a, b) => a.time - b.time);
}

// Year Statistics
export async function fetchYear(year: number): Promise<any | null> {
  return fetchDocument(COLLECTIONS.years, String(year));
}

// Rankings
export async function fetchEventRankings(eventKey: string): Promise<any[]> {
  return fetchCollection(COLLECTIONS.rankings, [
    where("event", "==", eventKey),
    orderBy("rank", "asc"),
  ]);
}

// Team Events
export async function fetchTeamEvents(teamNum: number, year?: number): Promise<any[]> {
  const constraints: QueryConstraint[] = [where("team", "==", teamNum)];
  if (year) {
    constraints.push(where("year", "==", year));
  }
  return fetchCollection(COLLECTIONS.team_events, constraints);
}

// Metadata
export async function fetchMetadata(key: string): Promise<any | null> {
  return fetchDocument(COLLECTIONS.metadata, key);
}
