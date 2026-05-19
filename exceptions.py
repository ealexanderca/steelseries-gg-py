class GGError(Exception):
    pass

class ChatMixNotAvailable(GGError):
    def __init__(self, mode):
        self.mode = mode
    def __str__(self):
        if self.mode =='finiteWheel':
            return "Chat Mix is not available! set the output device to one that does not have a hardware dial."
        elif self.mode == 'differentDeviceSelected':
            return "Chat Mix is not available! set game and chat to the same output device."
        else:
            return "Chat Mix is not available! Check sonar for why its not available for software control"

class corePropsNotFound(GGError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"Could not find the coreProps.json at '{self.path}'! Provide the correct path on initialization."

class InvalidUrl(GGError):
    def __init__(self, url):
        self.url = url

    def __str__(self):
        return f"Following url is malformed: {self.url}"

class InvalidApp(GGError):
    def __init__(self, app):
        self.app = app

    def __str__(self):
        return f"Following app is not valid: {self.app}"

class testError(GGError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"
    
class connectionError(GGError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return f"{self.msg}"

class InvalidRequest(GGError):
    def __init__(self, url,code):
        self.url = url
        self.code = code

    def __str__(self):
        return f"Error {self.code}, Request of the following url is malformed: {self.url}"

class InvalidChannel(GGError):
    def __init__(self, channel):
        self.channel = channel

    def __str__(self):
        return f"Channel '{self.channel}' does not exist"

class InvalidStreamingSlider(GGError):
    def __init__(self, slider):
        self.slider = slider

    def __str__(self):
        return f"Slider '{self.slider}' does not exist"

class DuplicateEQName(GGError):
    def __init__(self, eq):
        self.eq = eq

    def __str__(self):
        return f"Duplicate EQ Names '{self.eq}'! specifying the channel with nullify this issue!"
    
class EnginePathNotFoundError(GGError):
    def __init__(self, path):
        self.path = path

    def __str__(self):
        return f"Could not find the engine at '{self.path}'! Provide the correct path on initialization."
    

class InvalidDevice(GGError):
    def __init__(self, id):
        self.id = id

    def __str__(self):
        return f"Could not find a device with the id '{self.id}'! Provide a valid id or check if the device is connected."
