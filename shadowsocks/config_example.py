# !!! Please rename config_example.py as config.py BEFORE editing it !!!

import logging
# !!! Only edit this line when you update your configuration file !!!
# After you update, the value of CONFIG_VERSION in config.py and
# config_example.py should be the same in order to start the server
CONFIG_VERSION = 1


# Manyuser Interface Settings
# ---------------------------
# If API is enabled, database will no longer be used
# The known web panel that is compatible with the API is SS-Panel V3
# Be careful and check whether your web panel supports this API BEFORE you enable this feature
API_ENABLED = False
# Time interval between 2 pulls from the database or API
CHECKTIME = 30
# Time interval between 2 pushes to the database or API
SYNCTIME = 300
# Timeout for MySQL connection or web socket (if using API)
TIMEOUT = 30

# MySQL Database Config (NO NEED to edit if you set API_ENABLED 'True' above)
MYSQL_HOST = 'db.example.net'
MYSQL_PORT = 3306
MYSQL_USER = 'root'
MYSQL_PASS = 'root'
MYSQL_DB = 'shadowsocks'
MYSQL_USER_TABLE = 'user'
NID = 0

# Shadowsocks MultiUser API Settings
API_URL = 'http://domain/mu'
# API Key (you can find this in the .env file if you are using SS-Panel V3)
API_PASS = 'mupass'
API_NODE_ID = '1'


# Manager Settings
# ----------------
# USUALLY you can just keep this section unchanged
# if you want manage in other server you should set this value to global ip
MANAGER_BIND_IP = '127.0.0.1'
# make sure this port is idle
MANAGER_PORT = 65000


# Server Settings
# ---------------
# Address binding settings
# if you want to bind ipv4 and ipv6 please use '::'
# if you want to bind only all of ipv4 please use '0.0.0.0'
# if you want to bind a specific IP you may use something like '4.4.4.4'
SS_BIND_IP = '::'
# This default method will be replaced by database/api query result if applicable when SS_CUSTOM_METHOD is enabled
SS_METHOD = 'chacha20-ietf-poly1305'
SS_CUSTOM_METHOD = True
# Enforce the use of AEAD ciphers
# When enabled, all requests of creating server with a non-AEAD cipher will be omitted
# For more information, please refer to http://www.shadowsocks.org/en/spec/AEAD-Ciphers.html
SS_ENFORCE_AEAD = False
# Skip listening these ports
SS_SKIP_PORTS = [80]
# TCP Fastopen (Some OS may not support this, Eg.: Windows)
SS_FASTOPEN = False
# Shadowsocks socket timeout
# It should not be too small as some protocol has keep-alive packet of long time, Eg.: BT
SS_TIMEOUT = 310


# Firewall Settings
# -----------------
# These settings are to prevent user from abusing your service
SS_FIREWALL_ENABLED = False
# Mode = whitelist or blacklist
SS_FIREWALL_MODE = 'blacklist'
# Member ports should be INTEGERS
# Only Ban these target ports (for blacklist mode)
SS_BAN_PORTS = [22, 23, 25]
# Only Allow these target ports (for whitelist mode)
SS_ALLOW_PORTS = [53, 80, 443, 8080, 8081]
# Trusted users (all target ports will be not be blocked for these users)
SS_FIREWALL_TRUSTED = [443]
# Banned Target IP List
SS_FORBIDDEN_IP = []


# Debugging and Logging Settings
# --------------------------
# If SS_VERBOSE is true, traceback will be printed to STDIO when an exception is thrown
SS_VERBOSE = False
LOG_ENABLE = True
# Available Log Level: logging.NOTSET|DEBUG|INFO|WARNING|ERROR|CRITICAL
LOG_LEVEL = logging.INFO
LOG_FILE = 'shadowsocks.log'
# The following format is the one suggested for debugging
# LOG_FORMAT = '%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s'
LOG_FORMAT = '%(asctime)s %(levelname)s %(message)s'
LOG_DATE_FORMAT = '%b %d %H:%M:%S'
