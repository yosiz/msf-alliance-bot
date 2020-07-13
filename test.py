from datetime import datetime
import json

colors = {
    "❤️": 731625542490783814,  # red
    "💛": 731625689660522556,  # yellow
    "💚": 731625734338248775,  # green
    "💙": 731625764981702716,  # blue
    "💜": 731625799307755660,  # purple
}

# with open("data/db/guilds/1","w") as f:
#     json.dump(colors,f)
#
# with open("data/db/guilds/1","r") as f:
#     data = json.load(f)
#
# print(data)
# print(data.keys())
#
# from lib.db import db
#
# version = db.record("PRAGMA user_version")
# # b = db.record("SELECT COUNT(*) AS CNT FROM pragma_table_info('guilds') WHERE name = ?", "StarredChannel")
#
# if version:
#     version = version[0]
#     print(version)
#     db.execute(f"PRAGMA user_version = {version + 1}")
#     print(db.record("PRAGMA user_version"))
def check_xp_formula():
    from random import randint
    xp = 0
    lvl =0

    for i in range(1000):
        xp +=randint(10,20)
        lvl = int(((xp)//42)**0.55)
        print(i+1,xp,lvl)


if __name__ == '__main__':
    check_xp_formula()
