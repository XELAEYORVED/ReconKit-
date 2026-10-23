import { Dashboard } from "../components/Dashboard";
import { PageHeader } from "../components/Layout";

export function Home() {
  return (
    <>
      <PageHeader title="Tableau de bord" subtitle="Vue d'ensemble de tes scans." />
      <Dashboard />
    </>
  );
}
