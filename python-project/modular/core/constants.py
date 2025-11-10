# constants.py
import os
PATH_TO_C_EXE = "./TestGlove64.exe"
GLOVE_CONNECTION_PORT = "USB0"
IMAGES_FOLDER = os.path.join(os.path.dirname(__file__), "..", "assets", "gesture-images")


IMAGE_MAP = {
    0: "0.png", 1: "1.png", 2: "2.png", 3: "3.png", 4: "4.png",
    5: "5.png", 6: "6.png", 7: "7.png", 8: "8.png", 9: "9.png",
    10: "10.png", 11: "11.png", 12: "12.png", 13: "13.png",
    14: "14.png", 15: "15.png", -1: "-1.png",
}

SENSOR_NAMES = [
    "Thumb Near", "Thumb Far", "Thumb/Index", "Index Near", "Index Far",
    "Index/Middle", "Middle Near", "Middle Far", "Middle/Ring", "Ring Near",
    "Ring Far", "Ring/Little", "Little Near", "Little Far",
    "Thumb Palm", "Wrist Bend", "Roll", "Pitch"
]
