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
