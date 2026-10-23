import type { TargetType } from "./types";

/** Plain-language labels for every module, shown across the UI. */
export interface ModuleMeta {
  label: string;
  /** One short sentence a non-expert understands. */
  plain: string;
  group: "infra" | "tech" | "identity" | "history" | "exposure";
}

export const MODULES: Record<string, ModuleMeta> = {
  whois: { label: "Propriétaire du domaine", plain: "Qui a enregistré le nom, quand, et chez quel registrar.", group: "infra" },
  dns: { label: "Enregistrements DNS", plain: "Les adresses IP, serveurs mail et règles anti-usurpation du domaine.", group: "infra" },
  subdomains: { label: "Sous-domaines", plain: "Les autres adresses publiques du site (mail., api., dev.…).", group: "infra" },
  cert_transparency: { label: "Certificats HTTPS", plain: "Les certificats émis publiquement pour ce domaine.", group: "infra" },
  ip_geo: { label: "Localisation du serveur", plain: "Le pays, la ville et l'hébergeur du serveur.", group: "infra" },
  network_map: { label: "Réseau (ASN)", plain: "Le réseau auquel appartient le serveur et ses voisins sur Internet.", group: "infra" },
  tech: { label: "Technologies du site", plain: "CMS, frameworks, CDN et outils détectés sur le site.", group: "tech" },
  headers: { label: "Sécurité HTTP", plain: "Les protections de base que le site envoie au navigateur, avec une note.", group: "tech" },
  shodan: { label: "Ports et services exposés", plain: "Les services visibles depuis Internet et les failles connues.", group: "tech" },
  reputation: { label: "Réputation", plain: "Si l'adresse est signalée comme malveillante (clés API requises).", group: "tech" },
  email: { label: "Emails du domaine", plain: "Les adresses email publiques liées au domaine.", group: "identity" },
  email_profile: { label: "Profil de l'email", plain: "Le type de fournisseur, la sécurité du domaine et un éventuel profil Gravatar.", group: "identity" },
  leak_check: { label: "Fuites de données", plain: "Si l'email apparaît dans des fuites connues (clé HIBP requise).", group: "identity" },
  social: { label: "Réseaux sociaux", plain: "Les plateformes où ce pseudo existe.", group: "identity" },
  github: { label: "GitHub", plain: "Les dépôts publics qui mentionnent la cible.", group: "identity" },
  metadata: { label: "Métadonnées de documents", plain: "Auteurs et logiciels cachés dans les PDF/Word publics.", group: "identity" },
  wayback: { label: "Archives du site", plain: "L'historique du site dans la Wayback Machine.", group: "history" },
  google_dork: { label: "Recherche Google ciblée", plain: "Des pages sensibles indexées par Google (clé requise).", group: "exposure" },
  pastebin: { label: "Sites de « paste »", plain: "Des mentions sur Pastebin et sites similaires (clé requise).", group: "exposure" },
};

export const GROUPS: Record<ModuleMeta["group"], string> = {
  infra: "Infrastructure",
  tech: "Technologies & sécurité",
  identity: "Identité",
  history: "Historique",
  exposure: "Exposition",
};

export const TYPE_LABEL: Record<TargetType | string, string> = {
  domain: "Domaine",
  ip: "Adresse IP",
  email: "Email",
  username: "Pseudo",
  unknown: "Inconnu",
};

export const RISK_LABEL: Record<string, string> = {
  low: "Faible",
  medium: "Moyen",
  high: "Élevé",
  critical: "Critique",
};

export const STATUS_LABEL: Record<string, string> = {
  pending: "En attente",
  running: "En cours",
  completed: "Terminé",
  failed: "Échoué",
  cancelled: "Annulé",
};

export function moduleLabel(name: string): string {
  return MODULES[name]?.label ?? name;
}
