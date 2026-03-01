from backend.scrapers.amazon.scrape_amazon_titles import scrape_amazon_product_page

url = "https://www.amazon.co.uk/Avlash%C2%AE-Disposable-Biodegradable-Cutlery-Friendly/dp/B09S3VF6Z4/ref=sr_1_2_sspa?crid=3LJJEN0C4SSVJ&dib=eyJ2IjoiMSJ9.hhQqlbb3KAvzwAX-2Wsotk6mM853QcQmq2Hy8ZtPK4WnT4n84yFZ-tMQ-dmvL0K6cK8bUBuolmW7-lyPA7qobuWMyV_u2DpYxsN7aHFflVBSTW9aiagaLrTfpEg7sDgdW2nAwh6hxPW-iHE_ojAqvXnGcSv2j_wGFkm_zYwiswaMrAtLcA-eggCc8MEBApds4UCJQENwUZR02ggMhN_G6XGLmE5gG5CVQz6ppgUq-cg4h6T7XggpvP18pp1wMrWW7Cy9lBTJp7tJCjfc0YK_zIrP-A3H8AUjl9scG0utNGQ.hNbX0hZYj9Fi5-Gwo8NPcVU62WEo8HRs1M5dhIFoXHA&dib_tag=se&keywords=spoon&qid=1772031780&sprefix=spoo%2Caps%2C235&sr=8-2-spons&aref=09gVzRnz5y&sp_csd=d2lkZ2V0TmFtZT1zcF9hdGY&th=1"

result = scrape_amazon_product_page(url, fallback=False)
print({
    "title": result.get("title"),
    "brand": result.get("brand"),
    "origin": result.get("origin"),
    "country_of_origin": result.get("country_of_origin"),
    "origin_source": result.get("origin_source"),
})
