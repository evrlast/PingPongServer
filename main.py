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
                         'name': '',
                         'id': 0,
                         'score': 0,
                         'isReady': False,
                         'enemySocket': None,
                         'enemyName': ''})


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
            name = data.get('name')
            back = data.get('exit')
            play = data.get('playAgain')

            if play:
                index = find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])

                USERS[thisUserIndex]['isReady'] = True

                if USERS[thisUserIndex]['isReady'] and USERS[index]['isReady']:
                    enemyId = USERS[find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])]['id']
                    speedGenerate()
                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'enemyName': USERS[thisUserIndex]['enemyName'],
                                    'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    await USERS[thisUserIndex]['enemySocket'].send(
                        json.dumps({'enemyName': USERS[thisUserIndex]['name'],
                                    'speedX': speedX / 100 * enemyId,
                                    'speedY': speedY / 100 * enemyId}))

            if back:
                await USERS[thisUserIndex]['enemySocket'].send(
                    json.dumps({'leave': 1}))

                USERS[thisUserIndex]['id'] = 0
                USERS[thisUserIndex]['score'] = 0
                USERS[thisUserIndex]['enemySocket'] = None
                USERS[thisUserIndex]['enemyName'] = ''

            if name:
                USERS[thisUserIndex]['name'] = name
                USERS[thisUserIndex]['score'] = 0

            if code:
                index = find(USERS, 'code', code)
                if index != -1 and index != thisUserIndex and USERS[index]['name'] != '':
                    USERS[thisUserIndex]['enemySocket'] = USERS[index]['socket']
                    USERS[thisUserIndex]['enemyName'] = USERS[index]['name']
                    USERS[thisUserIndex]['id'] = -1
                    USERS[thisUserIndex]['isReady'] = True

                    USERS[index]['enemySocket'] = USERS[thisUserIndex]['socket']
                    USERS[index]['enemyName'] = USERS[thisUserIndex]['name']
                    USERS[index]['id'] = 1
                    USERS[index]['isReady'] = True

                    speedGenerate()

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'enemyName': USERS[thisUserIndex]['enemyName']}))
                    await USERS[thisUserIndex]['enemySocket'].send(
                        json.dumps({'enemyName': USERS[thisUserIndex]['name']}))

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    enemyId = USERS[find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])]['id']

                    await USERS[thisUserIndex]['enemySocket'].send(
                        json.dumps({'speedX': speedX / 100 * enemyId,
                                    'speedY': speedY / 100 * enemyId}))
                else:
                    await USERS[thisUserIndex]['socket'].send(json.dumps({'codeError': 1}))

            index = find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])

            if USERS[thisUserIndex]['isReady'] and USERS[index]['isReady']:
                if goal:
                    speedGenerate()

                    USERS[thisUserIndex]['score'] += 1

                    enemyId = USERS[find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])]['id']

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    await USERS[thisUserIndex]['enemySocket'].send(
                        json.dumps({'speedX': speedX / 100 * enemyId,
                                    'speedY': speedY / 100 * enemyId,
                                    'score': USERS[thisUserIndex]['score']}))

                    if USERS[thisUserIndex]['score'] >= 11:
                        index = find(USERS, 'socket', USERS[thisUserIndex]['enemySocket'])

                        USERS[thisUserIndex]['score'] = 0
                        USERS[thisUserIndex]['isReady'] = False

                        USERS[index]['score'] = 0
                        USERS[index]['isReady'] = False

                        await USERS[thisUserIndex]['socket'].send(
                            json.dumps({'result': "You lose!"}))

                        await USERS[thisUserIndex]['enemySocket'].send(
                            json.dumps({'result': "You win!"}))

                if dx:
                    await USERS[thisUserIndex]['enemySocket'].send(json.dumps({'dx': dx}))

            else:
                USERS[thisUserIndex]['score'] = 0

    finally:
        if find(USERS, 'enemySocket', websocket) != -1:
            await USERS[find(USERS, 'enemySocket', websocket)]['socket'].send(
                json.dumps({'leave': 1}))
            USERS[find(USERS, 'enemySocket', websocket)]['id'] = 0
            USERS[find(USERS, 'enemySocket', websocket)]['enemySocket'] = None

        unregister(websocket)


start_server = websockets.serve(start, config.IP, config.PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
