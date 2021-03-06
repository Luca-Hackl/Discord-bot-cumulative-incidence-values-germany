#%%

import nest_asyncio
import discord
import os

import Visualize
import WebScraping
import statistics

from dotenv import load_dotenv
from importlib import reload
from datetime import date,datetime
from sys import argv, platform
from time import time

import threading
import mysql.connector
import requests
API_URL = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/RKI_Landkreisdaten/FeatureServer/0/query?where=1%3D1&outFields=*&returnGeometry=false&outSR=4326&f=json"


if __name__ == "__main__":
    load_dotenv()
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    # check if token is present
    if TOKEN == "" or TOKEN == None:
      print("❌ No Token specified")
      print("   Run program with `DISCORD_BOT_TOKEN='<token>' python3 DiscordBot.py` or edit the .env file")
      exit(1)

    FORCEASYNCIO = False
    PREFIX = "😷"
    PRODUCTION_MODE = False

    capture_prefix = False
    for argument in argv:
        # Build prefix
        # From this point on it would probably make more sense to do the whole thing via an Args parse lib 😄
        if capture_prefix:
            if argument.startswith("-"):
                capture_prefix = False
            else:
                PREFIX += (" " if len(PREFIX) > 0 else "") + argument

        if argument == "--prefix":
            capture_prefix = True
            PREFIX = ""

        if argument == "-p":
            PRODUCTION_MODE = True

    statistics.SQLsetup()
    client = discord.Client()
    dictionary = WebScraping.generate_dict()
    response = statistics.SQLadding()
    
    @client.event
    async def on_ready():
        print("Bot started and connected to Discord...")
        now = datetime.now()
        f = now.strftime("%d.%m.%Y %H:%M")
        await client.change_presence(activity=discord.Game(name=f"({f}): {response[1]}"))

    @client.event
    async def on_message(message):
        try:
            command = message.content
            
            # Reload WebScraping module only in development mode, because among other things "requests" is quite a large module,
            # which can lead to longer waiting times.
            # Besides, you don't need the live updating in productive mode anyway.
            if not PRODUCTION_MODE:
                reload(WebScraping)

            if command.startswith(PREFIX):
                # Strip prefix from message ("😷 test" -> "test")
                county = message.content[len(PREFIX):].strip()
                
                # New update command: 😷!update to prevent prefix overloads with other discord bots

                if county == "help":

                    embed = WebScraping.helpembed()

                    await message.channel.send(embed = embed)

                elif county == "top5": 
                    
                    embed = statistics.top5()

                    await message.channel.send(embed=embed)


                elif county[:5] == "stats":               
                    
                    croppedinput = county[6:]   #getting rid of the stats  
                    if croppedinput.find(" vs ") != -1:
                        
                        img = Visualize.statscompare(croppedinput)             
            
                    else:
                        
                        img = Visualize.barplot(croppedinput)  
                        
                    await message.channel.send(file=discord.File(img))    
    

                elif county[:4] == "line":               

                    croppedinput = county[5:]   #getting rid of the line                       
                    
                    
                    if croppedinput.find(" vs ") != -1:
                        
                        img = Visualize.scatterplotcomp(croppedinput)            
            
                    else:
                        
                        img = Visualize.scatterplot(croppedinput)  
                        
                    await message.channel.send(file=discord.File(img))    
                
                else:     
                    states = {"Brandenburg": "BB", "Berlin": "BE", 
                    "Baden-Württemberg": "BW", "Bayern": "BY", 
                    "Bremen": "HB", "Hessen": "HE", "Hamburg": "HH", 
                    "Mecklenburg-Vorpommern": "MV", "Niedersachsen": "NI",
                    "Nordrhein-Westfalen": "NW", "Rheinland-Pfalz": "RP",
                    "Schleswig-Holstein": "SH", "Saarland": "SL",
                    "Sachsen": "SN", "Sachsen-Anhalt": "ST", "Thüringen": "TH"}

                    
                    if county in states: 
                        embed = statistics.statesearch(county)

                        await message.channel.send(content=f"*Fetched*", embed=embed)

                    elif county in states.values():

                        key_list = list(states.keys())
                        val_list = list(states.values())

                        position = val_list.index(county)
                        state = key_list[position]

                        embed = statistics.statesearch(state)

                        await message.channel.send(content=f"*Fetched*", embed=embed)
                        

                    else:

                        embed, time_start = WebScraping.discordstring(county, dictionary)
                        fetch_time = round((time()-time_start)*1000, 2)
                        msg = await message.channel.send(f"⏰ Searching for county **{county}**...")

                        await msg.edit(content=f"*Fetched in **{fetch_time}ms***", embed=embed)
    
        except Exception as e:
            print("Error occured: " + e)


    if FORCEASYNCIO or not (platform == "win32" or platform == "win64"):
        print("👉 Using nest_asyncio")
        import nest_asyncio
        nest_asyncio.apply()
    client.run(TOKEN)


# %%