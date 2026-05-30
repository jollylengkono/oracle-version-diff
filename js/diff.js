export const SECTIONS = ['certification', 'whats_new', 'behavior_changes', 'deprecated', 'desupported'];

export function keyFor(section, item) {
  if (section === 'certification') return `${item.category}::${item.value}`;
  return item.title;
}

export function diffSection(section, olderItems, newerItems) {
  const olderByKey = new Map(olderItems.map(i => [keyFor(section, i), i]));
  const newerByKey = new Map(newerItems.map(i => [keyFor(section, i), i]));
  const added = [], removed = [], changed = [], unchanged = [];

  for (const [key, item] of newerByKey) {
    if (!olderByKey.has(key)) { added.push(item); continue; }
    const prev = olderByKey.get(key);
    if ((prev.description || '') !== (item.description || '')) changed.push(item);
    else unchanged.push(item);
  }
  for (const [key, item] of olderByKey) {
    if (!newerByKey.has(key)) removed.push(item);
  }
  return { added, removed, changed, unchanged };
}

export function diffRecords(older, newer) {
  const result = {};
  for (const section of SECTIONS) {
    result[section] = diffSection(
      section,
      older.sections[section] || [],
      newer.sections[section] || []
    );
  }
  return result;
}

function byVersion(records) {
  return new Map(records.map(record => [record.version, record]));
}

function dateValue(record) {
  return Date.parse(record.released || '1970-01-01');
}

export function aggregateRange(records, olderVersion, newerVersion) {
  const ordered = [...records].sort((a, b) => dateValue(b) - dateValue(a));
  const lookup = byVersion(ordered);
  const selectedA = lookup.get(olderVersion);
  const selectedB = lookup.get(newerVersion);
  if (!selectedA || !selectedB) {
    throw new Error('Selected version was not found in loaded records.');
  }

  if (selectedA.version === selectedB.version) {
    return aggregateSelected([selectedA]);
  }

  const indexA = ordered.findIndex(record => record.version === selectedA.version);
  const indexB = ordered.findIndex(record => record.version === selectedB.version);
  const newerIndex = Math.min(indexA, indexB);
  const olderIndex = Math.max(indexA, indexB);

  const selected = ordered.slice(newerIndex, olderIndex).reverse();

  return aggregateSelected(selected);
}

function aggregateSelected(records) {
  const result = {};
  for (const section of SECTIONS) {
    result[section] = [];
    const seen = new Set();
    for (const record of records) {
      const items = (record.sections && record.sections[section]) || [];
      for (const item of items) {
        const key = `${item.title || ''}\u0000${item.description || ''}\u0000${item.source_url || ''}`;
        if (seen.has(key)) continue;
        seen.add(key);
        result[section].push({
          ...item,
          introduced_version: record.version,
          introduced_label: record.release_label || record.version,
          introduced_released: record.released
        });
      }
    }
  }
  return result;
}
