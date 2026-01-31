# 🌸 ORIA : Assistant d’Information en Santé Féminine

**ORIA** est un espace d'écoute et d'orientation conversationnel dédié à la santé des femmes. Conçu pour briser les tabous et offrir une première réponse fiable, cet assistant aide à décrypter les symptômes et oriente vers les structures de soins adaptées, sans jamais se substituer à un médecin.

🚀 **Démo Live :** [medical-chatbot-ochre.vercel.app](https://medical-chatbot-ochre.vercel.app)

⚙️ **Backend API :** Déployé sur Railway (FastAPI + Mistral AI)

---

## ✨ Objectifs du projet

Le projet répond à un besoin de pré-orientation rapide et sécurisé. ORIA permet aux utilisatrices de :

* **Libérer la parole :** Décrire des symptômes de manière anonyme et sans jugement.
* **Comprendre :** Recevoir des informations pédagogiques sur le fonctionnement du corps.
* **S'orienter :** Savoir quand une consultation est nécessaire et quel spécialiste solliciter.

---

## 🛠 Architecture Technique

Le projet repose sur une stack moderne privilégiant la performance et la légèreté :

| Composant | Technologie | Hébergement |
| --- | --- | --- |
| **Frontend** | HTML5, CSS3 (Modern UI), JavaScript | **Vercel** |
| **Backend** | Python, FastAPI | **Railway** |
| **Intelligence** | Mistral AI (via API) | - |
| **Sécurité** | Privacy by Design (0 stockage) | - |

---

## 🩺 Périmètre & Garde-fous

### 🎯 Sujets couverts

Le chatbot est spécialisé dans la santé hormonale et gynécologique :

* **Cycles :** Règles douloureuses, irrégularités, syndrome prémenstruel (SPM).
* **Pathologies :** Endométriose, SOPK, infections (urinaires/vaginales), IST.
* **Vie reproductive :** Contraception, grossesse, post-partum, ménopause.

### 🛡 Sécurité Médicale (Safety First)

ORIA intègre des règles strictes de "Triage" :

1. **Zéro Diagnostic :** L'assistant suggère des hypothèses mais ne pose jamais de diagnostic définitif.
2. **Zéro Prescription :** Aucune recommandation de médicament ou de posologie.
3. **Filtrage Hors-Sujet :** Toute question non liée à la santé féminine est redirigée vers le périmètre de compétence de l'IA.

---

## 🚨 Protocoles d'Urgence Internationaux

En cas de détection de symptômes critiques (douleur aiguë, hémorragie, détresse respiratoire), ORIA affiche immédiatement les numéros de secours selon la zone géographique :

* **🇫🇷 France :** Appelez le **15** ou le **112**.
* **🇨🇭 Suisse :** Appelez le **144** ou le **112**.
* **🇩🇪 Allemagne :** Appelez le **112**.

---

## 🔒 Confidentialité & Éthique

Conformément aux enjeux de santé, ORIA respecte la vie privée :

* **Anonymat total :** Aucune donnée personnelle (nom, email) n'est demandée.
* **Pas de logs :** Les conversations ne sont ni stockées, ni utilisées pour l'entraînement de modèles tiers.
* **Transparence :** L'utilisatrice est informée dès le début qu'elle discute avec une IA.

---

## 👥 Équipe & Contact

Projet réalisé avec passion par **Ikram** et **Evan**.


> **Avertissement Légal :** ORIA fournit des informations à but pédagogique uniquement. En cas de doute, consultez toujours un professionnel de santé ou contactez les services d'urgence.