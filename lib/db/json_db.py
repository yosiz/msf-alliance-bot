import os
import json
import jsonpickle
datapath = "./data/db/guilds/"


def add_guild(guild_id):
    os.makedirs(f"{datapath}{guild_id}", exist_ok=True)


def save_section(guild_id, section, data):
    add_guild(guild_id)
    frozen = jsonpickle.encode(data)

    with open(f"{datapath}{guild_id}/{section}.json", "w") as f:
        json.dump(data, f)


def read_section(guild_id, section):
    with open(f"{datapath}{guild_id}/{section}.json", "r") as f:
        data = json.load(f)
    return data


class DB():
    def __init__(self, guild_id):
        self.guild_id = guild_id

    def save(self, section, data):
        with open(f"{datapath}{self.guild_id}/{section}.json") as f:
            json.dump(data, f)
