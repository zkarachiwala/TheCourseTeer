"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";

export type Filters = {
  name: string;
  university: string;
  type: string;
  duration: string;
  atarMin: string;
  atarMax: string;
};

type Props = {
  universities: string[];
  durations: string[];
  sort: string;
  dir: string;
  filters: Filters;
};

const inputCls =
  "w-full rounded border border-gray-200 bg-white px-2 py-1 text-xs dark:border-gray-700 dark:bg-gray-900 dark:text-gray-100";

export function FilterRow({ universities, durations, sort, dir, filters: f }: Props) {
  const router = useRouter();
  const [name, setName] = useState(f.name);
  const [atarMin, setAtarMin] = useState(f.atarMin);
  const [atarMax, setAtarMax] = useState(f.atarMax);

  useEffect(() => setName(f.name), [f.name]);
  useEffect(() => setAtarMin(f.atarMin), [f.atarMin]);
  useEffect(() => setAtarMax(f.atarMax), [f.atarMax]);

  function buildUrl(overrides: Partial<Filters>) {
    const merged = { ...f, name, atarMin, atarMax, ...overrides };
    const p = new URLSearchParams();
    if (sort) p.set("sort", sort);
    if (dir) p.set("dir", dir);
    p.set("page", "1");
    if (merged.name) p.set("f_name", merged.name);
    if (merged.university) p.set("f_uni", merged.university);
    if (merged.type) p.set("f_type", merged.type);
    if (merged.duration) p.set("f_dur", merged.duration);
    if (merged.atarMin) p.set("f_atar_min", merged.atarMin);
    if (merged.atarMax) p.set("f_atar_max", merged.atarMax);
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
        <select
          value={f.university}
          onChange={e => router.push(buildUrl({ university: e.target.value }))}
          className={inputCls}
        >
          <option value="">All</option>
          {universities.map(u => <option key={u} value={u}>{u}</option>)}
        </select>
      </td>
      <td className="py-1 pr-4">
        <select
          value={f.type}
          onChange={e => router.push(buildUrl({ type: e.target.value }))}
          className={inputCls}
        >
          <option value="">All</option>
          <option value="UG">UG</option>
          <option value="PG">PG</option>
        </select>
      </td>
      <td className="py-1 pr-4">
        <select
          value={f.duration}
          onChange={e => router.push(buildUrl({ duration: e.target.value }))}
          className={inputCls}
        >
          <option value="">All</option>
          {durations.map(d => <option key={d} value={d}>{d}y</option>)}
        </select>
      </td>
      <td className="py-1 pr-4" />
      <td className="py-1">
        <div className="flex items-center gap-1">
          <input
            type="number"
            value={atarMin}
            onChange={e => setAtarMin(e.target.value)}
            onBlur={() => router.push(buildUrl({}))}
            placeholder="Min"
            min={0}
            max={99}
            className={`${inputCls} w-14`}
          />
          <span className="text-xs text-gray-400">–</span>
          <input
            type="number"
            value={atarMax}
            onChange={e => setAtarMax(e.target.value)}
            onBlur={() => router.push(buildUrl({}))}
            placeholder="Max"
            min={0}
            max={99}
            className={`${inputCls} w-14`}
          />
        </div>
      </td>
    </tr>
  );
}
