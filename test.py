from modules.marteso import MartesoClient

client = MartesoClient()

result = client.search_keyword(
    "habit tracker",
    "us",
    "en"
)

print(result)
