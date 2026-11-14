"use client";

// Small building blocks shared by every page, styled with Tailwind classes.
// The pages sit on top of a map, so cards are "frosted glass": slightly
// see-through, with the map blurred behind them.

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "dark" | "danger" | "ghost";
  size?: "md" | "sm";
};

const buttonStyles = {
  primary: "bg-amber-400 text-slate-950 shadow-sm shadow-amber-500/30 hover:bg-amber-300",
  dark: "bg-slate-900 text-white shadow-sm hover:bg-slate-700",
  danger: "bg-rose-600 text-white shadow-sm hover:bg-rose-500",
  ghost: "text-slate-700 hover:bg-slate-900/5",
};

const buttonSizes = { md: "px-4 py-2.5 text-sm", sm: "px-3 py-1.5 text-xs" };

export function Button({ variant = "primary", size = "md", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`rounded-xl font-semibold transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-slate-900 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-40 disabled:active:scale-100 ${buttonStyles[variant]} ${buttonSizes[size]} ${className}`}
      {...props}
    />
  );
}

const fieldStyle =
  "w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-amber-400 focus:ring-4 focus:ring-amber-100 disabled:bg-slate-50";
const labelStyle = "mb-1.5 block text-xs font-semibold uppercase tracking-wide text-slate-500";

export function Field({ label, ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className="block">
      <span className={labelStyle}>{label}</span>
      <input className={fieldStyle} {...props} />
    </label>
  );
}

export function SelectField({
  label,
  children,
  ...props
}: SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  return (
    <label className="block">
      <span className={labelStyle}>{label}</span>
      <select className={fieldStyle} {...props}>
        {children}
      </select>
    </label>
  );
}

export const glass = "rounded-2xl border border-white/70 bg-white/85 shadow-xl shadow-slate-900/10 backdrop-blur-md";

export function Card({ title, children, className = "" }: { title?: string; children: ReactNode; className?: string }) {
  return (
    <section className={`${glass} p-6 ${className}`}>
      {title && <h2 className="mb-4 text-lg font-bold tracking-tight">{title}</h2>}
      {children}
    </section>
  );
}

export type NoticeState = { kind: "ok" | "error"; text: string } | null;

export function Notice({ notice }: { notice: NoticeState }) {
  if (!notice) return null;
  const style =
    notice.kind === "ok"
      ? "border-emerald-200 bg-emerald-50/95 text-emerald-900"
      : "border-rose-200 bg-rose-50/95 text-rose-900";
  return (
    <p role="status" className={`rounded-xl border px-4 py-2.5 text-sm font-medium shadow-sm backdrop-blur ${style}`}>
      {notice.text}
    </p>
  );
}

export function Tabs({ tabs, current, onChange }: { tabs: string[]; current: string; onChange: (tab: string) => void }) {
  return (
    <div role="tablist" className={`inline-flex max-w-full gap-1 overflow-x-auto rounded-full border border-white/70 bg-white/80 p-1 shadow-lg shadow-slate-900/10 backdrop-blur-md`}>
      {tabs.map((tab) => (
        <button
          key={tab}
          role="tab"
          aria-selected={tab === current}
          onClick={() => onChange(tab)}
          className={`whitespace-nowrap rounded-full px-4 py-2 text-sm font-semibold transition ${
            tab === current ? "bg-slate-900 text-white shadow" : "text-slate-600 hover:bg-slate-900/5 hover:text-slate-900"
          }`}
        >
          {tab}
        </button>
      ))}
    </div>
  );
}

export function Table({ headings, children, empty }: { headings: string[]; children: ReactNode; empty: boolean }) {
  if (empty) return <p className="py-6 text-center text-sm text-slate-500">Nothing to show yet.</p>;
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead>
          <tr className="border-b border-slate-200 text-xs uppercase tracking-wide text-slate-500">
            {headings.map((heading) => (
              <th key={heading} className="px-3 py-2.5 font-semibold">
                {heading}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-100 [&_td]:px-3 [&_td]:py-3 [&_tr]:transition hover:[&_tr]:bg-slate-900/[0.03]">
          {children}
        </tbody>
      </table>
    </div>
  );
}

const statusStyles: Record<string, string> = {
  pending: "bg-amber-100 text-amber-900 ring-amber-200",
  accepted: "bg-sky-100 text-sky-900 ring-sky-200",
  completed: "bg-emerald-100 text-emerald-900 ring-emerald-200",
  cancelled: "bg-slate-100 text-slate-600 ring-slate-200",
};

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${statusStyles[status] ?? ""}`}>
      {status}
    </span>
  );
}

export function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  return (
    <div className="fixed inset-0 z-30 flex items-center justify-center bg-slate-900/40 p-4 backdrop-blur-sm" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl bg-white p-6 shadow-2xl"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 className="mb-4 text-lg font-bold tracking-tight">{title}</h2>
        {children}
      </div>
    </div>
  );
}

export function ratingText(rating: "up" | "down" | null): string {
  if (rating === "up") return "👍";
  if (rating === "down") return "👎";
  return "Not rated";
}

// The UBA badge used in the header and on the login pages.
export function Logo({ subtitle }: { subtitle: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-400 text-xl font-black text-slate-950 shadow-md shadow-amber-500/40">
        U
      </span>
      <div className="leading-tight">
        <p className="text-2xl font-black tracking-tight">UBA</p>
        <p className="text-xs font-medium text-slate-500">{subtitle}</p>
      </div>
    </div>
  );
}
