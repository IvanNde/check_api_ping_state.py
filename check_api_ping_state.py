#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import sys
import argparse
import json

def nagios_exit(status_code, message):
    """Formate la sortie et quitte le script avec le bon code de statut."""
    status_text = {0: "OK", 1: "WARNING", 2: "CRITICAL", 3: "UNKNOWN"}.get(status_code, "UNKNOWN")
    print(f"{status_text}: {message}")
    sys.exit(status_code)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='A state checker plugin that relies on a "success" flag from an API.')

    # Arguments de connexion à l'API
    parser.add_argument('--api-host', required=True, help='Hostname or IP of the collector API')
    parser.add_argument('--api-port', type=int, default=8000, help='Port of the collector API')
    parser.add_argument('--target-id', required=True, help='The numeric ID of the target server')
    parser.add_argument('--ssl', action='store_true', help='Use HTTPS for the API call')

    # NOTE: Il n'y a plus d'arguments pour les seuils (-w, -c)

    args = parser.parse_args()

    # 1. Construire l'URL et appeler l'API avec GET
    protocol = "https" if args.ssl else "http"
    url = f"{protocol}://{args.api_host}:{args.api_port}/ping/{args.target_id}/"
    headers = {'Accept': 'application/json'}

    try:
        response = requests.get(url, headers=headers, timeout=20)
        # On vérifie l'erreur 404 spécifiquement AVANT de lever une exception générale
        if response.status_code == 404:
            nagios_exit(2, f"Target server with ID '{args.target_id}' not found in API (Error 404)")

        # Si le code n'est pas 404, on vérifie les autres erreurs (500, 401, etc.)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        nagios_exit(3, f"API connection error - {e}")
    except json.JSONDecodeError:
        nagios_exit(3, f"Failed to decode JSON from API. Response: {response.text}")

    # 2. Analyser la réponse JSON en se basant uniquement sur "success" et "message"

    success_flag = data.get("success")
    message = data.get("message", "No message provided by API.")

    if success_flag is True:
        # Si le succès est explicitement vrai, tout va bien.
        nagios_exit(0, message) # Statut OK
    elif success_flag is False:
        # Si le succès est explicitement faux, c'est une erreur critique.
        nagios_exit(2, message) # Statut CRITICAL
    else:
        # Si la clé "success" n'existe pas ou est nulle (null), c'est une réponse invalide.
        nagios_exit(3, "API response is missing a valid 'success' boolean key.")