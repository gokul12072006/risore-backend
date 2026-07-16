from src.web_search import fetch_crypto_api, fetch_universal_search

print("Testing Crypto API for Beldex in INR...")
crypto_res = fetch_crypto_api("What is the price of beldex in INR?")
print("Crypto Result:", crypto_res)

print("Testing Universal Search for Beldex price...")
univ_res = fetch_universal_search("What is the price of beldex in INR?")
print("Universal Result:", univ_res)
