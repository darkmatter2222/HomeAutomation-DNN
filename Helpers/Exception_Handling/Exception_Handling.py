import json
import traceback

def formatexception(exception):
    response = {
        "traceback": traceback.format_exc(),
        "exception": exception
    }
    return json.dumps(response, indent=2)

