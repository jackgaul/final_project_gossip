# import redis

# redis_client = redis.StrictRedis(host='localhost', port=6379, db=0, decode_responses=True)

# games = redis_client.hgetall('games')

# print(type(games))
# print(games)

mydict = {1: 'Geeks', 2: 'for', 3: 'geeks'}
keysList = list(mydict.keys())[0]
print(keysList)
