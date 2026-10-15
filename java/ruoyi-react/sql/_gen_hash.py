import bcrypt
h = bcrypt.hashpw(b"123456", bcrypt.gensalt(rounds=10)).decode()
# Spring BCryptPasswordEncoder accepts $2a$ / $2b$
print(h.replace("$2b$", "$2a$"))
