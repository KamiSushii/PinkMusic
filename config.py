import discord

#Config file
YOUTUBE_REGEX = r"^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|v\/)?)([\w\-]+)(\S+)?$"
YOUTUBEPL_REGEX = r"(?:https?:\/\/)?(?:youtu\.be\/|(?:www\.|m\.)?youtube\.com\/(?:playlist|list|embed)(?:\.php)?(?:\?.*list=|\/))([a-zA-Z0-9\-_]+)"
TOKEN = 'OTk4NDY4MzAzMjAwNzMxMjI2.GLtQbk.ztwfzX0Jkt7Ave3Co4_tqll1K62bt5dL7q4CGU'
OPTIONS = {
    "1️⃣": 0,
    "2️⃣": 1,
    "3️⃣": 2,
    "4️⃣": 3,
    "5️⃣": 4,
}

template = {
    '__colour':discord.Colour.nitro_pink(),
}

nodes = {
            "node1": {
                "host": "node1.gglvxd.tk",
                "port": 443,
                "password": "free",
                "identifier": "pinkMusic1",
                "region": "asia",
                "https": True,
            },
            # "node2": {
            #     "host": "lava.link",
            #     "port": 80,
            #     "password": "youshallnotpass",
            #     "identifier": "pinkMusic2",
            # },
            # "node3": {
            #     "host": "lavalink.oops.wtf",
            #     "port": 443,
            #     "password": "www.freelavalink.ga",
            #     "identifier": "pinkMusic3",
            #     "https": True
            # }
}