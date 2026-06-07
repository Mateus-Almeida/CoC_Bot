######################
# == User Configs == #
######################

# OPTIONAL: Web app (enter empty string to disable)
WEB_APP_URL = "" # (e.g. 12.34.567.890:1234)
PA_USERNAME, PA_PASSWORD = "", "" # only if using pythonanywhere to auto extend hosting

# OPTIONAL: Telegram notifications (enter empty string to disable)
TELEGRAM_BOT_TOKEN = "" # (e.g. 123456789:ABCdefGHIjkl-MNO_pqrSTUvwxYZ)

# OPTIONAL: Groq API key for faster/more accurate OCR (enter empty string to disable)
GROQ_API_KEY = ""

# REQUIRED: Instance Settings
INSTANCE_IDS = ["main"]
ADB_ADDRESSES = ["127.0.0.1:5555"] # Bluestacks ADB addresses in order of instance IDs
DEFAULT_INSTANCE_ID = INSTANCE_IDS[0]

# REQUIRED: General Settings
LOCAL_GUI = False # web app not required
CHECK_INTERVAL = 1 # minutes

# REQUIRED: Upgrade settings
MAX_UPGRADES_PER_CHECK = 10 # applies to both home and builder base
START_FROM_MENU_TOP = True

#   Home base upgrade settings
OPEN_HOME_BUILDERS = 1 # number of home base builders to keep open (not upgrading), suggested to be 0 for maximum efficiency

UPGRADE_HEROES = False # can be overridden on desktop or web app
UPGRADE_HOME_BASE = False # can be overridden on desktop or web app
UPGRADE_HOME_LAB = False # can be overridden on desktop or web app
ASSIGN_LAB_ASSISTANT = False # can be overridden on desktop or web app
ASSIGN_BUILDER_ASSISTANT = False # can be overridden on desktop or web app

PRIORITY_HOME_BASE_UPGRADES = True # if false, will upgrade in random order regardless of priority settings (can be overridden on desktop or web app)
PRIORITY_HOME_LAB_UPGRADES = True # if false, will upgrade in random order regardless of priority settings (can be overridden on desktop or web app)

#   Every row is a priority level, with the first row being the highest priority
#   Within each row, upgrades are of equal priority and will be randomly chosen between
#   If no listed upgrades are available, will default to random upgrades
#   IMPORTANT: Capitalization and spacing must match exactly with in-game text
#   TIP: It is recommended to minimize the number of priority levels to keep check time reasonable (all upgrades in the same priority are checked in parallel)
HOME_BASE_UPGRADE_PRIORITY = [
    [
        "Laboratory",
        "Blacksmith",
        "Hero Hall",
        "Barbarian King",
        "Archer Queen",
        "Minion Prince",
        "Grand Warden",
        "Royal Champion",
        "Dragon Duke",
    ],
    [
        "Army Camp",
        "Barracks",
        "Dark Barracks",
        "Spell Factory",
        "Dark Spell Factory",
        "Workshop",
        "Clan Castle",
    ],
    [
        "Wall",
    ],
]
HOME_LAB_UPGRADE_PRIORITY = [
    [
        "Balloon",
        "Dragon",
        "Lightning Spell",
        "Rage Spell",
        "Freeze Spell",
        "Poison Spell",
        "Earthquake Spell",
    ],
]

#   Builder base upgrade settings
OPEN_BUILDER_BUILDERS = 1 # number of builder base builders to keep open (not upgrading), suggested to be 0 for maximum efficiency

UPGRADE_BUILDER_BASE = False # can be overridden on desktop or web app
UPGRADE_BUILDER_LAB = False # can be overridden on desktop or web app

PRIORITY_BUILDER_BASE_UPGRADES = True # if false, will upgrade in random order regardless of priority settings (can be overridden on desktop or web app)
PRIORITY_BUILDER_LAB_UPGRADES = True # if false, will upgrade in random order regardless of priority settings (can be overridden on desktop or web app)

#   Every row is a priority level, with the first row being the highest priority
#   Within each row, upgrades are of equal priority and will be randomly chosen between
#   If no listed upgrades are available, will default to random upgrades
#   IMPORTANT: Capitalization and spacing must match exactly with in-game text
#   TIP: It is recommended to minimize the number of priority levels to keep check time reasonable (all upgrades in the same priority are checked in parallel)
BUILDER_BASE_UPGRADE_PRIORITY = [
    [
        "Builder Hall",
        "Multi Mortar",
        "Builder Barracks",
        "Battle Machine",
        "Battle Copter",
        "Star Laboratory",
    ],
    [
        "Gold Storage",
        "Elixir Storage",
        "Double Cannon",
        "Archer Tower",
    ],
]
BUILDER_LAB_UPGRADE_PRIORITY = [
    [
        "Boxer Giant",
        "Night Witch",
    ],
    [
        "Baby Dragon",
        "Power P.E.K.K.A",
    ],
]

# REQUIRED: Attack Settings
TROOP_DEPLOY_TIME = 2 # seconds
ATTACK_SLOT_RANGE = (0, 100) # inclusive, first slot is index 0
EXCLUDE_CLAN_TROOPS = False
ATTACK_HOME_BASE = True # can be overridden on desktop or web app
ATTACK_BUILDER_BASE = False # can be overridden on desktop or web app
CLEAR_POPUPS_BEFORE_ATTACK = False # True to run preventative popup cleaning before matchmaking (adds ~5s)

########################
# == System Configs == #
########################
DEBUG = True
DISABLE_DEVICE_SLEEP = True
WINDOW_DIMS = (1920, 1080) # width, height
ADB_ABS_DIR = r"C:\Users\almeima2\Pictures\Clash_auto\CoC_Bot\bin" # absolute path to dir with adb executable, leave empty to use system PATH

# == Memory & Optimization Configs == #
CLEAN_EMULATOR_ON_CYCLE = True # Clean Android RAM/cache via ADB on each cycle
RESTART_EMULATOR_CYCLE_INTERVAL = 10 # Restart BlueStacks process after this many cycles (0 to disable)
AUTO_COMPLETE_BATTLE = True # True to restart app and skip battle time; False to wait until battle finishes humanly

# == Attack Cloud / Matchmaking Configs == #
CLOUD_CANCEL_AFTER = 25     # segundos antes de cancelar a busca por oponente e retentar
MAX_CANCEL_RETRIES = 2      # máximo de cancelamentos por ciclo de busca
MATCHMAKING_SCREENSHOT_INTERVAL = 0.8  # segundos entre capturas ADB na busca nas nuvens (menor valor = detecção mais rápida)


# == Logging Configs == #
LOG_DIR = "logs"            # pasta relativa ao src/ onde salvar os logs de sessão
MAX_LOG_FILES = 10          # máximo de arquivos de log retidos (os mais antigos são removidos)