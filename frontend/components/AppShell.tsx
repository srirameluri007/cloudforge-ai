"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { AuthProvider, useAuth } from "@/lib/auth";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import Spinner from "@/components/Spinner";

function Guard({ children, breadcrumb }: { children: React.ReactNode; breadcrumb: string }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, user, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner label="Loading…" />
      </div>
    );
  }

  if (!user) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <Sidebar userName={user.name} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Header breadcrumb={breadcrumb} />
        <main className="flex-1 p-4 sm:p-6">{children}</main>
      </div>
    </div>
  );
}

export default function AppShell({
  children,
  breadcrumb,
}: {
  children: React.ReactNode;
  breadcrumb: string;
}) {
  return (
    <AuthProvider>
      <Guard breadcrumb={breadcrumb}>{children}</Guard>
    </AuthProvider>
  );
}
