# ReconKit, expliqué simplement

> Tu n'es pas informaticien ? Ce guide est pour toi.
> (La documentation technique est dans le [README](README.md).)

## C'est quoi ?

ReconKit répond à une question : **« Qu'est-ce qu'Internet sait déjà sur… ? »**

Tu lui donnes **une seule chose** :

| Tu tapes… | Exemple | ReconKit te dit… |
| --- | --- | --- |
| 🌐 Un site web | `example.com` | à qui il appartient, où il est hébergé, quelles technologies il utilise, s'il est bien protégé |
| 🖥️ Une adresse IP | `8.8.8.8` | dans quel pays se trouve le serveur, chez quel hébergeur, quels « portes » (ports) sont ouvertes |
| ✉️ Un email | `prenom@entreprise.com` | si l'adresse peut vraiment recevoir des emails, si c'est une adresse jetable, s'il y a un profil public lié |
| 👤 Un pseudo | `johndoe` | sur quels réseaux sociaux ce pseudo existe |

Ensuite il te donne **un score de risque de 0 à 100** et des **fiches claires**, en
français, qui expliquent ce qui a été trouvé.

## Est-ce que c'est légal ? Est-ce que la cible le voit ?

ReconKit est **100 % passif** : il ne « touche » jamais la cible. Il lit uniquement
des informations **déjà publiques** (annuaires d'Internet, archives du web, registres
de certificats…). La cible ne voit rien passer.

⚠️ **Mais** : n'analyse que **ce qui t'appartient** (ton site, ton email, ton
pseudo) ou ce que tu as **l'autorisation** d'analyser. Rassembler des infos sur
une personne sans raison valable peut être illégal (RGPD).

## Ce que ReconKit ne fait pas

- ❌ Il ne cherche pas une personne par son **nom et prénom** (`Jean Dupont` ne marche pas).
- ❌ Il ne pirate rien et ne devine aucun mot de passe.
- ❌ Il ne lit pas d'emails ni de messages privés.

## Installer et lancer (le plus simple)

Il te faut **Docker Desktop** (gratuit : <https://www.docker.com/products/docker-desktop/>).

1. Télécharge le projet (bouton vert **Code → Download ZIP** sur GitHub) et décompresse-le.
2. Ouvre un terminal dans le dossier du projet.
3. Tape ces deux commandes (la première crée le fichier de réglages, une seule fois) :

   ```bash
   cp .env.example .env        # sous Windows (invite de commandes) : copy .env.example .env
   docker compose up --build
   ```

4. Attends quelques minutes la première fois, puis ouvre **<http://localhost:8000>**
   dans ton navigateur.

Pour arrêter : `Ctrl + C` dans le terminal.

## Utiliser ReconKit, pas à pas

1. **Tableau de bord** : la page d'accueil. Clique sur **« Lancer un scan »**.
2. **Nouveau scan** : tape ta cible (ou clique sur un exemple). ReconKit reconnaît tout
   seul si c'est un site, une IP, un email ou un pseudo, et te montre la liste de ce qu'il
   va vérifier. Clique sur **« Lancer le scan »**.
3. **Pendant le scan** (entre 30 secondes et 2 minutes) : chaque vérification s'affiche
   en direct :
   - ✅ **trouvé** : il y a des informations ;
   - ⊖ **ignoré** : il faudrait une clé API (voir plus bas), ce n'est pas une erreur ;
   - ✕ **erreur** : la source publique n'a pas répondu, réessaie plus tard.
4. **Résultats** : clique sur **« Voir les résultats »**.

## Lire les résultats

### Le score de risque

| Score | Niveau | Ce que ça veut dire |
| --- | --- | --- |
| 0 – 19 | 🟢 Faible | Rien d'inquiétant |
| 20 – 39 | 🟡 Moyen | Quelques points à corriger |
| 40 – 69 | 🟠 Élevé | Plusieurs problèmes visibles publiquement |
| 70 – 100 | 🔴 Critique | À traiter en priorité |

Juste à côté, **« Pourquoi ce score ? »** liste chaque problème trouvé et combien de
points il ajoute. Le score n'est jamais une boîte noire.

### Les fiches

Chaque vérification a sa fiche, avec une phrase de conclusion en couleur :
🟢 c'est bien · 🟡 à surveiller · 🔴 problème · 🔵 information.

Quelques mots que tu vas croiser :

| Mot | En clair |
| --- | --- |
| **DNS** | L'annuaire d'Internet : il relie un nom (`example.com`) à l'adresse d'un serveur. |
| **Sous-domaine** | Une « sous-adresse » d'un site : `mail.example.com`, `shop.example.com`… |
| **DMARC / SPF** | Des protections qui empêchent quelqu'un d'envoyer de faux emails au nom d'un domaine. |
| **Certificat HTTPS** | Ce qui affiche le cadenas 🔒 dans le navigateur. |
| **Port** | Une « porte » d'un serveur. Certaines ne devraient jamais être ouvertes sur Internet. |
| **CVE** | Une faille de sécurité connue et répertoriée publiquement. |
| **Gravatar** | Un service qui associe une photo de profil (et parfois d'autres comptes) à un email. |
| **Fuite de données** | Un piratage passé où des emails (et parfois des mots de passe) ont été publiés. |

### Les autres onglets

- **Chronologie** : l'histoire du site (création, captures dans les archives du web…).
- **Carte & réseau** : où se trouve le serveur sur la carte du monde.
- **Graphe** : un dessin des liens entre tout ce qui a été trouvé.
- **Données brutes** : tout le détail technique, pour les curieux.

### Télécharger un rapport

En bas du bilan, clique sur **PDF** pour avoir un rapport à imprimer ou à envoyer.

## Les autres pages

- **Historique** : tous tes anciens scans. Tu peux les mettre en ⭐ favoris, ajouter des
  tags et des notes. Coche **deux scans** de la même cible puis **« Comparer »** pour voir
  ce qui a changé entre les deux.
- **Réglages** : pour ajouter des **clés API**.

## C'est quoi une clé API ? En ai-je besoin ?

**Non, pas pour commencer** : 15 vérifications sur 19 marchent sans rien configurer.

Une clé API, c'est un « badge d'accès » gratuit (ou parfois payant) qu'un service te
donne quand tu crées un compte chez lui. Elle débloque des vérifications en plus, par
exemple :

- **Have I Been Pwned** → savoir si un email a fuité (payant) ;
- **Hunter.io** → trouver plus d'emails d'une entreprise ;
- **VirusTotal / AbuseIPDB** → savoir si un site est signalé comme dangereux.

Dans **Réglages**, chaque service a un petit lien ↗ pour obtenir sa clé. Colle-la,
clique sur **Enregistrer** : c'est actif tout de suite.

## « Je n'ai aucun résultat », c'est normal ?

| Situation | Explication | Solution |
| --- | --- | --- |
| Tu as tapé un nom et un prénom | Ce n'est pas un type de cible accepté | Tape un site, une IP, un email ou un pseudo |
| Email avec peu de résultats | Pour un email, la plupart des sources demandent une clé API | Normal, ou ajoute une clé dans Réglages |
| Une fiche en ✕ erreur | La source publique était lente ou indisponible | Relance le scan plus tard |
| Pseudo introuvable | Il n'existe peut-être sur aucune grande plateforme | Normal |

👉 **Pour voir tout ce que ReconKit sait faire, scanne un nom de domaine**
(par exemple `example.com` ou le site de ton école).

## Questions fréquentes

**Est-ce que c'est gratuit ?** Oui, ReconKit est open source (licence MIT).

**Mes scans sont-ils envoyés quelque part ?** Non, ils restent sur ton ordinateur
(dossier `data/`).

**Un pseudo trouvé sur Instagram, c'est forcément la même personne ?** Non ! Deux
personnes peuvent avoir le même pseudo. ReconKit dit seulement que le compte existe.
