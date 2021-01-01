import Services.Helpers.Exception_Handling.Exception_Handling as eh



try:
    lol = 0
    lol = 1 / lol
except Exception as e:
    eh.formatexception(exception=e)