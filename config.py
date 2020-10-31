#-------------------------------------------------#
#             Bot Configuration File              #
#-------------------------------------------------#

# Open token file (so the repository doesn't receive the token and the config can still be pushed)
with open('token.txt','r') as file:
    token = file.read()

# System Basics
token = token.strip()
prefix = "?"
description = "Oe skxawng asrunga' lu."
version = "1.2.2"
operators = [423581502970789889,189504650645471232,205370567614922753,429361033446948864, 81105065955303424]
bot_channel = 718309398048538687

# These need to be Anaru's directory
repo = r"F:\Ewo\.git"
directory = r"F:\Ewo"
