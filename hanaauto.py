import requests
import json
import time
import logging
import random
import math
import traceback
from colorama import Fore, Style

# Konfigurasi logging
logging.basicConfig(filename='hana_auto_grow.log', level=logging.INFO)
API_KEY = "YOUR_API_KEY"  # Ganti dengan API Key Anda
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"

def refresh_access_token(refresh_token):
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps({"grant_type": "refresh_token", "refresh_token": refresh_token})

    response = requests.post(url, headers=headers, data=body)
    print(Fore.YELLOW + "Refreshing access token..." + Style.RESET_ALL)

    if response.status_code != 200:
        error_response = response.json()
        raise Exception(f"Failed to refresh access token: {error_response['error']}")

    return response.json()

def print_intro():
    intro_text = (
        "t.me/SOGamersAirdrop\n"
        "Auto Grow and Draw for HANA Network Multi Account\n"
    )
    print(Fore.CYAN + Style.BRIGHT + intro_text + Style.RESET_ALL)

def print_message(message, color=Fore.WHITE):
    print(color + Style.BRIGHT + message + Style.RESET_ALL)

def load_tokens_from_file():
    try:
        with open("token.json", "r") as token_file:
            return json.load(token_file)
    except FileNotFoundError:
        logging.error("File 'tokens.json' not found.")
        print_message("File 'tokens.json' tidak ditemukan.", Fore.RED)
        exit()

def execute_graphql_query(headers, query, variables=None):
    try:
        response = requests.post(GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables})
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"GraphQL request failed: {e}")
        raise

def get_user_total_points(headers):
    query_current_user = """
    query CurrentUser {
        currentUser {
            id
            sub
            name
            iconPath
            depositCount
            totalPoint
            evmAddress {
                userId
                address
            }
            inviter {
                id
                name
            }
        }
    }
    """
    response_current_user = requests.post(GRAPHQL_URL, headers=headers, json={"query": query_current_user})

    if response_current_user.status_code == 200:
        current_user_data = response_current_user.json()
        user_name = current_user_data['data']['currentUser']['name']
        initial_total_point = current_user_data['data']['currentUser']['totalPoint']
        inviter = current_user_data['data']['currentUser']['inviter']['id']
        return initial_total_point
    else:
        raise Exception("Failed to retrieve current user information.")

def main():
    accounts = load_tokens_from_file()

    for account in accounts:
        try:
            refresh_token = account['refresh_token']
            access_token = refresh_token  

            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }

            query_get_garden = """
            query GetGardenForCurrentUser {
                getGardenForCurrentUser {
                    gardenStatus { growActionCount, gardenRewardActionCount }
                    gardenMembers { name, id }
                }
            }
            """
            
            garden_data = execute_graphql_query(headers, query_get_garden)
            garden_status = garden_data['data']['getGardenForCurrentUser']['gardenStatus']
            garden_members = garden_data['data']['getGardenForCurrentUser']['gardenMembers']

            total_grows = garden_status['growActionCount']
            total_rewards = garden_status['gardenRewardActionCount']
            nama_akun = garden_members[0]['name']
            id_akun = garden_members[0]['id']

            print_message(f"Account: {nama_akun} (ID: {id_akun})", Fore.GREEN)
            print_message(f"Total Grows: {total_grows}, Total Rewards: {total_rewards}", Fore.BLUE)

            for _ in range(total_grows):
                try:
                    execute_graphql_query(headers, "mutation issueGrowAction { issueGrowAction }")
                    execute_graphql_query(headers, "mutation commitGrowAction { commitGrowAction }")

                    total_points = get_user_total_points(headers)
                    print_message(f"Grow action completed for {nama_akun}. Current Total Points: {total_points}", Fore.YELLOW)
                    time.sleep(random.randint(1, 5))
                except Exception as inner_e:
                    error_traceback = traceback.format_exc()
                    logging.error(f"Failed grow action for account {account.get('name', '')}: {inner_e}\n{error_traceback}")
                    print_message(f"Error during grow action: {inner_e}\n{error_traceback}", Fore.RED)

            mutation_execute_garden_reward = """
            mutation executeGardenRewardAction($limit: Int!) {
                executeGardenRewardAction(limit: $limit) {
                    data { cardId, group }
                    isNew
                }
            }
            """
            
            steps = math.ceil(total_rewards / 10)
            for _ in range(steps-1):
                try:
                    rewards_data = execute_graphql_query(headers, mutation_execute_garden_reward, {"limit": 10})
                    new_cards = [
                        f"Card ID: {card['data']['cardId']}, Group: {card['data']['group']}"
                        for card in rewards_data['data']['executeGardenRewardAction']
                        if card.get('isNew')
                    ]
                    print_message("; ".join(new_cards), Fore.MAGENTA)
                    time.sleep(random.randint(1, 5))
                except Exception as inner_e:
                    error_traceback = traceback.format_exc()
                    logging.error(f"Failed reward action for account {account.get('name', '')}: {inner_e}\n{error_traceback}")
                    print_message(f"Error during reward action: {inner_e}\n{error_traceback}", Fore.RED)

        except Exception as e:
            error_traceback = traceback.format_exc()
            logging.error(f"Error processing account {account.get('name', '')}: {e}\n{error_traceback}")
            print_message(f"Error: {e}\n{error_traceback}", Fore.RED)

if __name__ == "__main__":
    print_intro()
    main()
