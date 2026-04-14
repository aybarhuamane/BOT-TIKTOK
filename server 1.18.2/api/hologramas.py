# -----------------------------
# HOLOGRAMA TOP LIKES
# -----------------------------
HOLO_LIKES_X = 559
HOLO_LIKES_Y = 108
HOLO_LIKES_Z = -385
HOLO_TAG_LIKES = "topLikesHg"

# -----------------------------
# HOLOGRAMA TOP MONEY
# -----------------------------
HOLO_MONEY_X = 559
HOLO_MONEY_Y = 109
HOLO_MONEY_Z = -385
HOLO_TAG_MONEY = "topMoneyHg"

# -----------------------------
# HOLOGRAMA FUNCTIONS
# -----------------------------

def json_escape(text):
    return str(text).replace("\\", "\\\\").replace('"', '\\"')

def off_hologram(mc_command, tag):
    mc_command(f'kill @e[type=minecraft:armor_stand,tag={tag}]')

def clear_hologram(mc_command, tag):
    mc_command(f'kill @e[type=minecraft:armor_stand,tag={tag}]')


def clear_all_holograms(mc_command):
    clear_hologram(mc_command, HOLO_TAG_LIKES)
    clear_hologram(mc_command, HOLO_TAG_MONEY)


def spawn_hologram_line(mc_command, x, y, z, text, tag, color="white", bold=False):
    safe_text = json_escape(text)
    bold_str = "true" if bold else "false"

    mc_command(
        f'summon minecraft:armor_stand {x} {y} {z} '
        f'{{Invisible:1b,Marker:1b,NoGravity:1b,Invulnerable:1b,Small:1b,CustomNameVisible:1b,'
        f'Tags:["{tag}"],'
        f'CustomName:\'{{"text":"{safe_text}","color":"{color}","bold":{bold_str}}}\'}}'
    )


def actualizar_toplikes_holograma(mc_command, user_likes):
    clear_hologram(mc_command, HOLO_TAG_LIKES)

    top = sorted(user_likes.items(), key=lambda item: item[1], reverse=True)[:3]

    linea1 = f"1. {top[0][0]}  {top[0][1]}" if len(top) > 0 else "1. ---  0"
    linea2 = f"2. {top[1][0]}  {top[1][1]}" if len(top) > 1 else "2. ---  0"
    linea3 = f"3. {top[2][0]}  {top[2][1]}" if len(top) > 2 else "3. ---  0"

    spawn_hologram_line(mc_command, HOLO_LIKES_X, HOLO_LIKES_Y, HOLO_LIKES_Z, "TOP LIKES", HOLO_TAG_LIKES, "aqua", True)
    spawn_hologram_line(mc_command, HOLO_LIKES_X, HOLO_LIKES_Y - 0.30, HOLO_LIKES_Z, linea1, HOLO_TAG_LIKES, "white", False)
    spawn_hologram_line(mc_command, HOLO_LIKES_X, HOLO_LIKES_Y - 0.55, HOLO_LIKES_Z, linea2, HOLO_TAG_LIKES, "white", False)
    spawn_hologram_line(mc_command, HOLO_LIKES_X, HOLO_LIKES_Y - 0.80, HOLO_LIKES_Z, linea3, HOLO_TAG_LIKES, "white", False)


def actualizar_topmoney_holograma(mc_command, user_money):
    clear_hologram(mc_command, HOLO_TAG_MONEY)

    top = sorted(user_money.items(), key=lambda item: item[1], reverse=True)[:3]

    linea1 = f"1. {top[0][0]}  {top[0][1]}" if len(top) > 0 else "1. ---  0"
    linea2 = f"2. {top[1][0]}  {top[1][1]}" if len(top) > 1 else "2. ---  0"
    linea3 = f"3. {top[2][0]}  {top[2][1]}" if len(top) > 2 else "3. ---  0"

    spawn_hologram_line(mc_command, HOLO_MONEY_X, HOLO_MONEY_Y, HOLO_MONEY_Z, "TOP MONEY", HOLO_TAG_MONEY, "gold", True)
    spawn_hologram_line(mc_command, HOLO_MONEY_X, HOLO_MONEY_Y - 0.30, HOLO_MONEY_Z, linea1, HOLO_TAG_MONEY, "white", False)
    spawn_hologram_line(mc_command, HOLO_MONEY_X, HOLO_MONEY_Y - 0.55, HOLO_MONEY_Z, linea2, HOLO_TAG_MONEY, "white", False)
    spawn_hologram_line(mc_command, HOLO_MONEY_X, HOLO_MONEY_Y - 0.80, HOLO_MONEY_Z, linea3, HOLO_TAG_MONEY, "white", False)