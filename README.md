# steelseries-gg-py
An API to interface with the SteelSeries GGs various apps.
Currently the endpoints are restricted to the Sonar and engine endpoint for audio control as I only own a steelseries headset
most endpoints have individual function calls to set the data but to control sonar the best simplest functions to use are the apply_sonar and read_sonar.
read sonar takes options as an input to select what data to read and what endpoints to hit. selecting less options will reduve the endpoints required for data collection.
## Example classic mode dict
```json
{
  "streamer_mode": false,
  "eq": {
    "game": "Flat",
    "chatRender": "Flat",
    "media": "Flat",
    "aux": "Flat",
    "chatCapture": "Flat"
  },
  "volume": {
    "master": 1.0,
    "game": 1.0,
    "chatRender": 1.0,
    "media": 1.0,
    "aux": 1.0,
    "chatCapture": 1.0
  },
  "mute": {
    "master": false,
    "game": false,
    "chatRender": false,
    "media": false,
    "aux": false,
    "chatCapture": false
  },
  "redirection": {
    "game": "{0.0.0.00000000}.{318083ea-3e25-4187-ab53-80597d9abcd9}",
    "chat": "{0.0.0.00000000}.{318083ea-3e25-4187-ab53-80597d9abcd9}",
    "media": "{0.0.0.00000000}.{318083ea-3e25-4187-ab53-80597d9abcd9}",
    "aux": "{0.0.0.00000000}.{318083ea-3e25-4187-ab53-80597d9abcd9}",
    "mic": "{0.0.1.00000000}.{c546c47d-c76c-4b8c-ba7c-70e3509e4b8e}"
  }
}
```
## Example streamer mode dict
```json
{
  "streamer_mode": true,
  "streamMonitoring": false,
  "streamingRedirection": {
    "deviceId": "{0.0.0.00000000}.{0b707a69-1b89-49d5-a10b-46483c52f978}",
    "game": false,
    "chatRender": false,
    "media": false,
    "aux": false,
    "chatCapture": true
  },
  "monitoringRedirection": {
    "deviceId": "{0.0.0.00000000}.{318083ea-3e25-4187-ab53-80597d9abcd9}",
    "game": true,
    "chatRender": true,
    "media": true,
    "aux": true,
    "chatCapture": false
  },
  "micRedirection": {
    "deviceId": "{0.0.1.00000000}.{c546c47d-c76c-4b8c-ba7c-70e3509e4b8e}"
  },
  "eq": {
    "game": "Flat",
    "chatRender": "Flat",
    "media": "Flat",
    "aux": "Flat",
    "chatCapture": "Flat"
  },
  "monitoringVolume": {
    "master": 1.0,
    "game": 1.0,
    "chatRender": 1.0,
    "media": 1.0,
    "aux": 1.0,
    "chatCapture": 1.0
  },
  "streamingVolume": {
    "master": 1.0,
    "game": 1.0,
    "chatRender": 1.0,
    "media": 1.0,
    "aux": 1.0,
    "chatCapture": 1.0
  },
  "monitoringMute": {
    "master": false,
    "game": false,
    "chatRender": false,
    "media": false,
    "aux": false,
    "chatCapture": false
  },
  "streamingMute": {
    "master": false,
    "game": false,
    "chatRender": false,
    "media": false,
    "aux": false,
    "chatCapture": false
  }
}
```


# auto_sonar
This is a application that allows for the automatic swapping of sonar settings based on active application.
It allows for changing settings based on the active application based on the process name or the folder

## config structure
### poll_interval_ms
time between each check of the active application.
### app_detection_enabled
toggles the automatic detection on startup.
### simple_icons
if set to true it will display an icon that can be set through the porilfes colors. if set to false it will show an icon that is based off the current active applications profile image. will not necessarilly match the profile but will show if the detection is working.
#### profiles
##### color
can either be a single string color or a list of 2 colors that are used to set the simple icon colors
##### description
simple description of the profiles
##### folders
folder paths will be evaluated so you can use environment variables such as "%LOCALAPPDATA%
##### names
matched to the executable name for the active application
##### channel
this will move any application detected under this profile to the matching channel for automatic swapping 
### example

#
```json
{
  "poll_interval_ms": 500,
  "app_detection_enabled": true,
  "simple_icons":true,
  "profiles": {
    "default": {
      "color": "#ff4444",
      "description": "Default profile",
      "sonar":{
        "volume": {"game":1},
        "eq": {"all":"Flat"},
        "mute": {"all":false}
      },
    },
    "R6S": {
      "folders": ["%LOCALAPPDATA%\\Ubisoft\\r6s","C:\\Program Files (x86)\\Steam\\steamapps\\common\\Tom Clancy's Rainbow Six Siege"],
      "description": "Rainbow Six Siege",
      "channel": "game",
      "color":["#eeff00","#222222"],
      "sonar":{
        "volume": {"game":1.0},
        "eq": {"game":"r6s footboost"}
      }
    },
    "BF6": {
      "folders": ["C:\\Program Files (x86)\\Steam\\steamapps\\common\\Battlefield 6"],
      "names":["bf6"],
      "description": "BattleField6",
      "channel": "game",
      "color": ["#ff4444","#44ff44"],
      "sonar":{
        "volume": {"game":0.6},
        "eq": {"game":"bf6 surround"},
        "mute": {"game":false}
      }
    },
    "code": {
      "folders": [""],
      "names":["code.exe"],
      "description": "code test",
      "color": ["#23a9f2","#0076b8"]
    },
    "teams": {
      "folders": [""],
      "names":["teams.exe"],
      "description": "teams test",
      "color": ["#8091F2","#4E5FBF"]
    }
  },
}
```