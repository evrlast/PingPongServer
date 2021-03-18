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


def codeGenerator():
    newCode = ''.join(random.choice(letters) for i in range(6))

    while find(USERS, 'code', newCode) != -1:
        newCode = ''.join(random.choice(letters) for i in range(6))

    return newCode


def register(websocket):
    USERS.append({'socket': websocket,
                  'code': '',
                  'name': '',
                  'id': 0,
                  'score': 0,
                  'isReady': False,
                  'enemyIndex': -1})


def unregister(websocket):
    index = find(USERS, 'socket', websocket)
    for key in USERS[index]:
        USERS[index][key] = None


def speedGenerator():
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

    try:
        register(websocket)

        thisUserIndex = find(USERS, 'socket', websocket)

        USERS[thisUserIndex]['code'] = codeGenerator()

        await USERS[thisUserIndex]['socket'].send(
            json.dumps({'code': USERS[thisUserIndex]['code']}))

        print(USERS[thisUserIndex]['code'])

        async for message in websocket:
            enemyIndex = USERS[thisUserIndex]['enemyIndex']

            data = json.loads(message)

            dx = data.get('dx')
            goal = data.get('goal')
            code = data.get('code')
            name = data.get('name')
            back = data.get('exit')
            playAgain = data.get('playAgain')

            if enemyIndex != -1:

                if playAgain:
                    USERS[thisUserIndex]['isReady'] = True

                    if USERS[thisUserIndex]['isReady'] and USERS[enemyIndex]['isReady']:
                        speedGenerator()

                        await USERS[thisUserIndex]['socket'].send(
                            json.dumps({'enemyName': USERS[index]['name'],
                                        'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                        'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                        await USERS[enemyIndex]['socket'].send(
                            json.dumps({'enemyName': USERS[thisUserIndex]['name'],
                                        'speedX': speedX / 100 * USERS[enemyIndex]['id'],
                                        'speedY': speedY / 100 * USERS[enemyIndex]['id']}))

                if back:
                    await USERS[enemyIndex]['socket'].send(
                        json.dumps({'leave': 1}))

                    USERS[thisUserIndex]['id'] = 0
                    USERS[thisUserIndex]['score'] = 0
                    USERS[thisUserIndex]['code'] = codeGenerator()
                    USERS[thisUserIndex]['isReady'] = False
                    USERS[thisUserIndex]['enemyIndex'] = -1

                    USERS[enemyIndex]['enemyIndex'] = -1
                    USERS[enemyIndex]['isReady'] = False
                    USERS[enemyIndex]['code'] = codeGenerator()

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'code': USERS[thisUserIndex]['code']}))

                    await USERS[enemyIndex]['socket'].send(
                        json.dumps({'code': USERS[enemyIndex]['code']}))

            if name:
                USERS[thisUserIndex]['name'] = name

            if code:
                index = find(USERS, 'code', code)
                if index != -1 and index != thisUserIndex and USERS[index]['name'] != '':

                    USERS[thisUserIndex]['enemyIndex'] = index

                    USERS[thisUserIndex]['id'] = -1
                    USERS[thisUserIndex]['isReady'] = True

                    USERS[index]['id'] = 1
                    USERS[index]['isReady'] = True
                    USERS[index]['enemyIndex'] = thisUserIndex

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'enemyName': USERS[index]['name']}))

                    await USERS[index]['socket'].send(
                        json.dumps({'enemyName': USERS[thisUserIndex]['name']}))

                    speedGenerator()

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    await USERS[index]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[index]['id'],
                                    'speedY': speedY / 100 * USERS[index]['id']}))

                else:
                    await USERS[thisUserIndex]['socket'].send(json.dumps({'codeError': 1}))

            if USERS[thisUserIndex]['isReady'] and USERS[enemyIndex]['isReady']:
                if goal:
                    USERS[thisUserIndex]['score'] += 1

                    speedGenerator()

                    await USERS[thisUserIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[thisUserIndex]['id'],
                                    'speedY': speedY / 100 * USERS[thisUserIndex]['id']}))

                    await USERS[enemyIndex]['socket'].send(
                        json.dumps({'speedX': speedX / 100 * USERS[enemyIndex]['id'],
                                    'speedY': speedY / 100 * USERS[enemyIndex]['id'],
                                    'score': USERS[thisUserIndex]['score']}))

                    if USERS[thisUserIndex]['score'] >= 1:
                        USERS[thisUserIndex]['score'] = 0
                        USERS[thisUserIndex]['isReady'] = False

                        USERS[enemyIndex]['score'] = 0
                        USERS[enemyIndex]['isReady'] = False

                        await USERS[thisUserIndex]['socket'].send(
                            json.dumps({'result': "You lose!"}))

                        await USERS[enemyIndex]['socket'].send(
                            json.dumps({'result': "You win!"}))

                if dx:
                    await USERS[enemyIndex]['socket'].send(json.dumps({'dx': dx}))

            else:
                USERS[thisUserIndex]['score'] = 0

    finally:
        enemyIndex = USERS[thisUserIndex]['enemyIndex']
        if enemyIndex != -1:
            await USERS[enemyIndex]['socket'].send(
                json.dumps({'leave': 1}))
            USERS[enemyIndex]['id'] = 0
            USERS[enemyIndex]['enemyIndex'] = None

        unregister(websocket)


start_server = websockets.serve(start, config.IP, config.PORT)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
