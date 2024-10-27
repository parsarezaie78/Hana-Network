import asyncio
from web3 import Web3
import json
import random
from colorama import init, Fore, Style
from datetime import datetime

init(autoreset=True)

def print_header():
    header = """
    ███████╗████████╗ █████╗ ██╗     ██╗     
    ██╔════╝╚══██╔══╝██╔══██╗██║     ██║     
    ███████╗   ██║   ███████║██║     ██║     
    ╚════██║   ██║   ██╔══██║██║     ██║     
    ███████║   ██║   ██║  ██║███████╗███████╗
    ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚══════╝╚══════╝
        t.me/dpangestuw31
    Auto Deposit ETH for HANA Network
    """
    print(Fore.CYAN + Style.BRIGHT + header + Style.RESET_ALL)

RPC_URL = "https://mainnet.base.org"
CONTRACT_ADDRESS = "0xC5bf05cD32a14BFfb705Fb37a9d218895187376c"
AMOUNT_ETH = 0.0000001  

web3 = Web3(Web3.HTTPProvider(RPC_URL))

num_transactions_total = int(input(Fore.YELLOW + "Enter the number of transactions to be executed: " + Style.RESET_ALL))
print_header()

with open("pvkey.txt", "r") as file:
    private_keys = [line.strip() for line in file if line.strip()]

contract_abi = '''
[
    {
        "constant": false,
        "inputs": [],
        "name": "depositETH",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]
'''

amount_wei = web3.to_wei(AMOUNT_ETH, 'ether')
contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=json.loads(contract_abi))

nonces = {key: web3.eth.get_transaction_count(web3.eth.account.from_key(key).address) for key in private_keys}

transactions_per_account = {key: {'sent': 0, 'remaining': num_transactions_total} for key in private_keys}

async def send_transaction(private_key, delay):
    from_address = web3.eth.account.from_key(private_key).address
    short_from_address = from_address[:4] + "..." + from_address[-4:]
    
    # Get current time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        transaction = contract.functions.depositETH().build_transaction({
            'from': from_address,
            'value': amount_wei,
            'gas': 50000,
            'gasPrice': web3.eth.gas_price,
            'nonce': nonces[private_key],
        })

        signed_txn = web3.eth.account.sign_transaction(transaction, private_key=private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # Shorten the transaction hash
        short_tx_hash = tx_hash.hex()[:6] + "..." + tx_hash.hex()[-4:]

        # Update and display account-specific transaction status
        transactions_per_account[private_key]['sent'] += 1
        transactions_per_account[private_key]['remaining'] -= 1
        
        print(Fore.GREEN + f"\n[{current_time}] [{short_from_address}] [✓] Transaction sent")
        print(Fore.GREEN + f"    Hash: {short_tx_hash}")
        print(Fore.BLUE + f"Account {short_from_address} - Sent: {transactions_per_account[private_key]['sent']}, Remaining: {transactions_per_account[private_key]['remaining']}")

        nonces[private_key] += 1
        await asyncio.sleep(delay)

    except Exception as e:
        error_message = str(e)
        if 'nonce too low' in error_message:
            print(Fore.YELLOW + f"\n[{current_time}] [{short_from_address}] [!] Nonce too low. Fetching the latest nonce...")
            nonces[private_key] = web3.eth.get_transaction_count(from_address)
        else:
            print(Fore.RED + f"\n[{current_time}] [{short_from_address}] [✗] Error sending transaction: {error_message}")

async def main():
    tasks = []
    for _ in range(num_transactions_total):
        for private_key in private_keys:
            delay = random.randint(0, 5)
            tasks.append(send_transaction(private_key, delay))
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
    print(Fore.MAGENTA + "\nFinished sending transactions." + Style.RESET_ALL)
