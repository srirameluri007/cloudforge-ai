import AppShell from "@/components/AppShell";

export default function AppGroupLayout({ children }: { children: React.ReactNode }) {
  return <AppShell breadcrumb="CloudForge AI">{children}</AppShell>;
}
