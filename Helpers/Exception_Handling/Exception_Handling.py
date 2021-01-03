import json
import traceback

def formatexception(exception):
    response = {
        "traceback": traceback.format_exc(),
        "exception": exception
    }
    return str(response)

