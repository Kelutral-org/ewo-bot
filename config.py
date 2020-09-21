#-------------------------------------------------#
#             Bot Configuration File              #
#-------------------------------------------------#

# Open token file (so the repository doesn't receive the token and the config can still be pushed)
with open('token.txt','r') as file:
    token = file.read()

# System Basics
token = token.strip()
prefix = "?"
description = "Oe skxawng asrunga' lu"
version = "0.0.1"
# Operators are people with override access to bot admin commands like reload
operators = [423581502970789889,189504650645471232,205370567614922753,429361033446948864]
status = "In Dev"
