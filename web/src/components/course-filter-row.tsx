"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export type Filters = {
  name: string;
  university: string;
  duration: string;
  campus: string;
  atarMin: string;
};

type CampusOption = { name: string; university: string };

type Props = {
  universities: string[];
  durations: string[];
  campuses: CampusOption[];
  sort: string;
  dir: string;
  filters: Filters;
};

const inputCls =
  "w-full rounded border border-gray-200 bg-white px-2 py-1 text-xs dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100";

export function FilterRow({ universities, durations, campuses, sort, dir, filters: f }: Props) {
  const router = useRouter();
  const [name, setName] = useState(f.name);
  const [atarMin, setAtarMin] = useState(f.atarMin);

  useEffect(() => setName(f.name), [f.name]);
  useEffect(() => setAtarMin(f.atarMin), [f.atarMin]);

  function buildUrl(overrides: Partial<Filters>) {
    const merged = { ...f, name, atarMin, ...overrides };
    const p = new URLSearchParams();
    if (sort) p.set("sort", sort);
    if (dir) p.set("dir", dir);
    p.set("page", "1");
    if (merged.name) p.set("f_name", merged.name);
    if (merged.university) p.set("f_uni", merged.university);
    if (merged.duration) p.set("f_dur", merged.duration);
    if (merged.campus) p.set("f_cam", merged.campus);
    if (merged.atarMin) p.set("f_atar_min", merged.atarMin);
    return `/courses?${p.toString()}`;
  }

  return (
    <tr className="border-b border-gray-100 bg-gray-50 dark:border-gray-800 dark:bg-gray-900/40">
      <td className="py-1 pr-4">
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          onBlur={() => router.push(buildUrl({}))}
          onKeyDown={e => e.key === "Enter" && router.push(buildUrl({}))}
          placeholder="Search..."
          className={inputCls}
        />
      </td>
      <td className="py-1 pr-4">
        <select value={f.university} onChange={e => router.push(buildUrl({ university: e.target.value }))} className={inputCls}>
          <option value="">All</option>
          {universities.map(u => <option key={u} value={u}>{u}</option>)}
        </select>
      </td>
      <td className="py-1 pr-4">
        <input
          type="number"
          value={atarMin}
          onChange={e => setAtarMin(e.target.value)}
          onBlur={() => router.push(buildUrl({}))}
          onKeyDown={e => e.key === "Enter" && router.push(buildUrl({}))}
          placeholder="Min ATAR"
          min={0}
          max={99}
          className={inputCls}
        />
      </td>
      <td className="py-1 pr-4">
        {/* Mobile: name only */}
        <select value={f.campus} onChange={e => router.push(buildUrl({ campus: e.target.value }))} className={`${inputCls} sm:hidden`}>
          <option value="">All</option>
          {campuses.map(c => <option key={`${c.name}-${c.university}`} value={c.name}>{c.name}</option>)}
        </select>
        {/* Desktop: name (university) */}
        <select value={f.campus} onChange={e => router.push(buildUrl({ campus: e.target.value }))} className={`${inputCls} hidden sm:block`}>
          <option value="">All</option>
          {campuses.map(c => <option key={`${c.name}-${c.university}`} value={c.name}>{c.name} ({c.university})</option>)}
        </select>
      </td>
      <td className="hidden sm:table-cell py-1 pr-4">
        <select value={f.duration} onChange={e => router.push(buildUrl({ duration: e.target.value }))} className={inputCls}>
          <option value="">All</option>
          {durations.map(d => <option key={d} value={d}>{d}y</option>)}
        </select>
      </td>
    </tr>
  );
}
