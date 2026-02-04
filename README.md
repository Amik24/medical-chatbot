# 🌸 ORIA : Assistant d’Information en Santé Féminine

**ORIA** est un espace d'écoute et d'orientation conversationnel intelligent dédié à la santé des femmes. Conçu pour briser les tabous et offrir une première réponse fiable, cet assistant aide à décrypter les symptômes et oriente vers les structures de soins adaptées en France, Suisse et Allemagne.

🚀 **Démo Live :** [medical-chatbot-ochre.vercel.app](https://medical-chatbot-ochre.vercel.app)

⚙️ **Backend API :** FastAPI + Mistral AI (Déployé sur Railway)

---

##  Objectifs du projet

Le projet répond à un besoin de pré-orientation rapide, sécurisé et bienveillant.

* **Libérer la parole :** Une interface anonyme pour décrire des symptômes sans jugement.
* **Pédagogie active :** Expliquer les mécanismes hormonaux et gynécologiques simplement.
* **Orientation ciblée :** Identifier le degré d'urgence et le spécialiste approprié (gynécologue, sage-femme, endocrinologue).
* **Inclusivité linguistique :** Support complet et switch instantané entre le **Français**, l'**Anglais** et l'**Allemand**.

---

## 🛠 Architecture & Tech Stack

L'intelligence d'ORIA repose sur un système de **double filtrage** : un premier modèle classifie l'intention et la langue, tandis qu'un second génère la réponse spécialisée.

| Composant | Technologie | Rôle |
| --- | --- | --- |
| **Frontend** | HTML5 / CSS3 / JS | Interface utilisateur ultra-légère & responsive. |
| **Backend** | Python / FastAPI | Gestion des sessions, logique de triage et API. |
| **LLM** | Mistral-Small-Latest | Intelligence conversationnelle haute performance. |
| **Mémoire** | In-Memory Session | Conservation du contexte sur 10 messages (30 min). |

---

## 🩺 Périmètre & Sécurité

### Sujets couverts

* **Cycle & Hormones :** SPM, endométriose, SOPK, irrégularités.
* **Santé Urogénitale :** Cystites (douleurs urinaires), mycoses, IST.
* **Vie reproductive :** Contraception, grossesse, post-partum, ménopause.

### 🛡 Garde-fous (Safety First)

* **Zéro Diagnostic :** Utilisation systématique du conditionnel.
* **Zéro Prescription :** Aucune mention de médicaments ou dosages.
* **Triage Dynamique :** Filtrage des sujets hors-santé pour garantir la pertinence.

---

## 🚨 Protocoles d'Urgence

En cas de détection de signaux critiques (douleurs aiguës, hémorragies), ORIA affiche les numéros de secours locaux :

* **🇫🇷 France :** 15 ou 112
* **🇨🇭 Suisse :** 144 ou 112
* **🇩🇪 Allemagne :** 112

---

## Installation Locale

Si vous souhaitez faire tourner le projet sur votre machine :

1. **Cloner le projet**
```bash
git clone https://github.com/votre-user/oria-backend.git
cd oria-backend

```


2. **Installer les dépendances**
```bash
pip install -r requirements.txt

```


3. **Configurer les variables d'environnement**
Créer un fichier `.env` :
```env
MISTRAL_API_KEY=votre_cle_ici
MISTRAL_MODEL=mistral-small-latest

```


4. **Lancer le serveur**
```bash
python main.py

```



---

## 🔒 Confidentialité & Éthique

* **Privacy by Design :** Aucune donnée personnelle n'est collectée.
* **Éphémérité :** Les conversations sont stockées en RAM et supprimées après 30 minutes d'inactivité.
* **Éthique :** ORIA est une IA, elle ne remplace pas le lien humain mais le prépare.

---

## 👥 Équipe

Projet réalisé avec passion par **Ikram** et **Evan** au sein du **RedDrop Lab**.

> **Avertissement Légal :** ORIA fournit des informations à but pédagogique uniquement. En cas de doute, consultez toujours un professionnel de santé.
