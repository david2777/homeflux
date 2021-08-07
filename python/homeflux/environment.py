"""Environmental Constants"""
import os
import ast

DEBUG = bool(os.getenv('HOMEFLUX_DEBUG', False))
TEST = bool(os.getenv('UNIT_TEST', False))

INFLUX_TOKEN = os.getenv("INFLUX_TOKEN")
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_ORG = os.getenv("INFLUX_ORG")

GWP_USER = os.getenv("GWP_USER")
GWP_PASSWORD = os.getenv("GWP_PASSWORD")
GWP_UUID = os.getenv("GWP_UUID")

NUT_USERNAME = os.getenv("NUT_USERNAME", "monuser")
NUT_PASSWORD = os.getenv("NUT_PASSWORD")
NUT_PORT = ast.literal_eval(os.getenv("NUT_PORT", "3493"))
NUT_UPS_NAME = os.getenv("NUT_UPS_NAME", "ups")
NUT_HOSTS = ast.literal_eval(os.getenv("NUT_HOSTS", "{}"))
