import asyncio
import json
import random
import string

import websockets

import config

USERS = []
letters = string.ascii_uppercase.join(string.digits)

speedX = 0
speedY = 0


def find(lst, key, value):
    for i, dic in enumerate(lst):
        if dic[key] == value:
            return i
    return -1


def register(websocket):
    return USERS.append({'socket': websocket,
                         'code': ''.join(random.choice(letters) for i in range(6)),
                         'enemySocket': None,
                         'id': 0})


def unregister(websocket):
    USERS.pop(find(USERS, 'socket', websocket))


def speedGenerate():
    global speedX
    global speedY

    speedX = random.randrange(-20, 20, 3)
    speedY = random.randrange(-20, 20, 3)

    while 9 >= speedX >= -9:
        speedX = random.randrange(-20, 20, 3)

    while (9 >= speedY >= -9) or abs(speedY) > abs(speedX):
        speedY = random.randrange(-20, 20, 3)


async def start(websocket, path):
    global speedX
    global speedY

    score = 0

    register(websocket)

    try:
        await USERS[find(USERS, 'socket', websocket)]['socket'].send(
            json.dumps({'code': USERS[find(USERS, 'socket', websocket)]['code']}))
        print(USERS[find(USERS, 'socket', websocket)]['code'])

        async for message in websocket:
            thisUserIndex = find(USERS, 'socket', websocket)

            data = json.loads(message)

            dx = data.get('dx')
            goal = data.get('goal')
            code = data.get('code')

            if code:
                if find(USERS, 'code', code) != -1 and find(USERS, 'code', code) != thisUserIndex:
                    USERS[thisUserIndex]['enemySocket'] = USERS[find(USERS, 'code', code)]['socket']
                    USERS[thisUserIndex]['id'] = -1

                    USERS[find(USERS, 'code', code)]['enemySocket'] = USERS[thisUserIndex]['socket']
                    USERS[find(USERS, 'code', code)]['id'] = 1

                    speedGenerate()

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    enemyId = USERS[find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])]['id']

                    await USERS[thisUserIndex]['enemySocket'].send(
                        json.dumps({'speedX': speedX / 100 * enemyId,
                                    'speedY': speedY / 100 * enemyId}))

            if USERS[thisUserIndex]['enemySocket']:
                if goal:

                    speedGenerate()

                    score += 1

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    enemyId = USERS[find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])]['id']

                    await USERS[thisUserIndex]['enemySocket'].send(json.dumps({'speedX': speedX / 100 * enemyId,
                                                                               'speedY': speedY / 100 * enemyId,
                                                                               'score': score}))

                if dx:
                    await USERS[thisUserIndex]['enemySocket'].send(json.dumps({'dx': dx}))

            else:
                score = 0


    finally:
        if find(USERS, 'enemySocket', websocket) != -1:
            await USERS[find(USERS, 'enemySocket', websocket)]['socket'].send(
                json.dumps({'leave': 'Opponent out of the game'}))
            USERS[find(USERS, 'enemySocket', websocket)]['id'] = 0
            USERS[find(USERS, 'enemySocket', websocket)]['enemySocket'] = None

        unregister(websocket)


start_server = websockets.serve(start, config.IP, config.PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
