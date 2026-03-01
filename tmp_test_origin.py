import requests

url = "http://127.0.0.1:5000/estimate_emissions"
payload = {
    "amazon_url": "https://www.amazon.co.uk/Avlash%C2%AE-Disposable-Biodegradable-Cutlery-Friendly/dp/B09S3VF6Z4/ref=sr_1_2_sspa?crid=3LJJEN0C4SSVJ&dib=eyJ2IjoiMSJ9.hhQqlbb3KAvzwAX-2Wsotk6mM853QcQmq2Hy8ZtPK4WnT4n84yFZ-tMQ-dmvL0K6cK8bUBuolmW7-lyPA7qobuWMyV_u2DpYxsN7aHFflVBSTW9aiagaLrTfpEg7sDgdW2nAwh6hxPW-iHE_ojAqvXnGcSv2j_wGFkm_zYwiswaMrAtLcA-eggCc8MEBApds4UCJQENwUZR02ggMhN_G6XGLmE5gG5CVQz6ppgUq-cg4h6T7XggpvP18pp1wMrWW7Cy9lBTJp7tJCjfc0YK_zIrP-A3H8AUjl9scG0utNGQ.hNbX0hZYj9Fi5-Gwo8NPcVU62WEo8HRs1M5dhIFoXHA&dib_tag=se&keywords=spoon&qid=1772031780&sprefix=spoo%2Caps%2C235&sr=8-2-spons&aref=09gVzRnz5y&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1",
    "postcode": "SW1A 1AA",
    "include_packaging": True,
}

r = requests.post(url, json=payload, timeout=120)
print("status", r.status_code)
try:
    data = r.json()
    attrs = data.get("data", {}).get("attributes", {})
    print("country_of_origin", attrs.get("country_of_origin"))
    print("origin_source", attrs.get("origin_source"))
except Exception as error:
    print("json_error", error)
    print(r.text[:400])
