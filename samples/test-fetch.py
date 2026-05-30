from tools.get_wikipedia_article import get_wikipedia_article

result = get_wikipedia_article("Winston Churchill")

if "error" in result:
    print("Error:", result)
else:
    print("Title:", result["title"])
    print("URL:", result["url"])
    print(f"Content length: {len(result['content'])} chars")
    print(result["content"])
