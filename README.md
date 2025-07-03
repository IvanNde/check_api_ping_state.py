# Documentation du Plugin : `check_api_ping_state.py`

## 1. Objectif

Ce script Python est un plugin de supervision pour Centreon (compatible Nagios) conçu pour vérifier l'état de la connectivité d'une machine cible en interrogeant une API de collecte centralisée.

Son rôle n'est pas de mesurer la latence, mais de déterminer un état binaire : **OK** (joignable) ou **CRITICAL** (injoignable ou mal configuré). Il se base sur un simple indicateur de succès (`"success": true/false`) retourné par l'API.

## 2. Fonctionnalités Clés

*   **Vérification d'État** : Retourne un statut `OK` ou `CRITICAL` basé sur la réponse de l'API, sans dépendre de seuils de performance.
*   **Requêtes GET** : Utilise la méthode HTTP `GET` pour récupérer l'état, ce qui est standard pour une simple lecture d'information.
*   **Gestion Robuste des Erreurs** :
    *   **Configuration Incorrecte (404 Not Found)** : Si un ID de serveur inexistant est demandé, le plugin retourne un statut `CRITICAL` avec un message clair, indiquant une erreur de configuration.
    *   **Erreurs de Communication** : Gère les problèmes de connexion à l'API (timeout, erreur DNS, erreur serveur 5xx) en retournant un statut `UNKNOWN`.
    *   **Réponse Invalide** : Gère les cas où la réponse de l'API n'est pas un JSON valide ou ne contient pas la clé `"success"`.
*   **Haute Réutilisabilité** : Le plugin est conçu pour être utilisé avec une seule commande Centreon pour superviser la connectivité de multiples serveurs.
*   **Simplicité** : Ne nécessite aucun argument complexe (comme les seuils), ce qui simplifie grandement la configuration dans Centreon.
*   **Sécurité** : Le script supporte les connexions HTTPS (`--ssl`).

## 3. Prérequis

*   **Sur le collecteur (Poller) Centreon :**
    *   Python 3.
    *   La librairie Python `requests`. Si elle n'est pas installée :
        ```bash
        # Sur RHEL/CentOS/Rocky Linux
        sudo dnf install python3-requests
        # Sur Debian/Ubuntu
        sudo apt install python3-requests
        ```
*   **API Collecteur :**
    *   L'API doit être accessible depuis le collecteur Centreon.
    *   Elle doit exposer un endpoint `GET` qui accepte un ID de serveur dans l'URL (ex: `/ping/{id}/`).
    *   En cas de succès, elle doit retourner un JSON avec `"success": true` et un `"message"`.
    *   En cas d'échec de connectivité, elle doit retourner un JSON avec `"success": false` et un `"message"` décrivant l'erreur.
    *   Si l'ID du serveur n'existe pas, elle doit retourner un code HTTP **404 Not Found**.

## 4. Installation

1.  Copiez le fichier `check_api_ping_state.py` dans le répertoire des plugins de Centreon sur votre collecteur.
    ```bash
    sudo cp check_api_ping_state.py /usr/lib/centreon/plugins/
    ```
2.  Rendez le script exécutable.
    ```bash
    sudo chmod +x /usr/lib/centreon/plugins/check_api_ping_state.py
    ```
3.  Assurez-vous que le propriétaire du fichier est l'utilisateur du moteur Centreon.
    ```bash
    sudo chown centreon-engine:centreon-engine /usr/lib/centreon/plugins/check_api_ping_state.py
    ```

## 5. Utilisation en Ligne de Commande

### Syntaxe
```bash
./check_api_ping_state.py --api-host <HOST> --api-port <PORT> --target-id <ID> [OPTIONS]
```

### Arguments

| Argument      | Description                                                                 | Obligatoire |
|---------------|-----------------------------------------------------------------------------|-------------|
| `--api-host`  | L'adresse IP ou le nom d'hôte de votre API collecteur.                      | Oui         |
| `--api-port`  | Le port sur lequel votre API écoute.                                        | Oui         |
| `--target-id` | L'identifiant numérique de la machine cible, utilisé pour construire l'URL. | Oui         |
| `--ssl`       | Utiliser le protocole HTTPS au lieu de HTTP.                                | Non         |

## 6. Intégration avec Centreon

### Étape 1 : Création de la Commande de Check

1.  Naviguez vers `Configuration > Commands > Checks` et cliquez sur `Add`.
2.  Remplissez les champs comme suit :
    *   **Command Name**: `check_via_api_ping_state`
    *   **Command Type**: `Check`
    *   **Command Line**:
        ```bash
        $USER1$/check_api_ping_state.py --api-host $_HOSTAPI_ADDRESS$ --api-port $_HOSTAPI_PORT$ --target-id $_HOSTSERVERID$
        ```
        *Note : La commande est très simple et ne nécessite pas de macros pour les seuils.*

### Étape 2 : Configuration des Hôtes

*   **Hôte de l'API :**
    1.  Créez ou utilisez un hôte pour représenter votre API (ex: `My-Collector-API`).
    2.  Dans l'onglet `Host Extended Information`, ajoutez les macros :
        *   `API_ADDRESS` -> (IP de votre API)
        *   `API_PORT` -> (Port de votre API, ex: 8000)

*   **Hôte Cible (la machine à superviser) :**
    1.  Créez ou utilisez un hôte pour votre machine cible (ex: `server-web-01`).
    2.  Dans l'onglet `Host Extended Information`, ajoutez la macro pour son ID :
        *   `SERVERID` -> `1` (ou l'ID correspondant)

### Étape 3 : Configuration du Service

1.  Naviguez vers `Configuration > Services` et ajoutez un service à votre **hôte cible** (ex: `server-web-01`).
2.  Remplissez les champs :
    *   **Description**: `Ping Status`
    *   **Check Command**: Sélectionnez la commande créée précédemment : `check_via_api_ping_state`.
    *   **Arguments**: **Aucun argument n'est nécessaire.** Laissez cette section vide.
    *   **Relations**: Dans l'onglet `Relations`, pour la section "HOST", **sélectionnez l'hôte de votre API** (`My-Collector-API`). Cela permet à Centreon de trouver les macros `$_HOSTAPI_ADDRESS$` et `$_HOSTAPI_PORT$`.

### Étape 4 : Déploiement

Déployez la configuration sur votre collecteur pour appliquer les changements.

## 7. Exemples de Sorties du Plugin

*   **Cas nominal (succès) :**
    *   API répond : `{"success": true, "message": "Réponse en 10 ms"}`
    *   Sortie du plugin : `OK: Réponse en 10 ms`

*   **Cas d'échec de ping :**
    *   API répond : `{"success": false, "message": "Hôte inaccessible"}`
    *   Sortie du plugin : `CRITICAL: Hôte inaccessible`

*   **Cas d'un ID de serveur inexistant :**
    *   API répond avec un code HTTP 404.
    *   Sortie du plugin : `CRITICAL: Target server with ID '99' not found in API (Error 404)`

*   **Cas d'un problème avec l'API :**
    *   L'API ne répond pas (timeout).
    *   Sortie du plugin : `UNKNOWN: API connection error - ReadTimeout(...)`

---
Auteur: Ivan Nde
Version: 1.0
Date: 03/07/2024
