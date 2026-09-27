import Link from "next/link";

const FEATURES = [
  {
    title: "Natural-language requirements",
    description:
      "Describe your workload in plain English. CloudForge turns it into a structured infrastructure plan with secure defaults.",
  },
  {
    title: "Multi-cloud IaC output",
    description:
      "Generates Terraform, Bicep, ARM, CloudFormation, Kubernetes, and Helm — plus CI/CD pipelines for GitHub Actions, Azure DevOps, Jenkins, and GitLab.",
  },
  {
    title: "Security built in",
    description:
      "Every generation ships with a security findings report, zero-trust scoring, and cost guidance — before anything reaches your cloud.",
  },
  {
    title: "Compliance aware",
    description:
      "Target CIS, NIST, SOC 2, PCI-DSS, or ISO 27001 baselines so generated resources start from your required control set.",
  },
  {
    title: "One-click export",
    description:
      "Download individual files or export the entire project as a ZIP ready to commit to source control.",
  },
  {
    title: "Review-first workflow",
    description:
      "Clear provenance on every asset: which prompt, which provider, and a prominent reminder to have a qualified engineer review before deployment.",
  },
];

export default function LandingPage() {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-gray-200 dark:border-gray-800">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="text-xl font-bold">CloudForge AI</span>
          <nav className="flex items-center gap-3" aria-label="Account">
            <Link
              href="/login"
              className="rounded-md px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:text-gray-300 dark:hover:bg-gray-800"
            >
              Log in
            </Link>
            <Link
              href="/register"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
            >
              Sign up
            </Link>
          </nav>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6">
        <section className="py-16 text-center sm:py-24">
          <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl">CloudForge AI</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-gray-600 dark:text-gray-400">
            From natural-language requirements to secure, validated, deployment-ready cloud
            infrastructure.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/dashboard"
              className="rounded-md bg-blue-600 px-6 py-3 text-base font-semibold text-white hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500"
            >
              Start Building
            </Link>
            <Link
              href="/register"
              className="rounded-md border border-gray-300 px-6 py-3 text-base font-semibold text-gray-700 hover:bg-gray-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-blue-500 dark:border-gray-700 dark:text-gray-200 dark:hover:bg-gray-800"
            >
              Create account
            </Link>
          </div>
        </section>

        <section aria-labelledby="features-heading" className="pb-16">
          <h2 id="features-heading" className="sr-only">
            Features
          </h2>
          <ul className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <li
                key={f.title}
                className="rounded-lg border border-gray-200 bg-white p-6 dark:border-gray-800 dark:bg-gray-900"
              >
                <h3 className="text-base font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{f.description}</p>
              </li>
            ))}
          </ul>
        </section>

        <section aria-label="Deployment safety notice" className="pb-16">
          <div className="rounded-lg border border-amber-300 bg-amber-50 p-6 dark:border-amber-700 dark:bg-amber-950/40">
            <p className="text-sm font-semibold text-amber-900 dark:text-amber-100">
              Important: generated infrastructure must be reviewed by a qualified engineer before
              deployment.
            </p>
            <p className="mt-2 text-sm text-amber-800 dark:text-amber-200/80">
              CloudForge AI produces a starting point — not a signed-off production system. Always
              validate, test, and review generated code in your own environment before applying it
              to any cloud account.
            </p>
          </div>
        </section>
      </main>

      <footer className="border-t border-gray-200 py-6 dark:border-gray-800">
        <p className="mx-auto max-w-6xl px-6 text-sm text-gray-500 dark:text-gray-400">
          CloudForge AI — secure infrastructure, generated responsibly.
        </p>
      </footer>
    </div>
  );
}
