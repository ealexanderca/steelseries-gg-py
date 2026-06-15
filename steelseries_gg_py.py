from requests import Session, RequestException, put
import json
from os import path, environ
from uuid import uuid4
from urllib3 import disable_warnings
import exceptions as ex
from urllib.parse import urlparse
from typing import Callable, Any, overload
import psutil
from pycaw.pycaw import AudioUtilities
from pycaw.utils import AudioDevice
import logging

def generate_id() -> str:
    return str(uuid4())

def is_valid_url(url:str) -> bool:
    try:
        r = urlparse(url)
        return all([r.scheme, r.netloc])
    except Exception:
        return False

def to_bool(v:Any) -> bool:
    return str(v).lower() in {"true","1","yes"}

def is_null(v:Any) -> bool:
    return v is None or str(v).lower() in {"", "null", "none"}

class GG():

    def __init__(self, coreProps_path:str|None=None):
        self.valid_apps={"engine":"gg","moments":"gg","sonar":"gg","threeDAT":"gg","prismSyncV2":"engine"}
        self.EQ_filters:list[str]=["selected","default"]
        self.EQ_render_channels=["game", "chatRender", "media", "aux"]
        self.render_display_channels=["Game", "Chat", "Media", "Aux"]
        self.EQ_channels:list[str]=self.EQ_render_channels + ["chatCapture"]
        self.EQ_display_channels:list[str]=self.render_display_channels + ["Mic"]
        self.channels:list[str] = ["master"] + self.EQ_channels
        self.render_channels:list[str] = ["master"] + self.EQ_render_channels
        self.display_channels:list[str] = ["Master"] + self.EQ_display_channels
        self.mode_options:list[str] = ["stream","classic"]
        self.streamer_sliders:list[str] = ["streaming", "monitoring"]
        self.classic_render_devices=["game", "chat", "media", "aux"]
        self.classic_devices=self.classic_render_devices + ["mic"]
        self.stream_devices=self.streamer_sliders + ["mic"]
        self.coreProps_path:str = path.join(environ["ProgramData"],"SteelSeries","SteelSeries Engine 3","coreProps.json",)
        self.last_sonar_ip=None
        # Type annotations for dynamically added EndPoint attributes
        self.gg: GG.EndPoint
        self.reg: GG.EndPoint
        self.engine: GG.EndPoint
        self.moments: GG.EndPoint
        self.sonar: GG.EndPoint
        self.threeDAT: GG.EndPoint
        self.prismSyncV2: GG.EndPoint
        if coreProps_path:
            self.coreProps_path = coreProps_path

        disable_warnings()
        self.session = Session()
        self.session.verify = False
        self.status=self._reinit()

    def _reinit(self,):
        try:
            if not path.exists(self.coreProps_path):
                raise ex.corePropsNotFound(self.coreProps_path)
            with open(self.coreProps_path, "r") as rf:
                common_app_data = json.load(rf)
                self.gg = self.EndPoint(self,"gg",f'https://{common_app_data["ggEncryptedAddress"]}',)
                self.reg = self.EndPoint(self,"reg",f'http://{common_app_data["address"]}',)
        except:
            self.gg = self.EndPoint(self,"gg")
            self.reg = self.EndPoint(self,"reg")
            
        for app in self.valid_apps:
            try:
                setattr(self,app, self.EndPoint(self,app,parent_address=getattr(self, self.valid_apps[app]).url))
            except:
                setattr(self, app, self.EndPoint(self,app))

    def _wrapped_requests(self,method:str,server:EndPoint,url_path:str, **kwargs) -> dict:
        logging.debug(f"Sending {method.upper()} request to {server.name} with path {url_path} and kwargs {kwargs}")
        if "verify" not in kwargs:
            kwargs["verify"]=False
        tries=2
        if not is_valid_url(server("")):
            self._reinit()
            tries=1

        if server("") and not is_valid_url(server(url_path)):
            raise ex.InvalidUrl(url_path)
        
        for i in range(tries):
            try:
                response = self.session.request(method, server(url_path), **kwargs)
                break
            except RequestException:
                if i<tries:
                    self._reinit()
        else:
            raise ex.connectionError(f"request could not be sent to {server.name} {url_path}")
        
        if not response.ok:
            raise ex.InvalidRequest(url_path,response.status_code)
        
        if response.text=="":
            return {}
        return response.json()

    def _volume_path(self,streamer_mode:bool) -> str:
        return "/volumeSettings/streamer" if streamer_mode else "/volumeSettings/classic"

    def _load_function_json(self,data:dict) -> Any:
        data=data["function_data"]
        if isinstance(data,str):
            try:
                return json.loads(data)
            except:
                pass
        return data

    # direct requests

    def get_streamMonitoringLocked(self)->bool:
        return bool(self._wrapped_requests("get", self.sonar,"/streamRedirections/isStreamMonitoringLocked"))

    def get_fallbackSettings_isEnabled(self) -> bool:
        return bool(self._wrapped_requests("get", self.sonar,"/fallbackSettings/isEnabled"))

    def put_fallbackSettings_isEnabled(self,isEnabled:bool|str) -> bool:
        if type(isEnabled) is str and isEnabled.lower() == "toggle":
            isEnabled = not self.get_fallbackSettings_isEnabled()
        isEnabled = to_bool(isEnabled)
        return bool(self._wrapped_requests("put", self.sonar,f"/fallbackSettings/isEnabled/{isEnabled}"))

    def get_link(self,):
        return self._wrapped_requests("get", self.sonar,f"/linkAll/isRenderLinkAllEnabled")

    def put_linkAll_unlink(self) -> bool:
        return bool(self._wrapped_requests("put", self.sonar,f"/linkAll/unlink"))

    def put_linkAll_link(self,channel:str) -> dict:
        if channel not in self.EQ_channels:
            raise ex.InvalidChannel(channel)
        return self._wrapped_requests("put", self.sonar,f"/linkAll/link/{channel}")

    def multimediaDevices(self) -> dict:
        return self._wrapped_requests("put", self.sonar,"/multimediaDevices")

    def get_scanned_games(self) -> dict[str, list[dict]]:
        return self._wrapped_requests("get", self.gg,"/scannedGames")

    def get_locale(self) -> dict[str, list[dict]]:
        return self._wrapped_requests("get", self.gg,"/locale")

    def get_known_games(self) -> dict[str, list[dict]]:
        return self._wrapped_requests("get", self.gg,"/known_games")

    def get_chat_mix(self) -> dict:
        return self._wrapped_requests("get", self.sonar,"/chatMix")

    def get_applications(self) -> dict[str, list[dict]]:
        return self._wrapped_requests("get", self.engine,"/applications")

    def get_application_settings(self) -> dict[str, list[dict]]:
        return self._wrapped_requests("get", self.engine,"/application_setting")

    def get_devices(self) -> dict[str, list[dict]]:
        return self._wrapped_requests("get", self.engine,"/devices")

    def get_device(self, number:int) -> dict:
        return self._wrapped_requests("get", self.engine,f"/device/{number}")

    def get_device_configurations(self, number:int):
        return self._wrapped_requests("get", self.engine,f"/device/{number}/configurations")

    def get_device_routing(self):
        return self._wrapped_requests("get", self.sonar,"/AudioDeviceRouting")

    def get_stream_monitoring(self) -> bool:
        return bool(self._wrapped_requests("get", self.sonar,"/streamRedirections/isStreamMonitoringEnabled"))     

    def get_streamer_mode(self) -> bool:
        return self._wrapped_requests("get",self.sonar,"/mode/") == "stream"

    def get_volume(self) -> dict:
        streamer_mode=self.get_streamer_mode()
        volume_path = self._volume_path(streamer_mode)
        
        url_path = volume_path
        return self._wrapped_requests("get",self.sonar,url_path)

    def get_EQs(self, channel:str|None=None, flag:str|None=None) -> dict:
        if channel not in self.EQ_channels + [None]:
            raise ex.InvalidChannel(channel)
    
        if flag == "default" and channel not in self.EQ_channels:
            raise ex.InvalidChannel(channel)
        
        url_path = "/configs"
        if flag in self.EQ_filters:
            url_path = f"{url_path}/{flag}"
    
        if flag == "default":
            url_path = f"{url_path}?virtualAudioDevice={channel}"
        elif channel:
            url_path = f"{url_path}?vad={channel}"

        return self._wrapped_requests("get",self.sonar,url_path)        

    def get_audio_devices(self, assignable:bool=False) -> dict:
        url_path = "/audioDevices"
        if assignable:
            url_path = f"{url_path}?removeSteelSeriesVAD=true"

        return self._wrapped_requests("get",self.sonar,url_path)

    def get_redirections(self,) -> dict:
        streamer_mode=self.get_streamer_mode()
        if streamer_mode:
            url_path = "/streamRedirections"
        else:
            url_path = "/classicRedirections"

        return self._wrapped_requests("get",self.sonar,url_path)

    def put_audio_device_routing(self, device_id:str, pid:str|int):
        logging.debug(f"Routing device {device_id} to pid {pid}")
        return self._wrapped_requests("put", self.sonar,f"/AudioDeviceRouting/render/{device_id}/{pid}")

    def put_active_EQ(self, id:str|None):
        if id is None:
            return False
        return bool(self._wrapped_requests("put", self.sonar,f"/configs/{id}/select"))

    def put_EQ(self, EQ_json:dict):
        return self._wrapped_requests("put", self.sonar,"/configs", json=EQ_json)

    def put_stream_monitoring(self, enabled:str|bool) -> dict:
        if type(enabled) is str and enabled.lower() == "toggle":
            enabled = not self.get_stream_monitoring()
        enabled = to_bool(enabled)
        return self._wrapped_requests("put",self.sonar,f"/streamRedirections/isStreamMonitoringEnabled/{str(enabled)}")

    def put_streamer_mode(self, streamer_mode:bool|str) -> bool:
        if type(streamer_mode) is str and streamer_mode.lower() == "toggle":
            streamer_mode = not self.get_streamer_mode()
        if streamer_mode in self.mode_options:
            mode=streamer_mode
        if streamer_mode:
            mode = "stream"
        else:
            mode = "classic"
        return self._wrapped_requests("put",self.sonar,f"/mode/{mode}") == "stream"

    def put_volume(self, channel:str, volume:str|float, streamer_slider:str="streaming") -> dict:
        streamer_mode=self.get_streamer_mode()
        
        if channel not in self.channels:
            raise ex.InvalidChannel(channel)

        if streamer_mode and streamer_slider not in self.streamer_sliders:
            raise ex.InvalidStreamingSlider(streamer_slider)
        
        if isinstance(volume,str):
            if "r" in volume:
                if streamer_mode:
                    cur_vol=self.read_volume()[channel][streamer_slider]['volume']
                else:
                    cur_vol=self.read_volume()[channel]['volume']
                volume=volume.replace("r","")
                volume=cur_vol + float(volume)
            else:
                volume = float(volume)

        volume = max(0, min(volume, 1))

        url_path = self._volume_path(streamer_mode)
        if streamer_mode:
            url_path += f"/{streamer_slider}"

        return self._wrapped_requests("put",self.sonar,f"{url_path}/{channel}/Volume/{json.dumps(volume)}")

    def put_mute(self, channel:str, muted:str|bool|int, streamer_slider:str="streaming") -> dict:
        streamer_mode=self.get_streamer_mode()
        if channel not in self.channels:
            raise ex.InvalidChannel(channel)

        if streamer_mode and streamer_slider not in self.streamer_sliders:
            raise ex.InvalidStreamingSlider(streamer_slider)
        
        if type(muted) is str and muted.lower() == "toggle":
            if streamer_mode:
                muted = not self.read_volume()[channel][streamer_slider]["muted"]
            else:
                muted = not self.read_volume()[channel]["muted"]

        muted = to_bool(muted)
        url_path = self._volume_path(streamer_mode)
        if streamer_mode:
            url_path = f"{url_path}/{streamer_slider}"

        mute_keyword = "isMuted" if streamer_mode else "Mute"

        return self._wrapped_requests("put",self.sonar,f"{url_path}/{channel}/{mute_keyword}/{json.dumps(muted)}")

    def read_audio_initialization(self,channel:str) -> bool:
        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        return channel in self.read_sonar_devices()

    def put_audio_initialization(self, channel:str, enabled:bool|str) -> dict:

        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        if type(enabled) is str and enabled.lower() == "toggle":
            enabled = not self.read_audio_initialization(channel)

        enabled = to_bool(enabled)

        url_path = f"/audioInitialization/{channel}/isEnabled/{json.dumps(enabled)}"

        return self._wrapped_requests("put",self.sonar,url_path)

    def put_chat_mix(self, mix_volume:str|int|float) -> dict:
        current_mix=self.get_chat_mix()
        if not current_mix["state"]=="enabled":
            raise ex.ChatMixNotAvailable(current_mix["state"])
        if isinstance(mix_volume,str):
            if "r" in mix_volume:
                cur_vol=current_mix["balance"]
                mix_volume=mix_volume.replace("r","")
                mix_volume=cur_vol + float(mix_volume)
            else:
                mix_volume = float(mix_volume)

        mix_volume = max(-1, min(mix_volume, 1))

        return self._wrapped_requests("put",self.sonar,f"/chatMix?balance={json.dumps(mix_volume)}")

    def put_redirections_deviceId(self,deviceId:bool|str,channel:str="render", streamer_slider:str="streaming"):
        streamer_mode=self.get_streamer_mode()
        if channel not in self.classic_devices +["render"]:
            raise ex.InvalidChannel(channel)
        
        if streamer_mode and streamer_slider not in self.stream_devices:
            raise ex.InvalidStreamingSlider(streamer_slider)
            
        if streamer_mode:
            url_path = f"/streamRedirections/{streamer_slider}/deviceId/{deviceId}"
        else:
            url_path = f"/classicRedirections/{channel}/deviceId/{deviceId}"
        return self._wrapped_requests("put",self.sonar,url_path)

    def put_redirections_isEnabled(self, channel:str, enable:bool|str, streamer_slider:str="streaming") -> dict:
        streamer_mode=self.get_streamer_mode()
        if channel not in self.EQ_channels:
            raise ex.InvalidChannel(channel)
        
        if streamer_mode and streamer_slider not in self.streamer_sliders:
            raise ex.InvalidStreamingSlider(streamer_slider)
        
        if type(enable) is str and enable.lower() == "toggle":
            enable = not self.read_redirections()[streamer_slider][channel]
            
        if streamer_mode:
            url_path = f"/streamRedirections/{streamer_slider}/redirections/{channel}/isEnabled/{str(enable)}"
        else:
            url_path = f"/classicRedirections/redirections/{channel}/isEnabled/{str(enable)}"

        return self._wrapped_requests("put",self.sonar,url_path)

    def post_device_battery(self, number:int) -> dict[str,str]:
        return self._load_function_json(self._wrapped_requests("post", self.engine,f"/device/{number}/function/read_battery_status", json={}))

    def post_device_connection_status(self, number:int):
        return self._load_function_json(self._wrapped_requests("post", self.engine,f"/device/{number}/function/read_connection_status", json={}))

    def post_subApps_status(self,name:str,enable:bool) -> dict:
        enable = to_bool(enable)
        
        for app in self.valid_apps:
            if app == name:
                break
        else:
            raise ex.InvalidApp(name)
        return self._wrapped_requests("post",getattr(self, self.valid_apps[app]),'/subApps/status',json={"name":name,"isEnabled":enable})

    def post_EQ(self, EQ_json:dict):
        return self._wrapped_requests("post", self.sonar,"/configs", json=EQ_json)

    def delete_EQ(self, id:str):
        return self._wrapped_requests("delete", self.sonar,f"/configs/{id}")

    # Processed data

    def read_redirections(self,) -> dict:
        streamer_mode=self.get_streamer_mode()
        redirections=self.get_redirections()
        data={}
        if streamer_mode:
            for redirection in redirections:
                data[redirection["streamRedirectionId"]]={}
                redirection_data=data[redirection["streamRedirectionId"]]
                redirection_data["deviceId"]=redirection["deviceId"]
                for channel_data in redirection["status"]:
                    redirection_data[channel_data["role"]]=channel_data["isEnabled"]
        else:
            for channel in redirections:
                data[channel["id"]]={}
                for item in ["deviceId","isRunning"]:
                    data[channel["id"]][item]=channel[item]
        return data

    @overload
    def read_EQs(self, channel: str, flag: str|None = None) -> dict: ...
    @overload
    def read_EQs(self, channel: None = None, flag: str|None = None) -> list: ...
    def read_EQs(self,channel:str|None=None, flag:str|None=None) -> dict|list:
        if channel not in self.EQ_channels + [None]:
            raise ex.InvalidChannel(channel)
        
        EQs=self.get_EQs(channel=channel, flag=flag)
        EQs_out={}
        if flag == "selected":
            for EQ in EQs:
                EQs_out[EQ['virtualAudioDevice']]=EQ
            if channel:
                return EQs_out[channel]
            else:
                return EQs_out
        return EQs

    def read_EQ_id(self, name:str, channel:str|None=None) -> str|None:
        if channel not in self.EQ_channels + [None]:
            raise ex.InvalidChannel(channel)
        EQs=self.get_EQs(channel=channel)
        id:str|None = None
        for EQ in EQs:
            if EQ["name"]==name:
                if id==None:
                    id = EQ["id"]
                else:
                    ex.DuplicateEQName(name)
        return id

    def read_device_routing(self,active_only=False,get_path=False) -> dict:
        sources={}
        devices=self.get_device_routing()

        for device in devices:
            for session in device["audioSessions"]:
                if session["state"] == "active" or not active_only:
                    data={}
                    for key in ["displayName","processName","state","id","isRoutingErrorProne","routingErrorDetected"]:
                        data[key]=session[key]
                    if get_path:
                        try:
                            proc = psutil.Process(session["processId"])
                            data["path"] = proc.exe()
                        except:
                            data["path"] = None
                    data["deviceId"]=device["deviceId"]
                    data["role"]=device["role"] if device["role"] != "none" else None
                    if not sources.get(session["processId"],None):
                        sources[session["processId"]]={}
                    sources[session["processId"]][data["role"] if data["role"] else data["deviceId"]]=data
        return sources

    def read_sonar_devices(self,) -> dict:
        self.sonar_device_ids={}
        devices=self.get_audio_devices()
        self.channel_device_data={}
        for device in devices:
            if device["role"] in self.channels:
                self.channel_device_data[device["role"]]=device
        return self.channel_device_data

    def read_sonar_device_id(self, channel:str) -> str:

        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        return self.read_sonar_devices()[channel]["id"]

    def read_sonar_device_friendlyname(self, channel:str) -> str:

        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        return self.read_sonar_devices()[channel]["friendlyName"]

    def read_volume(self,) -> dict:
        val = self.get_volume()
        temp = val["devices"]
        temp["master"] = val["masters"]
        if self.get_streamer_mode():
            for item in temp:
                temp[item]=temp[item]["stream"]
        else:
            for item in temp:
                temp[item]=temp[item]["classic"]
        return temp 

    def get_correct_channels(self,option):
        if option == "redirection":
            channels=self.classic_devices
            render_channels=self.classic_render_devices
        elif option == "eq" or option.endswith("Redirection"):
            channels=self.EQ_channels
            render_channels=self.EQ_render_channels
        else:
            channels=self.channels
            render_channels=self.render_channels
        return channels,render_channels

    def read_sonar(self,options=["redirection","volume","mute","eq","monitoring","speaker","chatMix","audioInitialization"]) -> dict:
        options = [x.lower() if isinstance(x, str) else x for x in options]
        profile={}
        profile["streamerMode"]=self.get_streamer_mode()
        channel_settings={}
        if "eq" in options:
            EQs=self.read_EQs(flag="selected")
            channel_settings["eq"]=lambda channel: EQs[channel]["name"]
        if "redirection" in options:
            redirection_data=self.read_redirections()
        if "volume" or "mute" in options:
            volume_data=self.read_volume()
        if "audioInitialization" in options:
            channel_settings["monitoringVolume"]=self.read_audio_initialization
        if profile["streamerMode"]:
            profile["streamMonitoring"]=self.get_stream_monitoring()
            
            if "volume" in options:
                channel_settings["monitoringVolume"]=lambda channel: volume_data[channel]["monitoring"]["volume"]
                channel_settings["streamingVolume"]=lambda channel: volume_data[channel]["streaming"]["volume"]
            if "mute" in options:
                channel_settings["monitoringMute"]=lambda channel: volume_data[channel]["monitoring"]["muted"]
                channel_settings["streamingMute"]=lambda channel: volume_data[channel]["streaming"]["muted"]
            if "redirection" in options:
                channel_settings["monitoringRedirection"]=lambda channel: redirection_data["monitoring"][channel]
                channel_settings["streamingRedirection"]=lambda channel: redirection_data["streaming"][channel]
                for item in self.stream_devices:
                    profile[f"{item}Redirection"]={}
                    profile[f"{item}Redirection"]["deviceId"]=redirection_data[item]["deviceId"]
        else:
            if "volume" in options:
                channel_settings["volume"]=lambda channel: volume_data[channel]["volume"]
            if "mute" in options:
                channel_settings["mute"]=lambda channel: volume_data[channel]["muted"]
            if "redirection" in options:
                channel_settings["redirection"]=lambda channel: redirection_data[channel]["deviceId"]
        
        for setting in channel_settings:
            channels,_=self.get_correct_channels(setting)
            if setting not in profile:
                profile[setting] = {}
            for channel in channels:
                profile[setting][channel]=channel_settings[setting](channel)
        if "speaker" in options:
            profile["speaker"]=self.win_get_speaker_channel()
        if "chatMix" in options:
            profile["chatMix"]=self.get_chat_mix()["balance"]
        return profile

    def write_sonar(self, profile:dict, error_handler:Callable|None=None, win_volume=False,pid:int|None=None) -> bool:
        fully_applied=True
        if "streamerMode" in profile:
            streamer_mode=profile["streamerMode"]
            self.put_streamer_mode(streamer_mode)
        else:
            streamer_mode=self.get_streamer_mode()
        channel_settings={}
        channel_settings["eq"]=lambda channel, val: self.put_active_EQ(self.read_EQ_id(val, channel))  

        if not streamer_mode and pid and "channel" in profile:
            try:
                self.write_channel(profile["channel"], pid)
            except ex.GGError:
                if error_handler:
                    error_handler("channel",profile["channel"],None)
                    fully_applied=False
                else:
                    raise

        channel_settings["audioInitialization"]=self.put_audio_initialization

        if streamer_mode:
            if "streamMonitoring" in profile:
                self.put_stream_monitoring(profile["streamMonitoring"])

            channel_settings["monitoringRedirection"]= lambda channel, val: self.put_redirections_isEnabled(channel, val, "monitoring")
            channel_settings["streamingRedirection"]= self.put_redirections_isEnabled
            channel_settings["monitoringVolume"]= lambda channel, val: self.put_volume(channel, val, "monitoring")
            channel_settings["streamingVolume"]= self.put_volume
            channel_settings["monitoringMute"]= lambda channel, val: self.put_mute(channel, val, "monitoring")
            channel_settings["streamingMute"]= self.put_mute

            for item in self.stream_devices:
                if isinstance(profile.get(f"{item}Redirection"),dict) and profile[f"{item}Redirection"].get("deviceId"):
                    self.put_redirections_deviceId(profile[f"{item}Redirection"]["deviceId"],streamer_slider=item) 
        else:
            channel_settings["redirection"]= self.put_redirections_deviceId
            if win_volume:
                channel_settings["volume"]= self.win_set_vol
                channel_settings["mute"]= self.win_set_mute
            else:
                channel_settings["volume"]= self.put_volume
                channel_settings["mute"]= self.put_mute

        for option in channel_settings:
            if not profile.get(option):
                continue
            channels,_=self.get_correct_channels(option)
            all_options=["all","allRender"]
            for item in all_options:
                if item in profile[option]:
                    val=profile[option][item]
                    for channel in channels:
                        try:
                            channel_settings[option](channel, val)
                        except ex.GGError:
                            if error_handler:
                                error_handler(option,val,channel)
                                fully_applied=False
                            else:
                                raise
            for channel in profile[option]:
                if channel not in channels:
                    continue
                channel_settings[option](channel, profile[option][channel])
        if "speaker" in profile:
            try:
                self.win_set_speaker(profile["speaker"])
            except ex.GGError:
                if error_handler:
                    error_handler("speaker",profile["speaker"],None)
                    fully_applied=False
                else:
                    raise
        if "chatMix" in profile:
            try:
                self.put_chat_mix(profile["chatMix"])
            except ex.GGError:
                if error_handler:
                    error_handler("chatMix",profile["chatMix"],None)
                    fully_applied=False
                else:
                    raise
        return fully_applied

    def write_channel(self,channel:str, pid: int,check_level:int=2) -> bool:
        '''
        check_level
        0 = no checks, will send pid and device to the engine
        1 = will add check if the pid exists in windows
        2 = will add check if the pid exists in sonar
        3 = will add check if the source has errors when swapped by sonar
        4 = will add check if the device is active in sonar
        '''
        
        if channel not in self.EQ_channels:
            raise ex.InvalidChannel(channel)

        device=self.read_sonar_device_id(channel)

        if check_level==1 and not psutil.pid_exists(pid):
            return False
        
        if check_level>1:
            data=self.read_device_routing()
            
            if pid not in data:
                return False
    
            for channel in data[pid]:
                if data[pid][channel]["deviceId"]==device and data[pid][channel]["state"]=="active":
                    return True

            if check_level>2 and data[pid]["isRoutingErrorProne"]:
                return False

            if check_level>3 and data[pid]["state"]=="active":
                return False

        self.put_audio_device_routing(device, pid)
        return True

    def win_get_device(self,id) -> AudioDevice|None: 
        devices = AudioUtilities.GetAllDevices()
        for device in devices:
            if device.id.lower()==id.lower():
                return device
        else:
            return None

    def win_set_vol(self,channel,val):
        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        if channel=="master":
            return self.put_volume(channel, val)
        id=self.read_sonar_device_id(channel)
        device=self.win_get_device(id)
        if device is None:
            raise ex.InvalidDevice(id)
        volume = device.EndpointVolume
        volume.SetMasterVolumeLevelScalar(val, None)
        return volume.GetMasterVolumeLevelScalar()

    def win_set_mute(self,channel,muted):
        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        
        if type(muted) is str and muted.lower() == "toggle":
            muted = not self.read_volume()[channel]["muted"]

        muted = to_bool(muted)
        if channel=="master":
            return self.put_mute(channel, muted)

        id=self.read_sonar_device_id(channel)
        device:AudioDevice|None = self.win_get_device(id)
        if device is None:
            raise ex.InvalidDevice(id)
        volume = device.EndpointVolume
        volume.SetMute(int(muted), None)
        return volume.GetMute()

    def win_get_speaker(self,) -> AudioDevice|None:
        return AudioUtilities.GetSpeakers()

    def win_get_speaker_channel(self,) -> str|None:
        speaker=self.win_get_speaker()
        if speaker is None:
            return None
        devices=self.read_sonar_devices()
        for device in devices:
            if devices[device]["id"].lower()==speaker.id.lower():
                return devices[device]["role"]
        return speaker.id

    def win_set_speaker(self,channel):
        if channel not in self.channels:
            raise ex.InvalidChannel(channel)
        id=self.read_sonar_device_id(channel)
        AudioUtilities.SetDefaultDevice(id)
        return channel==self.win_get_speaker_channel()

    # Class for the automatic url gathering

    class EndPoint():

        def __init__(self,parent:GG,name:str,address:str|None=None,parent_address:str|None=None):
            self.name:str = name
            self.parent:GG=parent
            self.isEnabled:bool = False
            self.isReady:bool = False
            self.isRunning:bool = False
            self.url:str|None = ""
            if parent_address:
                self.url = self.load_address(parent_address,name)
            else:
                self.url = address

        def __call__(self,path:str) -> str:
            return f"{self.url}{path}"

        def load_address(self,address:str|None,app:str) -> str:
            failed=False
            try:
                response = self.parent.session.request("get", f"{address}/subApps", verify=False)
            except RequestException:
                failed=True
            if failed or response.status_code != 200:
                self.isEnabled = False
                self.isReady = False
                self.isRunning = False
                url = ""
            else:
                data = response.json()
                self.isEnabled = data["subApps"][app]["isEnabled"]
                self.isReady = data["subApps"][app]["isReady"]
                self.isRunning = data["subApps"][app]["isRunning"]
                
                url = data["subApps"][app]["metadata"]["webServerAddress"]
                if is_null(url):
                    url = data['subApps'][app]['metadata']['encryptedWebServerAddress']
                    if "http" not in url:
                        url = f"https://{url}"
                if "http" not in url:
                    url = f"http://{url}"
                if is_null(url):
                    url = ""
            return url
