from mcp.server.mcpserver import MCPServer #inside mcp package ther eis server module adn isndie there ready made calls called FastMCP
import httpx
import os
from dotenv import load_dotenv
import asyncio

load_dotenv()
API_KEY = os.getenv("GEOAPIFY_KEY")

mcp=MCPServer("travel-concierge") #createing an instance of FastMCP class in this case the server instance

async def geocode_city(city:str) -> tuple[float,float]: #this is a helper function
    '''Turn a city name into (latitude, longitude)'''

    url = "https://api.geoapify.com/v1/geocode/search"
    params = {"text":city, "apiKey":API_KEY, "limit":1}

    async with httpx.AsyncClient() as client:
        response = await client.get(url,params=params)
        response.raise_for_status()
        data=response.json()

    features = data["features"]
    if not features:
        raise ValueError(f"Could not find location: {city}")

    lon,lat = features[0]["geometry"]["coordinates"]
    return lat, lon

@mcp.tool()
async def search_hotels(city:str, radius_km:float=3.0)->str:
    '''find hotels in or near a given city'''

    lat,lon = await geocode_city(city) 
    '''But calling an async def function doesn't run it immediately — 
    it hands you back a special object called a coroutine, 
    which is more like "a paused task, not yet started." If you wrote:
    
    result would be that coroutine object itself — not (lat, lon) at all. Then your next line, lat, lon = result, would crash, because you can't unpack a coroutine object into two variables.

await is the instruction that means "actually run this paused task now, wait for it to finish, and give me its real return value." So:'''

    url = "https://api.geoapify.com/v2/places"

    params={
        "categories":"accommodation.hotel",
        "filter":f"circle:{lon},{lat},{radius_km*1000}",
        "limit":10,
        "apiKey":API_KEY
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(url,params=params)
        response.raise_for_status()
        places=response.json()["features"]

    if not places:
        return f"No hotels found near {city}"

    lines = [f"Hotels near {city}"]
    for place in places:
        props = place["properties"]
        name = props.get("name","Unnamed hotel")
        address = props.get("formatted","")
        lines.append(f" - {name} - {address}")

    return "\n".join(lines)

@mcp.tool()
async def find_attractions_near(city:str,radiusKm:float = 3.0) -> str:
    '''this tool will help you find the attractions in a city'''

    lat,lon = await geocode_city(city)

    url="https://api.geoapify.com/v2/places"

    params={
        "apiKey":API_KEY,
        "filter":f"circle:{lon},{lat},{radiusKm *1000}",
        "categories":"tourism.attraction",
        "limit":10
    }

    async with httpx.AsyncClient() as client:
        response =await client.get(url,params=params)
        response.raise_for_status()
        data=response.json()["features"]

    if not data:
        raise ValueError(f"No attractions found in {city}")

    lines = [f"Places in {city}"]
    for attractions in data:
        attraction = attractions["properties"]
        name = attraction.get("name","street")
        address=attraction.get("formatted","")
        lines.append(f" - {name} - {address}")

    return "\n".join(lines)
        


if __name__ == "__main__":
    mcp.run(transport="streamable-http")