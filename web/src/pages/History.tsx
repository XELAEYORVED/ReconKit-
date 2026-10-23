import { PageHeader } from "../components/Layout";
import { ScanHistory } from "../components/ScanHistory";

export function History() {
  return (
    <>
      <PageHeader
        title="Historique"
        subtitle="Retrouve tes scans, ajoute des favoris, des tags et des notes. Coche deux scans pour les comparer."
      />
      <ScanHistory />
    </>
  );
}
