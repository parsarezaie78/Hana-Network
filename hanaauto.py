import aiohttp
import asyncio
import json
import logging
import math
import random
import traceback
from colorama import Fore, Style

# Konfigurasi logging
logging.basicConfig(filename='hana_auto_grow.log', level=logging.INFO)
API_KEY = "AIzaSyDipzN0VRfTPnMGhQ5PSzO27Cxm3DohJGY"  # Ganti dengan API Key Anda
GRAPHQL_URL = "https://hanafuda-backend-app-520478841386.us-central1.run.app/graphql"

async def refresh_access_token(session, refresh_token):
    url = f"https://securetoken.googleapis.com/v1/token?key={API_KEY}"
    headers = {"Content-Type": "application/json"}
    body = json.dumps({"grant_type": "refresh_token", "refresh_token": refresh_token})

    print(Fore.YELLOW + "Refreshing access token..." + Style.RESET_ALL)
    async with session.post(url, headers=headers, data=body) as response:
        if response.status != 200:
            error_response = await response.json()
            print(Fore.YELLOW + f"Failed to refresh access token: {error_response['error']}" + Style.RESET_ALL)
            raise Exception(f"Failed to refresh access token: {error_response['error']}")
        
        return await response.json()

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

async def execute_graphql_query(session, headers, query, variables=None):
    try:
        async with session.post(GRAPHQL_URL, headers=headers, json={"query": query, "variables": variables}) as response:
            response.raise_for_status()
            return await response.json()
    except Exception as e:
        logging.error(f"GraphQL request failed: {e}")
        raise

async def get_user_total_points(session, headers):
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
    async with session.post(GRAPHQL_URL, headers=headers, json={"query": query_current_user}) as response:
        if response.status == 200:
            current_user_data = await response.json()
            return current_user_data['data']['currentUser']['totalPoint']
        else:
            raise Exception("Failed to retrieve current user information.")

async def process_account(session, account):
    try:
        refresh_token = account['refresh_token']
                
        # Refresh the access token
        try:
            token_response = await refresh_access_token(session, refresh_token)
            refresh_token = token_response.get("access_token")
            print("sukses")
        except:
            refresh_token = account['refresh_token']
        access_token = refresh_token  

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        query_get_garden = """
        query GetGardenForCurrentUser {
            getGardenForCurrentUser {
                id
                inviteCode
                gardenDepositCount
                gardenStatus {
                    id
                    activeEpoch
                    growActionCount
                    gardenRewardActionCount
                }
                gardenMilestoneRewardInfo {
                    id
                    gardenDepositCountWhenLastCalculated
                    lastAcquiredAt
                    createdAt
                }
                gardenMembers {
                    id
                    sub
                    name
                    iconPath
                    depositCount
                }
            }
        }
        """
        
        garden_data = await execute_graphql_query(session, headers, query_get_garden)
        garden_status = garden_data['data']['getGardenForCurrentUser']['gardenStatus']
        garden_members = garden_data['data']['getGardenForCurrentUser']['gardenMembers']

        total_grows = garden_status['growActionCount']
        total_rewards = garden_status['gardenRewardActionCount']

        if garden_members:
            nama_akun = garden_members[0]['name']
            id_akun = garden_members[0]['id']
        else:
            nama_akun = "Unknown"
            id_akun = "Unknown"

        print_message(f"Account: {nama_akun} (ID: {id_akun})", Fore.GREEN)
        print_message(f"Total Grows: {total_grows}, Total Rewards: {total_rewards}", Fore.BLUE)

        for _ in range(total_grows):
            try:
                await execute_graphql_query(session, headers, "mutation issueGrowAction { issueGrowAction }")
                await execute_graphql_query(session, headers, "mutation commitGrowAction { commitGrowAction }")

                total_points = await get_user_total_points(session, headers)
                print_message(f"Grow action completed for {nama_akun}. Current Total Points: {total_points}", Fore.YELLOW)
                await asyncio.sleep(random.randint(1, 5))
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
        for _ in range(steps - 1):
            try:
                rewards_data = await execute_graphql_query(session, headers, mutation_execute_garden_reward, {"limit": 10})
                new_cards = [
                    f"Card ID: {card['data']['cardId']}, Group: {card['data']['group']}"
                    for card in rewards_data['data']['executeGardenRewardAction']
                    if card.get('isNew')
                ]
                print_message("; ".join(new_cards), Fore.MAGENTA)
                await asyncio.sleep(random.randint(1, 5))
            except Exception as inner_e:
                error_traceback = traceback.format_exc()
                logging.error(f"Failed reward action for account {account.get('name', '')}: {inner_e}\n{error_traceback}")
                print_message(f"Error during reward action: {inner_e}\n{error_traceback}", Fore.RED)

    except Exception as e:
        error_traceback = traceback.format_exc()
        logging.error(f"Error processing account {account.get('name', '')}: {e}\n{error_traceback}")
        print_message(f"Error: {e}\n{error_traceback}", Fore.RED)


async def main():
    accounts = load_tokens_from_file()
    async with aiohttp.ClientSession() as session:
        while True:
            tasks = [process_account(session, account) for account in accounts]
            await asyncio.gather(*tasks)
            await asyncio.sleep(random.randint(5 * 60, 10 * 60))

if __name__ == "__main__":
    print_intro()
    asyncio.run(main())
