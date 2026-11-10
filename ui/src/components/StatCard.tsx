import React from "react";

export function Card({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-[24px] bg-surface shadow-soft ring-1 ring-line ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle }: { title: string; subtitle?: string }) {
  return (
    <div className="border-b border-line px-6 py-5">
      <h2 className="text-sm font-semibold tracking-tight text-ink">{title}</h2>
      {subtitle ? <p className="mt-1 text-sm text-muted">{subtitle}</p> : null}
    </div>
  );
}

export function CardBody({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return <div className={`px-6 py-6 ${className}`}>{children}</div>;
}
