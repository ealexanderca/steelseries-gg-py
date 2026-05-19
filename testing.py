"""
This file is for testing and debugging issues with the script.
"""

import sys
import requests
import json
import urllib3
sys.path.append(r"C:\Users\ealex\steelseries-gg-py\src")  # <- parent folder
urllib3.disable_warnings()

from gg import GG
import exceptions as GGex

# Example

gg = GG()

gg.get_chat_mix()
temp=gg.read_sonar()
temp2=gg.apply_sonar(temp)
gg.put_active_EQ(gg.read_EQ_id("bf6 surround","game"))
gg.win_set_vol("game",.7)
gg.put_linkAll_link("game")
# gg.win_set_device("game")

addresses:list[str|None]=[gg.gg.url,gg.reg.url,gg.sonar.url,gg.engine.url,gg.moments.url,gg.prismSyncV2.url,]
datas=[]
gg.read_redirections()
temp=gg.read_sonar()

for address in addresses:
    if address:
        try:
            data=requests.get(address+f"/features",verify=False,json={})
        except:
            datas.append(None)
            continue
        if data.status_code-200 >= 0 and data.status_code-200 <= 99:
            datas.append(json.loads(data.text))
        else:
            datas.append(data)

pass

other_endpoints="""
GET /avneradevices HTTP/1.1
GET /configs HTTP/1.1
GET /contentViewHistory/FTUE_Postgame_Modal HTTP/1.1
GET /device/248/configurations HTTP/1.1
GET /device/248/globalDeviceSettings HTTP/1.1
GET /device/248/onboardAudioEffectsStatus HTTP/1.1
GET /device/249 HTTP/1.1
GET /deviceOut HTTP/1.1
GET /devices HTTP/1.1
GET /features HTTP/1.1
GET /features/Bindable HTTP/1.1
GET /features/BuiltInEq HTTP/1.1
GET /features/HeadphoneOut HTTP/1.1
GET /features/HeadphoneOut HTTP/1.1
GET /features/LineOut HTTP/1.1
GET /moments/autoclipNames HTTP/1.1
GET /moments/clips HTTP/1.1
GET /moments/clips/currentSchemaVersion HTTP/1.1
GET /moments/contentViewHistory/FTUE_Postgame_Modal HTTP/1.1
GET /moments/games HTTP/1.1
GET /moments/memoryInfo HTTP/1.1
GET /moments/multimediadevices HTTP/1.1
GET /moments/settings HTTP/1.1
GET /moments/settings/getAvailableMonitors HTTP/1.1
GET /moments/storage HTTP/1.1
GET /multimediaDevices HTTP/1.1
# related to the engine headset profiles
POST /configuration/ed3a2294-9e87-474e-bd52-f3b5d23247d0/deploy HTTP/1.1
GET /quickset/isEnabled HTTP/1.1
GET /quickset/profiles HTTP/1.1
GET /quickset/selected HTTP/1.1
GET /settings HTTP/1.1
GET /startup/allowed HTTP/1.1
GET /streamRedirections/isStreamMonitoringEnabled HTTP/1.1
GET /streamRedirections/isStreamMonitoringLocked HTTP/1.1
GET /subApps HTTP/1.1
GET /user HTTP/1.1
GET /user/linkedAccounts HTTP/1.1
GET /v1/loadouts HTTP/1.1
GET /v1/loadouts/active HTTP/1.1
GET /v1/loadouts/presets HTTP/1.1
GET /v1/loadouts/status HTTP/1.1
GET /v1/status HTTP/1.1
POST /device/248/function/engine_fw_versions HTTP/1.1
POST /device/248/function/get_fw_version/checkBootloader HTTP/1.1
POST /device/248/function/is-supported-version HTTP/1.1
POST /game_metadata HTTP/1.1
POST /moments/clips/delete HTTP/1.1 json={"id":"f603cef5-6d59-46d3-8282-3dab5c5d0c9f","source":"gallery_single_delete_modal"}
POST /moments/settings HTTP/1.1 json={"enabled":true,"display_notifications":true,"enable_game_event_clips":false,"is_mic_muted":false,"capture_cursor":true,"clip_save_sound_enabled":true,"clip_save_sound_volume":100,"brand_exported_clips":false,"brand_overlay_position":"bottom-left","moments_postgame":true,"moments_postgame_modal":true,"enable_gamesense_oled":false,"gamesense_capture_started_oled":true,"gamesense_clip_saved_oled":true,"gamesense_mic_muted_oled":true,"recording_mode":0,"audio_bitrate":192,"audio_samplerate":48000,"capture_delay_event":5,"capture_delay_manual":1,"capture_directory":"C:\\Users\\ealex\\Videos\\SteelSeries Moments","clip_length":300,"trimmed_clip_directory":"C:\\Users\\ealex\\Videos\\SteelSeries Moments\\Exported Clips","shared_clip_directory":"","encoding_crf":28,"framerate":30,"resolution_height":1440,"resolution_width":2560,"audio_output_device":"default","audio_comm_output_device":"defaultCommunication","audio_input_device":"default","selected_monitor":"\\\\.\\DISPLAY1"}
POST /user/reload HTTP/1.1 json={}
PUT /v1/appKeyStore HTTP/1.1 json={"app":"GG","key":"lastVisitedRoute","value":"/gg/moments"}
GET /volumeSettings/devices/volumes HTTP/1.1
PUT /volumeSettings/devices/%7B0.0.1.00000000%7D.%7B459983e4-0a7c-45f1-bdac-f4b9fe498a38%7D/volume/1 HTTP/1.1
GET /v1/loadouts/devicesFamily HTTP/1.1
GET /v1/loadouts/eligibleDevices HTTP/1.1
GET /v1/loadouts/presets HTTP/1.1
GET /v1/connectedDevices HTTP/1.1
GET /testFlags HTTP/1.1
GET /multimediaDevices HTTP/1.1
"""


# possible simple api layout
class GGtemp():

    class Sources():
        def __init__(self,name,gg: GG):
            self.gg=gg
        
        class Source():
            pass


    class Channel():
        def __init__(self,name,gg: GG):
            self.gg=gg
            self.name=name

        class Volume():
            def __init__(self,channel):
                self.channel=channel

        class Mute():
            def __init__(self,channel):
                self.channel=channel
                self()

            def __call__(self, value=None):
                pass

            def toggle(self,):
                self(not self())
                pass


        class EQ():
            def __init__(self,channel):
                self.channel=channel

            def favourites(self,):
                pass

            def set(self,):
                pass
        
        class Redirection():
            def __init__(self,channel):
                self.channel=channel
            
            def __call__(self, value=None):
                pass

            def toggle(self,):
                self(not self())
                pass
