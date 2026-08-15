/**
 * Firestore Query Functions
 *
 * Provides typed access to Firestore lead collections.
 * The scraper stores leads in state-specific collections (e.g. leads_haryana).
 * This module auto-discovers all leads_* collections.
 */

import {
  collection,
  getDocs,
  doc,
  updateDoc,
  query,
  orderBy,
} from "firebase/firestore";
import { db } from "./firebase";

// ── Types ───────────────────────────────────────────────

export interface Lead {
  id: string;              // Firestore document ID
  collection: string;      // Which collection it came from (e.g. "leads_haryana")
  Name: string;
  Phone: string;
  Area: string;
  State: string;
  Source: string;
  Status: string;
}

export const STATUS_OPTIONS = [
  "Not Contacted",
  "Contacted",
  "Interested",
  "Not Interested",
  "Follow-up",
] as const;

export type LeadStatus = (typeof STATUS_OPTIONS)[number];

// ── Known collections ───────────────────────────────────
// Add new state collections here as your scraper targets more states.
// Firestore client SDK doesn't support listing collections,
// so we maintain a known list. The app will silently skip
// any collection that doesn't exist.

const KNOWN_LEAD_COLLECTIONS = [
  "leads",
  "leads_haryana",
  "leads_punjab",
  "leads_delhi",
  "leads_rajasthan",
  "leads_uttar_pradesh",
  "leads_maharashtra",
  "leads_gujarat",
  "leads_madhya_pradesh",
  "leads_karnataka",
  "leads_tamil_nadu",
  "leads_telangana",
  "leads_west_bengal",
  "leads_bihar",
];

// ── Fetch leads from a single collection ────────────────

async function getLeadsFromCollection(
  collectionName: string
): Promise<Lead[]> {
  try {
    const colRef = collection(db, collectionName);
    const q = query(colRef);
    const snapshot = await getDocs(q);

    if (snapshot.empty) return [];

    return snapshot.docs.map((docSnap) => {
      const data = docSnap.data();
      return {
        id: docSnap.id,
        collection: collectionName,
        Name: data.Name || data.name || "",
        Phone: data.Phone || data.phone || "",
        Area: data.Area || data.area || "",
        State: data.State || data.state || "",
        Source: data.Source || data.source || "Google Map",
        Status: data.Status || data.status || "Not Contacted",
      };
    });
  } catch {
    // Collection doesn't exist or no permissions — skip silently
    return [];
  }
}

// ── Fetch leads from ALL known collections ──────────────

export async function getAllLeads(): Promise<Lead[]> {
  const promises = KNOWN_LEAD_COLLECTIONS.map((col) =>
    getLeadsFromCollection(col)
  );
  const results = await Promise.all(promises);
  return results.flat();
}

// ── Update a single lead's status ───────────────────────

export async function updateLeadStatus(
  collectionName: string,
  docId: string,
  newStatus: string
): Promise<void> {
  const docRef = doc(db, collectionName, docId);
  await updateDoc(docRef, { Status: newStatus });
}
