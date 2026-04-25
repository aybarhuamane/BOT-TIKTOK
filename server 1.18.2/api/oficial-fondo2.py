#FONDO MATRIX
# GAME 1  - MATAR A CREEP

#library personalizada
from hologramas import (
    actualizar_toplikes_holograma,
    actualizar_topmoney_holograma,
    clear_hologram,
    clear_all_holograms,
    HOLO_TAG_LIKES,
    HOLO_TAG_MONEY,
)

from barralateral import (
    init_topmoney_sidebar,
    actualizar_topmoney_sidebar,
    resolve_gift_value,
    delete_sidebar

)


# libary general
from TikTokLive import TikTokLiveClient
from TikTokLive.events import CommentEvent, LikeEvent, GiftEvent, FollowEvent, ConnectEvent, ShareEvent
from mcrcon import MCRcon
import pyttsx3
import threading
from collections import deque
import asyncio
import time
import random
import socket
import winsound
import os
import re # PARA LIMPIAR TEXTO TTS Y EVITAR QUE TRABE CON EMOJIS O SIMBOLOS RAROS
# -----------------------------
# CONFIG
# -----------------------------
tiktok_user = "onxplayer"
host = "127.0.0.1"
port = 25575
password = "paciencia"
player = "CAPITANCATT"
tap_counter = 0
tap_double_counter = 0
bot_ready = False

# -----------------------------
# Queue para voz
# -----------------------------
VOICE_MAX_QUEUE = 10 # maximos 5 mensajes de cola antiguos
VOICE_MAX_AGE = 45  # max 30 segundos de espera en la cola para evitar decir cosas irrelevantes

voice_queue = deque()
voice_lock = threading.Lock()
voice_event = threading.Event()
# -----------------------------
# SALUDOS, LIKES Y DINERO
# -----------------------------

usuarios_saludados = set()   # GUARDAR PERSONAS A SALUDAR
user_likes = {}              # GUARDAR LIKES POR USUARIO
user_money = {}
gift_streak_memory = {}
# -----------------------------
# COORDENADAS
# -----------------------------
coord_evil = "-132 80 174"
coord_good = "-132 80 174"
coord_centro = "-132 80 174"

# coord_evil = "553 107 -404"
# coord_good = "558 104 -402"
# coord_centro = "555 102 -402"

# -----------------------------
# CONFIG ACTIVACION SIDEBAR
# -----------------------------
ENABLE_INIT_SIDEBAR = False            # true: activar  | false: desactivar
ENABLE_REFRESH_SIDEBAR = False          # true: actualizar al recibir regalo | false: no actualizar automáticamente

def init_sidebar_topmoney():
    if not ENABLE_INIT_SIDEBAR:
        delete_sidebar(mc_command)
        return
    init_topmoney_sidebar(mc_command)

def actualizar_sidebar_topmoney():
    if not ENABLE_REFRESH_SIDEBAR:
        return
    actualizar_topmoney_sidebar(mc_command, user_money)

# -----------------------------
# CONFIG ACTIVACION HOLOGRAMAS
# -----------------------------
ENABLE_HOLOGRAMS = False             # true: activar  | false: desactivar
ENABLE_HOLOGRAM_TOPLIKES = False     # true: activar  | false: desactivar
ENABLE_HOLOGRAM_TOPMONEY = False     # true: activar  | false: desactivar


def actualizar_holograma_likes():
    if not ENABLE_HOLOGRAMS:
        clear_hologram(mc_command, HOLO_TAG_LIKES)

        return
    if not ENABLE_HOLOGRAMS or not ENABLE_HOLOGRAM_TOPLIKES:
        return

    actualizar_toplikes_holograma(mc_command, user_likes)


def actualizar_holograma_money():
    if not ENABLE_HOLOGRAMS or not ENABLE_HOLOGRAM_TOPMONEY:
        clear_hologram(mc_command, HOLO_TAG_MONEY)
        return
    if not ENABLE_HOLOGRAM_TOPMONEY:
        return

    actualizar_topmoney_holograma(mc_command, user_money)

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
# SONIDO LIKE
# -----------------------------
def sonar_like():
    try:
        ruta = os.path.join(os.path.dirname(__file__), "sound", "like.wav")
        winsound.PlaySound(ruta, winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception as e:
        print(f"Error reproduciendo sonido like: {e}")
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
# VOZ (SISTEMA ANTI-BLOQUEO)
# -----------------------------
# -----------------------------
# VOZ (COLA LIMITADA Y EXPIRACIÓN)
# -----------------------------
def limpiar_cola_expirada():
    ahora = time.time()
    while voice_queue and (ahora - voice_queue[0][1]) > VOICE_MAX_AGE:
        texto_expirado, _ = voice_queue.popleft()
        print(f"DESCARTADO POR TIEMPO -> {texto_expirado}")

# def limpiar_texto_tts(texto):  #V.1.0 - LIMPIA SOLO EMOJIS Y SIMBOLOS RAROS
#     texto = str(texto)
#     # quita emojis y símbolos raros que a veces traban el TTS
#     texto = re.sub(r"[^\w\sáéíóúÁÉÍÓÚñÑ,.!?-]", "", texto)
#     texto = re.sub(r"\s+", " ", texto).strip()
#     return texto


def limpiar_texto_tts(texto):
    texto = str(texto)

    # unir letras separadas: H O L A -> HOLA / Q U E T A L -> QUETAL
    texto = re.sub(
        r'\b(?:[A-Za-zÁÉÍÓÚáéíóúÑñ]\s+){2,}[A-Za-zÁÉÍÓÚáéíóúÑñ]\b',
        lambda m: m.group(0).replace(" ", ""),
        texto
    )

    # quitar guion suelto al final: K A T I - -> KATI
    texto = re.sub(r"\s*-\s*$", "", texto)

    # quitar símbolos raros
    texto = re.sub(r"[^\w\sáéíóúÁÉÍÓÚñÑ,.!?-]", "", texto)

    # limpiar espacios repetidos
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto

# LIMPIA USER MINECAFT PARA LA INVOCACION DE MODS

def limpiar_user_mc(user):
    user = str(user)

    # solo letras, números y _
    user = re.sub(r"[^a-zA-Z0-9_]", "", user)

    # evitar vacío
    if user == "":
        user = "anon"

    return user


def speak_task():
    while True:
        voice_event.wait()

        item = None

        with voice_lock:
            limpiar_cola_expirada()

            if voice_queue:
                item = voice_queue.popleft()

            if not voice_queue:
                voice_event.clear()

        if item is None:
            continue

        text, timestamp = item

        if (time.time() - timestamp) > VOICE_MAX_AGE:
            print(f"DESCARTADO ANTES DE HABLAR -> {text}")
            continue

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

threading.Thread(target=speak_task, daemon=True).start()

def speak(text):
    # == LEE EMOTICONES TAMBIEN ==
    text = str(text).strip()
    # == NO LEE EMOTICONES ==
    #text = limpiar_texto_tts(text)
    # if not text:
    #     return
    
    ahora = time.time()

    with voice_lock:
        limpiar_cola_expirada()

        while len(voice_queue) >= VOICE_MAX_QUEUE:
            texto_eliminado, _ = voice_queue.popleft()
            print(f"COLA LLENA, ELIMINADO -> {texto_eliminado}")

        voice_queue.append((text, ahora))
        voice_event.set()

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

    init_sidebar_topmoney()
    actualizar_sidebar_topmoney()
    actualizar_holograma_likes()
    actualizar_holograma_money()

@client.on(CommentEvent)
async def on_comment(event):
    if not bot_ready:
        return
    # == LEE EMOTICONES TAMBIEN ==
    user = event.user.nickname
    user_tts = limpiar_texto_tts(user)   # solo para voz del nombre
    comment = event.comment                              # comentario intacto


    print(f"CHAT -> {user} | USER_LIMPIO: {user_tts} : {comment} ")
    # == NO LEE EMOTICONES ==
    
    if user== "One player":
        speak(f"El anfitrion dice {comment[:100]}")
    else:
        speak(f"{user_tts} dice {comment[:80]}")
    #####**********************************   TEAM A DEFENSA  *******************************

    # LOBO - 1 coin

    if comment == "hola" or comment == "Hola" or comment == "HOLA" or comment == "buenas" or comment == "ola":
        speak(f" Hola {user_tts} bienvenido al directo")



@client.on(ShareEvent)
async def on_share(event):
    if not bot_ready:
        return

    user = event.user.nickname
    user_tts = limpiar_texto_tts(user)
    joined = getattr(event, "users_joined", None)

    print(f"SHARE -> {user} compartió el live | users_joined={joined}")
    speak(f"Gracias {user} por compartir el directo")

    mc_command(
        f'summon minecraft:villager {coord_good} '
        #f'{{CustomName:\'{{"text":"{user}"}}\',"CustomNameVisible":1b}}'
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
    user_tts = limpiar_texto_tts(user)
    user_clean = limpiar_user_mc(user)
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

    print("========== GIFT DEBUG ==========")
    print(f"user         : {user}")
    print(f"gift_raw     : {gift_raw}")
    print(f"gift_lower   : {gift}")
    print(f"streakable   : {event.gift.streakable}")
    print(f"streaking    : {getattr(event, 'streaking', None)}")
    print(f"repeat_count : {repeat_count}")
    print("================================")


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

    speak(f"Gracias {user_tts} por el regalo")  #ANTES ERA USER


    #####**********************************   ACCIONES REGALOS  *******************************

    # TNT simple
    if "gg" in gift:
        x = random.randint(-6, 6)
        z = random.randint(-6, 6)
        mc_command(f'execute positioned {coord_centro} run summon minecraft:tnt ~{x} ~ ~{z} {{Fuse:80}}')

    # TNT masivo
    elif "dona" in gift or "rosquilla" in gift:
        for _ in range(50):
            x = random.randint(-6, 6)
            z = random.randint(-6, 6)
            mc_command(f'execute positioned {coord_centro} run summon minecraft:tnt ~{x} ~ ~{z} {{Fuse:80}}')

    # GOLEMS
    elif "guardian wings" in gift:
        for _ in range(3):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(
                f'execute positioned {coord_centro} run summon minecraft:iron_golem ~{x} ~ ~{z} '
                f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )

    elif "osito mishka" in gift:
        for _ in range(30):  # 🔥 BAJADO DE 100 A 30 PARA EVITAR LAG
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(
                f'execute positioned {coord_centro} run summon minecraft:iron_golem ~{x} ~ ~{z} '
                f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )

    # PIGLIN
    elif "maracas" in gift:
        for _ in range(5):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(
                f'execute positioned {coord_evil} run summon minecraft:zombified_piglin ~{x} ~ ~{z} '
                f'{{HandItems:[{{id:"minecraft:golden_sword",Count:1b}},{{}}],'
                f'CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )

    # ZOMBIES
    elif "rose" in gift:
        for _ in range(10):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)
            mc_command(
                f'execute positioned {coord_evil} run summon minecraft:zombie ~{x} ~ ~{z} '
                f'{{ArmorItems:[{{}},{{}},{{}},{{id:"minecraft:diamond_helmet",Count:1b}}],'
                f'CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )

    # WITHER
    elif "capibara" in gift:
        for _ in range(3):
            x = random.randint(-6, 6)
            z = random.randint(-6, 6)
            mc_command(
                f'execute positioned {coord_evil} run summon minecraft:wither ~{x} ~ ~{z} '
                f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )

    #RAVAGER
    elif "rose big" in gift or "rose king" in gift:
        for _ in range(10):
            x = random.randint(-6, 6)
            z = random.randint(-6, 6)
            mc_command(
                f'execute positioned {coord_evil} run summon minecraft:ravager ~{x} ~ ~{z} '
                f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )
    #SKELETON ENDER
    #SKELETON WITHER (Corregido)
    elif "heart me" in gift:
        for _ in range(5):
            x = random.randint(-6, 6)
            z = random.randint(-6, 6)
            mc_command(
                f'execute positioned {coord_evil} run summon minecraft:wither_skeleton ~{x} ~ ~{z} '
                f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )
            
    elif "perfum" in gift:
        for _ in range(10):
            x = random.randint(-6, 6)
            z = random.randint(-6, 6)
            mc_command(
                f'execute positioned {coord_evil} run summon minecraft:evoker ~{x} ~ ~{z} '
                f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            )

    # WARDEN
    elif "finger heart" in gift:
        user_esc = user.replace("\\", "\\\\").replace('"', '\\"')
        mc_command(
            f'summon minecraft:warden {coord_evil} '
            f'{{CustomName:\'{{"text":"{user_clean}"}}\',CustomNameVisible:1b,'
            f'Brain:{{memories:{{"minecraft:dig_cooldown":{{value:{{}},ttl:1200L}}}}}}}}'
        )

    # DRAGON
    elif "leon the kitten" in gift:
        mc_command(
            f'summon minecraft:ender_dragon {coord_evil} '
            f'{{CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
        )

    else:
        print(f"[INFO] Regalo sin acción: {gift}")


    
    actualizar_topmoney_sidebar(mc_command, user_money)
    actualizar_holograma_money()

# HABLA BIENVENIDO AL UNIRSE ALGUIEN
@client.on(FollowEvent)
async def on_follow(event):
    if not bot_ready:
        return

    user = event.user.nickname
    user_tts = limpiar_texto_tts(user)

    print(f"NUEVO FOLLOW -> {user}")
    speak(f"Bienvenido {user_tts} al directo")
    #mc_command(f'summon minecraft:iron_golem {coord_good}')
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
    user_tts = limpiar_texto_tts(user)
    # -----------------------------
    # TOP LIKERS
    # -----------------------------
    if user not in user_likes:
        user_likes[user] = 0

    user_likes[user] += event.count
    # actualizar_toplikers_sidebar()
    actualizar_holograma_likes()

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
        sonar_like()
        #speak(f"Gracias por los likes {user_tts} ") # ahora si a corrreeer ")
        for i in range(5):
            x = random.randint(-5, 5)
            z = random.randint(-5, 5)

            user_clean = limpiar_user_mc(user)
            # mc_command(
            #     f'execute positioned {coord_evil} run summon minecraft:zombie ~{x} ~ ~{z} '
            #     f'{{ArmorItems:[{{id:"minecraft:golden_boots",Count:1b}},{{id:"minecraft:golden_leggings",Count:1b}},{{id:"minecraft:golden_chestplate",Count:1b}},{{id:"minecraft:golden_helmet",Count:1b}}],'
            #     f'CustomName:\'{{"text":"{user_clean}"}}\',"CustomNameVisible":1b}}'
            # )
            mc_command(
            f'execute positioned {coord_evil} run summon minecraft:zombie ~{x} ~ ~{z} '
            f'{{ArmorItems:[{{id:"minecraft:golden_boots",Count:1b}},{{id:"minecraft:golden_leggings",Count:1b}},{{id:"minecraft:golden_chestplate",Count:1b}},{{id:"minecraft:golden_helmet",Count:1b}}]}}'
            )

        #==== efecto  al invocar ==
        #mc_command(f'execute at {player} run summon minecraft:firework_rocket ~ ~3 ~ {{LifeTime:30}}')
     
       # mc_command(f'give {player} minecraft:bow 1')
       # mc_command(f'give {player} minecraft:arrow 16')
        tap_counter = 0





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
