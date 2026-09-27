"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import { post } from "@/lib/api";
import ThemeToggle from "./ThemeToggle";const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/dashboard?new=1", label: "New Project" },
  { href: "/settings", label: "Settings" },
];

export default function Sidebar({ userName }: { userName?: string }) {
  const pathname = usePathname();
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);

  async function handleLogout() {
    setLoggingOut(true);
    try {
      await post("/api/v1/auth/logout");
    } catch {
      // Best effort: even if the backend call fails, leave the app.
    } finally {
      router.push("/");
      router.refresh();
    }
  }

  function isActive(href: string): boolean {
    if (href === "/dashboard") return pathname === "/dashboard";
    return pathname.startsWith(href.split("?")[0]);
  }

  const nav = (
    <nav aria-label="Primary" className="flex flex-col gap-1">
      {NAV_ITEMS.map((item) => {
        const active = isActive(item.href);
        return (
          <Link
            key={item.label}
            href={item.href}
            onClick={() => setOpen(false)}
            aria-current={active ? "page" : undefined}
            className={`rounded-md px-3 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 ${
              active
                ? "bg-blue-600 text-white"
                : "text-gray-700 hover:bg-gray-200 dark:text-gray-300 dark:hover:bg-gray-800"
            }`}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );

  return (
    <>
      {/* Mobile top bar */}
      <div className="flex items-center justify-between border-b border-gray-200 bg-white px-4 py-3 dark:border-gray-800 dark:bg-gray-950 lg:hidden">
        <button
          type="button"
          onClick={() => setOpen(true)}
          aria-label="Open navigation"
          className="rounded-md p-2 text-gray-700 hover:bg-gray-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:text-gray-200 dark:hover:bg-gray-800"
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M3 6h18M3 12h18M3 18h18" />
          </svg>
        </button>
        <span className="text-sm font-semibold text-gray-900 dark:text-white">CloudForge AI</span>
        <ThemeToggle />
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="fixed inset-0 z-40 lg:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div className="absolute inset-0 bg-black/50" onClick={() => setOpen(false)} aria-hidden="true" />
          <div className="absolute left-0 top-0 flex h-full w-64 flex-col bg-white p-4 dark:bg-gray-950">
            <div className="mb-4 flex items-center justify-between">
              <span className="text-sm font-semibold text-gray-900 dark:text-white">CloudForge AI</span>
              <button
                type="button"
                onClick={() => setOpen(false)}
                aria-label="Close navigation"
                className="rounded-md p-2 text-gray-700 hover:bg-gray-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:text-gray-200 dark:hover:bg-gray-800"
              >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
            {nav}
            <div className="mt-auto pt-4">
              <UserFooter userName={userName} loggingOut={loggingOut} onLogout={handleLogout} />
            </div>
          </div>
        </div>
      )}

      {/* Desktop sidebar */}
      <aside className="hidden w-60 shrink-0 flex-col border-r border-gray-200 bg-white p-4 dark:border-gray-800 dark:bg-gray-950 lg:flex">
        <Link href="/dashboard" className="mb-6 px-2 text-lg font-bold text-gray-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:text-white">
          CloudForge AI
        </Link>
        {nav}
        <div className="mt-auto pt-4">
          <UserFooter userName={userName} loggingOut={loggingOut} onLogout={handleLogout} />
        </div>
      </aside>
    </>
  );
}

function UserFooter({
  userName,
  loggingOut,
  onLogout,
}: {
  userName?: string;
  loggingOut: boolean;
  onLogout: () => void;
}) {
  return (
    <div className="border-t border-gray-200 pt-3 dark:border-gray-800">
      {userName && (
        <p className="px-2 pb-2 text-sm text-gray-600 dark:text-gray-400" aria-label={`Signed in as ${userName}`}>
          {userName}
        </p>
      )}
      <button
        type="button"
        onClick={onLogout}
        disabled={loggingOut}
        className="w-full rounded-md bg-gray-200 px-3 py-2 text-sm font-medium text-gray-800 hover:bg-gray-300 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:opacity-50 dark:bg-gray-800 dark:text-gray-200 dark:hover:bg-gray-700"
      >
        {loggingOut ? "Signing out…" : "Log out"}
      </button>
    </div>
  );
}

