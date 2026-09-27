"use client";

import { useRef } from "react";

interface TabItem {
  key: string;
  label: string;
  disabled?: boolean;
}

interface TabsProps {
  tabs: TabItem[];
  activeKey: string;
  onChange: (key: string) => void;
  ariaLabel: string;
}

/** Accessible, keyboard-navigable tab list (arrow-key support). */
export default function Tabs({ tabs, activeKey, onChange, ariaLabel }: TabsProps) {
  const listRef = useRef<HTMLDivElement>(null);

  function focusTab(index: number) {
    const buttons = listRef.current?.querySelectorAll<HTMLButtonElement>('[role="tab"]');
    const btn = buttons?.[index];
    btn?.focus();
    if (btn && !btn.disabled) onChange(btn.dataset.key ?? "");
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    const current = tabs.findIndex((t) => t.key === activeKey);
    if (e.key === "ArrowRight") {
      e.preventDefault();
      focusTab((current + 1) % tabs.length);
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      focusTab((current - 1 + tabs.length) % tabs.length);
    } else if (e.key === "Home") {
      e.preventDefault();
      focusTab(0);
    } else if (e.key === "End") {
      e.preventDefault();
      focusTab(tabs.length - 1);
    }
  }

  return (
    <div
      ref={listRef}
      role="tablist"
      aria-label={ariaLabel}
      onKeyDown={handleKeyDown}
      className="flex flex-wrap gap-1 border-b border-gray-200 dark:border-gray-800"
    >
      {tabs.map((tab) => {
        const active = tab.key === activeKey;
        return (
          <button
            key={tab.key}
            type="button"
            role="tab"
            data-key={tab.key}
            id={`tab-${tab.key}`}
            aria-selected={active}
            aria-controls={`tabpanel-${tab.key}`}
            disabled={tab.disabled}
            onClick={() => onChange(tab.key)}
            className={`rounded-t-md px-3 py-2 text-sm font-medium focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 disabled:cursor-not-allowed disabled:opacity-40 ${
              active
                ? "border-b-2 border-blue-600 text-blue-700 dark:text-blue-300"
                : "text-gray-600 hover:text-gray-900 dark:text-gray-400 dark:hover:text-gray-100"
            }`}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );
}
