"use client";

import { LoaderOne } from "@/components/ui/loader";

export default function GlobalLoading() {
  return (
    <div className="fixed top-3 left-3 z-50">
      <LoaderOne size="sm" />
      <span className="sr-only">Loading…</span>
    </div>
  );
}


