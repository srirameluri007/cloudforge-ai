import ThemeToggle from "./ThemeToggle";

/** Top header bar shown on desktop above app content. */
export default function Header({ breadcrumb }: { breadcrumb: string }) {
  return (
    <header className="hidden items-center justify-between border-b border-gray-200 bg-white px-6 py-3 dark:border-gray-800 dark:bg-gray-950 lg:flex">
      <p className="text-sm text-gray-500 dark:text-gray-400" aria-label="Breadcrumb">
        {breadcrumb}
      </p>
      <ThemeToggle />
    </header>
  );
}
