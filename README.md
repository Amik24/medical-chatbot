# Medical Chatbot – Santé féminine

Assistant conversationnel d’information en santé féminine, conçu pour orienter, poser des questions de clarification et signaler les situations à risque, sans diagnostic médical.

Démo : https://medical-chatbot-ochre.vercel.app  
Backend API : déployé sur Railway

---

## Objectif

Ce projet vise à fournir un outil de pré-orientation en santé féminine, accessible et sécurisé, permettant aux utilisatrices de :

- décrire leurs symptômes
- recevoir des informations générales à faible risque
- être orientées vers une consultation médicale si nécessaire

Ce chatbot ne remplace pas un professionnel de santé.

---

## Périmètre fonctionnel

Le chatbot répond uniquement aux sujets liés à la santé féminine, notamment :

- règles, cycle menstruel, retard de règles
- douleurs pelviennes ou abdominales
- pertes vaginales, infections urinaires ou vaginales
- contraception, grossesse, post-partum
- IST, endométriose, SOPK, ménopause

Toute question hors de ce périmètre est refusée automatiquement.

---

## Garde-fous médicaux

Le système applique des règles strictes :

- pas de diagnostic certain  
- pas de prescription  
- pas de dosage précis  
- informations générales uniquement  
- rappel systématique des services d’urgence en cas de symptômes graves

Un mécanisme de triage automatique empêche toute réponse hors santé féminine.

---

## Architecture

Frontend  
- HTML, CSS, JavaScript  
- Déployé sur Vercel  

Backend  
- FastAPI (Python)  
- Déployé sur Railway  
- Appels LLM via l’API Mistral  

Sécurité  
- Aucun stockage de données personnelles  
- Pas de comptes utilisateurs  
- Pas de conservation des conversations  

---

## Exemple d’usage

Utilisateur :  
“J’ai un retard de règles de 10 jours, est-ce normal ?”

Assistant :  
Fournit des informations générales, pose des questions de clarification, et recommande une consultation médicale si nécessaire, sans poser de diagnostic.

---

## Urgences

En cas de symptômes graves (douleur intense, saignement abondant, malaise, fièvre élevée, détresse respiratoire) :  
Appelez immédiatement le 15 ou le 112.

---

## État du projet

- Prototype fonctionnel
- Déploiement en production
- Tests utilisateurs en cours
- Amélioration continue du ton, de l’UX et de la pédagogie médicale

---

## Avertissement légal

Ce projet fournit de l’information générale uniquement.  
Il ne constitue ni un avis médical, ni un diagnostic, ni une prescription.

---

## Contact

Projet réalisé par Ikram et Evan.  
Retours et tests bienvenus.
