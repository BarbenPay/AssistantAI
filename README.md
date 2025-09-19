Assistant IA Personnel
Ce projet est un assistant personnel intelligent en ligne de commande, conçu pour vous aider à gérer vos tâches quotidiennes, votre agenda et vos e-mails de manière fluide et intuitive.

✨ Fonctionnalités
Gestion de Tâches : Ajoutez, suivez et mettez à jour une liste de tâches avec des priorités et des dates d'échéance. Les tâches sont sauvegardées dans une base de données locale.

Intégration Google Agenda : Consultez vos prochains rendez-vous, ajoutez de nouveaux événements et supprimez-les directement depuis la console.

Analyse d'E-mails : Connectez-vous à votre boîte de réception pour analyser vos e-mails non lus. L'assistant utilise l'IA pour résumer le contenu, évaluer l'importance et suggérer des actions.

Recommandations Intelligentes : Obtenez des suggestions sur les prochaines actions à entreprendre en fonction d'une analyse combinée de vos e-mails et de votre agenda.

Traitement du Langage Naturel : Interagissez avec l'assistant en utilisant des phrases simples et naturelles.

🔧 Comment ça fonctionne ?
Le projet utilise une architecture Manager-Agents. Le manager.py sert de coordinateur central. Lorsque vous entrez une commande, il utilise l'API Gemini pour comprendre votre intention, puis il délègue la tâche à l'agent spécialisé approprié (task_agent, agenda_agent, ou email_agent).

🚀 Installation
Suivez ces étapes pour configurer et lancer le projet sur votre machine.

1. Prérequis

Python 3.8 ou supérieur

Un compte Google pour accéder à l'API Google Calendar et Gmail.

Une clé d'API pour Google Gemini (disponible sur Google AI Studio).

2. Configuration Initiale

Clonez le projet (ou téléchargez les fichiers) sur votre machine.

Créez un environnement virtuel (recommandé) :

Bash
python -m venv venv
source venv/bin/activate  # Sur Windows: venv\Scripts\activate
Installez les dépendances :
Créez un fichier requirements.txt avec le contenu suivant :

Plaintext
google-generativeai
python-dotenv
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
Puis installez-le :

Bash
pip install -r requirements.txt
3. Configuration des Accès

API Google Calendar :

Suivez ce guide rapide pour activer l'API Google Calendar et télécharger votre fichier credentials.json.

Placez le fichier credentials.json dans le dossier config/.

La première fois que vous utiliserez une commande liée à l'agenda, une page d'authentification Google s'ouvrira dans votre navigateur. Autorisez l'accès pour générer un fichier token.json qui stockera vos identifiants.

Informations d'Identification :

Créez un fichier nommé .env dans le dossier config/.

Ajoutez-y les informations suivantes :

Extrait de code
# Clé API obtenue depuis Google AI Studio
GEMINI_API_KEY="VOTRE_CLÉ_API_GEMINI"

# Votre adresse e-mail Gmail
EMAIL_ADDRESS="votre_email@gmail.com"

# Mot de passe d'application pour Gmail (NE PAS utiliser votre mot de passe principal)
# Suivez ce guide pour en créer un : https://support.google.com/accounts/answer/185833
EMAIL_PASSWORD="votre_mot_de_passe_application"
▶️ Utilisation
Pour démarrer l'assistant, exécutez le script manager.py depuis la racine du projet :

Bash
python manager.py
L'assistant affichera Entrez votre commande :. Vous pouvez alors taper l'une des commandes ci-dessous. Pour quitter, tapez quitter.

📋 Commandes Disponibles
✅ Gestion des Tâches

Commande

Exemple

Résultat Attendu

ajoute la tâche [description]

ajoute la tâche faire les courses

Confirme l'ajout de la tâche avec une priorité par défaut.

ajoute la tâche urgente [description] pour [date/demain]

ajoute la tâche urgente Finir le rapport pour demain

Ajoute une tâche avec une priorité haute (1) et une date d'échéance.

montre-moi les tâches

liste les tâches

Affiche toutes les tâches non terminées, classées par priorité.

montre-moi les tâches [à faire/en cours/terminées]

montre-moi les tâches terminées

Filtre et affiche les tâches selon le statut demandé.

passe la tâche [mot-clé] au statut [en cours/terminé]

passe la tâche 'faire les courses' au statut terminé

Met à jour le statut de la tâche et affiche une confirmation.

supprime la tâche [mot-clé]

supprime la tâche faire les courses

Supprime la tâche. Si plusieurs tâches correspondent, il vous demandera de préciser.

📅 Gestion de l'Agenda

Commande

Exemple

Résultat Attendu

montre-moi mon agenda

montre-moi mon agenda

Affiche les 10 prochains événements de votre Google Calendar.

ajoute '[nom]' le [date]

ajoute 'Rdv docteur' le 30 juillet

Crée un événement dans votre Google Calendar et confirme sa création.

supprime l'événement [mot-clé]

supprime l'événement 'Rdv docteur'

Recherche et supprime l'événement correspondant de votre calendrier.

📧 Gestion des E-mails

Commande

Exemple

Résultat Attendu

analyse mes emails

analyse mes emails

Affiche un résumé, le niveau d'importance et l'action suggérée pour vos 5 derniers e-mails non lus.

🤖 Recommandations de l'Assistant

Commande

Exemple

Résultat Attendu

donne-moi une recommandation

qu'est ce que je peux faire

Fournit un plan d'action priorisé basé sur l'analyse de vos e-mails récents et de votre agenda.

qu'est ce que j'ai d'urgent à faire aujourd'hui

qu'est ce que j'ai d'urgent à faire

Identifie et affiche les actions les plus critiques à réaliser le jour même.