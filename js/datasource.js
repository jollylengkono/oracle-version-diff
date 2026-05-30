// js/datasource.js
// The ONLY data-access seam. To move to Supabase/REST later, replace the bodies
// of loadIndex/loadRecord with API calls — app.js and pure logic stay unchanged.
import { DATA_BASE } from './config.js';

export function indexPath() { return `${DATA_BASE}/index.json`; }
export function recordPath(file) { return `${DATA_BASE}/${file}`; }

async function fetchJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

export async function loadIndex() { return fetchJson(indexPath()); }
export async function loadRecord(file) { return fetchJson(recordPath(file)); }
