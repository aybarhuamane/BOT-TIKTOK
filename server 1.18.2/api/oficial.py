# GAME 1  - MATAR A CREEP

#library personalizada
from hologramas import actualizar_toplikes_holograma, actualizar_topmoney_holograma
# libary general
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, LikeEvent, GiftEvent, FollowEvent, ConnectEvent, ShareEvent
from mcrcon import MCRcon
import pyttsx3
import threading
import queue
import asyncio
import time
import random
import socket

# -----------------------------
# CONFIG
# -----------------------------
tiktok_user = "masvideos4k"
host = "127.0.0.1"
port = 25575
password = "paciencia"
player = "CAPITANCATT"
tap_counter = 0
tap_double_counter = 0
bot_ready = False
voice_queue = queue.Queue()
usuarios_saludados = set()   # GUARDAR PERSONAS A SALUDAR
user_likes = {}              # GUARDAR LIKES POR USUARIO
user_money = {}
gift_streak_memory = {}
# -----------------------------
# COORDENADAS
# -----------------------------
coord_evil = "559 104 -389"
coord_good = "559 104 -389"
coord_centro = "559 104 -389"

# coord_evil = "553 107 -404"
# coord_good = "558 104 -402"
# coord_centro = "555 102 -402"


# -----------------------------
# RCON PERSISTENTE
# -----------------------------
rcon_lock = threading.Lock()
rcon_client = None

def mc_connect():
    global rcon_client
    if rcon_client is None:
        rcon_client = MCRcon(host, password, port=port)
        rcon_client.connect()

def mc_command(cmd):
    global rcon_client
    try:
        with rcon_lock:
            if rcon_client is None:
                mc_connect()
            return rcon_client.command(cmd)
    except Exception as e:
        print(f"RCON ERROR: {e}")
        print(f"CMD FALLÓ: {cmd}")
        try:
            if rcon_client is not None:
                rcon_client.disconnect()
        except:
            pass
        rcon_client = None
        return None

# -----------------------------
# CHEQUEO DE INTERNET
# -----------------------------

def hay_internet():
    try:
        socket.create_connection(("1.1.1.1", 53), timeout=3).close()
        return True
    except OSError:
        return False

# -----------------------------
# VALOR DEL REGALO
# -----------------------------
def resolve_gift_value(gift_name: str) -> int:
    if not gift_name:
        return 0
    gift = gift_name.lower().strip()


    if "big rose" in gift or "rosa grande" in gift:
        return 10
    elif "maracas" in gift:
        return 1
    elif "rose" in gift:
        return 1
    elif "tiktok" in gift:
        return 1
    elif "heart me" in gift:
        return 1
    elif "it's corn" in gift or "its corn" in gift:
        return 1
    elif "rosquilla" in gift:
        return 5
    elif "overreact" in gift or "Overreact" in gift:
        return 5
    elif "corazon coreano" in gift or "corazón coreano" in gift:
        return 30
    elif "confeti" in gift:
        return 100
    elif "money gun" in gift:
        return 500
    if "lion" in gift or "leon" in gift or "león" in gift:
        return 1000
    return 1

# -----------------------------
# TOP MONEY SIDEBAR
# -----------------------------
SIDEBAR_OBJECTIVE = "topMoney"
last_sidebar_entries = []

def limpiar_nombre_scoreboard(name, max_len=12):
    safe = str(name).replace('"', "").replace("\\", "").replace("\n", "").replace("\r", "")
    safe = safe.replace(" ", "_")
    return safe[:max_len]

def init_topmoney_sidebar():
    global last_sidebar_entries

    mc_command(f"scoreboard objectives remove {SIDEBAR_OBJECTIVE}")
    mc_command(f"scoreboard objectives add {SIDEBAR_OBJECTIVE} dummy")
    mc_command(f"scoreboard objectives setdisplay sidebar {SIDEBAR_OBJECTIVE}")

    # Intento de nombre visible del panel.
    # Si tu server no lo acepta, no rompe nada importante.
    mc_command(
        f'scoreboard objectives modify {SIDEBAR_OBJECTIVE} displayname '
        f'{{"text":"TOP MONEY","color":"red"}}'
    )

    last_sidebar_entries = []


def actualizar_topmoney_sidebar():
    global last_sidebar_entries

    mc_command(f"scoreboard objectives setdisplay sidebar {SIDEBAR_OBJECTIVE}")

    # Borra líneas anteriores
    for entry in last_sidebar_entries:
        mc_command(f'scoreboard players reset "{entry}" {SIDEBAR_OBJECTIVE}')

    top = sorted(user_money.items(), key=lambda x: x[1], reverse=True)[:3]


    if len(top) > 0:
        nombre1 = limpiar_nombre_scoreboard(top[0][0])
        money1 = top[0][1]
        linea1 = f"1_{nombre1}"
        score1 = money1
    else:
        linea1 = "1_"
        score1 = 0

    if len(top) > 1:
        nombre2 = limpiar_nombre_scoreboard(top[1][0])
        money2 = top[1][1]
        linea2 = f"2_{nombre2}"
        score2 = money2
    else:
        linea2 = "2_"
        score2 = 0

    if len(top) > 2:
        nombre3 = limpiar_nombre_scoreboard(top[2][0])
        money3 = top[2][1]
        linea3 = f"3_{nombre3}"
        score3 = money3
    else:
        linea3 = "3_"
        score3 = 0

    mc_command(f'scoreboard players set "{linea1}" {SIDEBAR_OBJECTIVE} {score1}')
    mc_command(f'scoreboard players set "{linea2}" {SIDEBAR_OBJECTIVE} {score2}')
    mc_command(f'scoreboard players set "{linea3}" {SIDEBAR_OBJECTIVE} {score3}')

    last_sidebar_entries = [linea1, linea2, linea3]

# -----------------------------
# VOZ (SISTEMA ANTI-BLOQUEO)
# -----------------------------
def speak_task():
    while True:
        text = voice_queue.get()
        if text is None:
            break

        try:
            engine = pyttsx3.init()
            engine.setProperty("rate", 190)
            engine.setProperty("volume", 1.0)

            print(f"DICIENDO: {text}")
            engine.say(text)
            engine.runAndWait()

            engine.stop()
            del engine
        except Exception as e:
            print(f"Error en motor de voz: {e}")
        finally:
            voice_queue.task_done()

threading.Thread(target=speak_task, daemon=True).start()

def speak(text):
    while not voice_queue.empty():
        try:
            voice_queue.get_nowait()
        except:
            pass
    voice_queue.put(text)

# -----------------------------
# TIKTOK
# -----------------------------
client = TikTokLiveClient(unique_id=tiktok_user)

@client.on(ConnectEvent)
async def on_connect(event):
    global bot_ready
    print("CONECTADO - ESPERANDO 2 SEG PARA FILTRAR...")
    await asyncio.sleep(2)
    bot_ready = True
    speak("Bot listo")

    init_topmoney_sidebar()
   # actualizar_topmoney_sidebar()
    actualizar_topmoney_sidebar()
    actualizar_toplikes_holograma(mc_command, user_likes)
    actualizar_topmoney_holograma(mc_command, user_money)

@client.on(CommentEvent)
async def on_comment(event):
    if not bot_ready:
        return

    user = event.user.nickname
    comment = event.comment

    print(f"CHAT -> {user}: {comment}")
    speak(f"{user} dice {comment[:70]}")
   
    #####**********************************   TEAM A DEFENSA  *******************************

    # LOBO - 1 coin

    if comment == "hola" or comment == "Hola" or comment == "HOLA" or comment == "buenas" or comment == "ola":
        speak(f" Hola {user} bienvenido al directo")

    if comment == "c12":
        mc_command(f'summon minecraft:wolf {coord_good} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')


    # X1 TNT - 10 coin
    if comment == "c13":
        for i in range(10):
            mc_command(f'summon minecraft:tnt {coord_centro} {{Fuse:80}}')

    if comment == "c123":
        for i in range(100):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(f'execute positioned {coord_centro} run summon minecraft:tnt ~{x} ~5 ~{z} {{Fuse:80}}')

    if comment == "xyz":
        for i in range(200):
            mc_command(
                f'summon minecraft:zombie {coord_evil} '
                f'{{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:leather_helmet",Count:1b}}],'
                f'CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )
        for i in range(50):
            mc_command(
                f'summon minecraft:witch {coord_evil} '
                f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )
        for i in range(30):
            mc_command(
                f'summon minecraft:piglin {coord_evil} '
                f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )

        for i in range(5):
            mc_command(
                f'summon minecraft:iron_golem {coord_good} '
                f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )           
        mc_command(f'summon minecraft:wolf {coord_good} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')
        mc_command(f'summon minecraft:wolf {coord_good} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')

    # GOLEN - 30 coin
    if comment == "c14":
        mc_command(f'summon minecraft:iron_golem {coord_good} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')

    # X10 LLUVIA TNT - 10 coin
    if comment == "c15":
        for i in range(10):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(f'execute positioned {coord_centro} run summon minecraft:tnt ~{x} ~5 ~{z} {{Fuse:80}}')

    #####**********************************   TEAM B ZOMBIE  *******************************

    # ZOMBIE CON CASCO HIERRO - 1 coin
    if comment == "c16":
        for i in range(2):
            mc_command(
                f'summon minecraft:zombie {coord_evil} '
                f'{{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:diamond_helmet",Count:1b}}],'
                f'CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )

    # SKELETON - 5 coin
    if comment == "c17":
        mc_command(f'execute at {player} run summon minecraft:skeleton ~ ~1 ~ {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')

    # CREEPER EXPLOSIVO - 30 coin
    if comment == "c18":
        mc_command(f'execute positioned {coord_evil} run summon minecraft:creeper ~ ~1 ~ {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')

    # BOS WITHER - 500 coin
    if comment == "c19":
        mc_command(f'summon minecraft:wither {coord_evil} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')





@client.on(ShareEvent)
async def on_share(event):
    if not bot_ready:
        return

    user = event.user.nickname
    joined = getattr(event, "users_joined", None)

    print(f"SHARE -> {user} compartió el live | users_joined={joined}")
    speak(f"Gracias {user} por compartir el directo")

    for i in range(1):
        mc_command(
            f'summon minecraft:villager {coord_good} '
            f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
        )

    mc_command(f'execute at {player} run summon minecraft:firework_rocket ~ ~3 ~')

@client.on(GiftEvent)
async def on_gift(event):
    global gift_streak_memory
    if not bot_ready:
        return

    # Ignorar eventos duplicados de streak
    if event.gift.streakable and not event.streaking:
        return

    user = event.user.nickname
    user_id = getattr(event.user, "unique_id", user)
    gift_raw = event.gift.name
    gift = gift_raw.lower().strip()

    repeat_count = getattr(event, "repeat_count", 1)
    if not isinstance(repeat_count, int) or repeat_count < 1:
        repeat_count = 1

    # print(f"REGALO -> {user} envió {gift}") #ANTIGUO
    # speak(f"Gracias {user} por el regalo")  #ANTIGUO

    # if event.gift.streakable and not event.streaking:  #ANTIGUO
    #     return

# AGREGADO  ------------------------
    if event.gift.streakable:
        key = f"{user_id}:{gift}"
        prev_count = gift_streak_memory.get(key, 0)
        delta_count = repeat_count - prev_count

        if delta_count < 1:
            delta_count = 1

        gift_streak_memory[key] = repeat_count

  
    else:
        delta_count = repeat_count

    gift_value = resolve_gift_value(gift)
    delta_money = gift_value * delta_count

    if user not in user_money:
        user_money[user] = 0

    user_money[user] += delta_money

    print(
        f"REGALO -> {user} | raw='{gift_raw}' | gift='{gift}' | "
        f"repeat={repeat_count} | delta={delta_count} | value={gift_value} | "
        f"sumado={delta_money} | total={user_money[user]}"
    )

    if gift_value == 0:
        print(f"[AVISO] Regalo no mapeado en resolve_gift_value(): '{gift_raw}'")

    speak(f"Gracias {user} por el regalo")



    #####**********************************   TEAM A DEFENSA  *******************************

    # LOBO - 1 coin
    if "maracas" in gift:
        mc_command(
            f'summon minecraft:wolf {coord_good} '
            f'{{Owner:"{player}",CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
        )
    # x5 TNT - 1 coin
    if "rose" in gift:
        for i in range(5):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(f'execute positioned {coord_centro} run summon minecraft:tnt ~{x} ~5 ~{z} {{Fuse:80}}')


    # GOLEN - 1 coin
    if "guardian wings" in gift:
        for i in range(5):
            mc_command(f'summon minecraft:iron_golem {coord_centro} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')
            # mc_command(
            # f'summon minecraft:wither_skeleton {coord_evil} '
            # f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            # )


    # X100 LLUVIA TNT - 100 coin
    if "confeti" in gift:
        for i in range(100):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(f'execute positioned {coord_centro} run summon minecraft:tnt ~{x} ~5 ~{z} {{Fuse:80}}')

    #####**********************************   TEAM B ZOMBIE  *******************************

    # CHANCHO- 1 coin
    if "tiktok" in gift:
        for i in range(5):
            mc_command(
            # f'summon minecraft:zombie {coord_evil} '
            # f'{{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:diamond_helmet",Count:1b}}],'
            # f'CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            f'summon minecraft:zombified_piglin {coord_evil} '
            f'{{HandItems:[{{id:"minecraft:golden_sword",Count:1b}},{{}}],'
            f'CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )

    # SKELETON  - 5 coin
    if "rosquilla" in gift:
        for i in range(20):
            mc_command(f'execute at {player} run summon minecraft:skeleton ~ ~1 ~ {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')
    # BRUJA - 5 coin
    if "overreact" in gift or "Overreaect" in gift:
        for i in range(20):
            mc_command(f'summon minecraft:witch {coord_good} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')

    # CREEPER EXPLOSIVO - 30 coin
    if "corazon coreano" in gift or "corazón coreano" in gift:
    #    mc_command(f'give {player} minecraft:enchanted_golden_apple 5')
        mc_command(f'summon minecraft:ravager {coord_evil} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')
    # BOS WITHER - 500 coin
    if "money gun" in gift:
        mc_command(f'summon minecraft:wither {coord_evil} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')
    if "Rose king" in gift:
        mc_command(f'summon minecraft:evoker {coord_evil} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')

    # BOS DRAGON- 1000 coin
    if "leon the kitten" in gift or "Leon the kitten" in gift:
        mc_command(
            f'summon minecraft:ender_dragon {coord_evil} '
            f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
        )
    
    actualizar_topmoney_sidebar()
    actualizar_topmoney_holograma(mc_command, user_money)

# HABLA BIENVENIDO AL UNIRSE ALGUIEN
@client.on(FollowEvent)
async def on_follow(event):
    if not bot_ready:
        return

    user = event.user.nickname

    print(f"NUEVO FOLLOW -> {user}")
    speak(f"Bienvenido {user} al directo")
    mc_command(f'summon minecraft:iron_golem {coord_good} {{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}')
    mc_command(f'execute at {player} run summon minecraft:firework_rocket ~ ~2 ~')

# AGREGA EVENTO LIKE
@client.on(LikeEvent)
async def on_like(event):
    global tap_counter
    global tap_double_counter

    if not bot_ready:
        return

    user = event.user.nickname

    # -----------------------------
    # TOP LIKERS
    # -----------------------------
    if user not in user_likes:
        user_likes[user] = 0

    user_likes[user] += event.count
    # actualizar_toplikers_sidebar()
    actualizar_toplikes_holograma(mc_command, user_likes)

    ##### v1 *********************************************************
    # SALUDAR SOLO UNA VEZ POR USUARIO
    if user not in usuarios_saludados:
        speak(f"Bienvenido {user} al directo")
        usuarios_saludados.add(user)

    # TAP TAP - ENVIA MISIL
    tap_counter += event.count
    tap_double_counter += event.count
    print(f"TAP TAP TOTAL -> x5 :  {tap_counter} -> x400 : {tap_double_counter}")

    if tap_counter >= 50: 
        speak(f"Gracias por los likes {user} ") # ahora si a corrreeer ")


        for i in range(5):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
 
            # mc_command(
            #     f'summon minecraft:zombie {coord_evil} '
            #     f'{{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:leather_helmet",Count:1b}}],'
            #     f'CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            # )
            
                #f'summon minecraft:zombie {coord_evil} '
            mc_command(
                f'execute positioned {coord_centro} run summon minecraft:zombie ~{x} ~5 ~{z} '
                f'{{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:diamond_helmet",Count:1b}}],'
                f'CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
            )
        mc_command(f'execute at {player} run summon minecraft:firework_rocket ~ ~3 ~ {{LifeTime:30}}')
       # mc_command(f'give {player} minecraft:bow 1')
       # mc_command(f'give {player} minecraft:arrow 16')
        tap_counter = 0

    if tap_double_counter >= 500:
        #speak("Gracias por los likes")

        # mc_command(
        #     f'execute at {player} run summon minecraft:firework_rocket ~ ~3 ~ {{LifeTime:30}}'
        # )
        # CANTODAD DE ZOMBIE GENERADO POR TAP TAP

        #mc_command(
        #    f'summon minecraft:iron_golem {coord_good} '
        #    f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
        #)           

        tap_double_counter = 0




    ##### fin v1 *****************************************************

# -----------------------------
# RUN
# -----------------------------
if __name__ == "__main__":
    while True:
        try:
            if not hay_internet():
                print("Sin internet... esperando reconexión.")
                while not hay_internet():
                    time.sleep(5)
                print("Internet restablecido. Reconectando TikTok...")

            bot_ready = False
            client.run()

        except KeyboardInterrupt:
            print("Bot detenido manualmente.")
            break

        except Exception as e:
            bot_ready = False
            print(f"Se perdió la conexión con TikTok: {e}")
            print("Esperando internet para reconectar...")

            while not hay_internet():
                time.sleep(5)

            print("Internet volvió. Reintentando conexión en 3 segundos...")
            time.sleep(3)
