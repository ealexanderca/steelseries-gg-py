from steelseries_gg_py import GG
import exceptions as ex

def test_all():
    gg = GG()
    # starting and stopping sonar works but will start it on a seperate IP meaning it needs to be started through GG seperate
    # gg._post_subApps_status("sonar",False)
    # gg._post_subApps_status("sonar",True)
    # testing streamer mode, test first because the rest of the script is dependant
    streamer_mode=gg.get_streamer_mode()
    gg.put_streamer_mode(not streamer_mode)
    if gg.get_streamer_mode() == streamer_mode:
        raise ex.testError("issue with the streamer mode being set")
    gg.put_streamer_mode("toggle")
    if gg.get_streamer_mode() != streamer_mode:
        raise ex.testError("issue with the streamer mode being set")

    gg.put_streamer_mode(False)

    # save state tests
    classic_test_dict={'streamer_mode': False, 'eq': {'game': 'bf6 surround', 'chatRender': 'Less Nasal', 'media': 'bass', 'aux': 'Podcast', 'chatCapture': 'Alias - Boom Arm'}, 'volume': {'game': 0.72, 'chatRender': 0.65, 'media': 0.55, 'aux': 0.46, 'chatCapture': 0.33, 'master': 0.84}, 'mute': {'game': 0.72, 'chatRender': 0.65, 'media': 0.55, 'aux': 0.46, 'chatCapture': 0.33, 'master': 0.84}}
    classic_actual_dict=gg.read_sonar()
    gg.write_sonar(classic_test_dict)
    if gg.read_sonar() != gg.read_sonar():
        raise ex.testError("issue with the batch updating")
    gg.write_sonar(classic_actual_dict)

    gg.put_streamer_mode(True)

    # stream mode monitoring
    enabled=gg.get_stream_monitoring()
    gg.put_stream_monitoring(not enabled)
    if gg.get_stream_monitoring() == enabled:
        raise ex.testError("issue with the stream monitoring")
    gg.put_stream_monitoring("toggle")
    if gg.get_stream_monitoring() != enabled:
        raise ex.testError("issue with the stream monitoring")

    # stream mode save state
    streaming_test_dict={'streamer_mode': True, 'stream_monitoring': False, 'eq': {'game': 'r6s footboost', 'chatRender': 'Broadcast', 'media': 'Music: Lo-fi Chill', 'aux': 'Music: Punchy', 'chatCapture': 'Walkie Talkie'}, 'monitorRedirection': {'game': True, 'chatRender': True, 'media': True, 'aux': False, 'chatCapture': False}, 'streamRedirection': {'game': False, 'chatRender': True, 'media': False, 'aux': True, 'chatCapture': True}, 'monitorVolume': {'game': 0.704, 'chatRender': 0.65999997, 'media': 0.6336, 'aux': 0.55439997, 'chatCapture': 0.5, 'master': 0.88}, 'streamVolume': {'game': 0.19600001, 'chatRender': 0.1176, 'media': 0.1274, 'aux': 0.07350001, 'chatCapture': 0.06, 'master': 0.49}, 'monitorMute': {'game': True, 'chatRender': True, 'media': True, 'aux': True, 'chatCapture': True, 'master': True}, 'streamMute': {'game': False, 'chatRender': False, 'media': False, 'aux': False, 'chatCapture': True, 'master': False}}
    streaming_actual_dict=gg.read_sonar()
    gg.write_sonar(streaming_test_dict)
    if gg.read_sonar() != gg.read_sonar():
        raise ex.testError("issue with the batch updating")
    gg.write_sonar(streaming_actual_dict)

    # routing tests
    routing=gg.get_device_routing()
    for channel in routing:
        if channel["role"] not in gg.EQ_channels:
            continue
        for session in channel["audioSessions"]:
            if session["state"]=="active":
                pid=session["processId"]
                deviceId=channel["deviceId"]
                break
        else:
            continue
        break
    gg.put_audio_device_routing(deviceId,pid)

    # eq testing
    for test_channel in gg.EQ_channels:
        
        EQ_id = gg.read_EQs(channel=test_channel,flag="selected")["id"]

        EQ = gg.read_EQs(channel=test_channel,flag="selected")
        temp_EQ_name = EQ['name']
        temp_EQ = EQ['id']

        gg.put_active_EQ(gg.read_EQ_id(temp_EQ_name,channel=test_channel))
        if gg.read_EQs(channel=test_channel,flag="selected")["id"] != temp_EQ:
            raise ex.testError("could not set the EQs")

        gg.put_active_EQ(EQ_id)

        if EQ_id !=gg.read_EQs(channel=test_channel,flag="selected")["id"]:
            raise ex.testError("could not set the EQs")
    
    gg.put_streamer_mode(False)
    for test_channel in gg.channels:
        
        # classic volume control tests
        vol = gg.read_volume()[test_channel]["volume"]
        gg.put_volume(test_channel,0.5)
        if 0.5 != round(gg.read_volume()[test_channel]["volume"],2):
            raise ex.testError("issue with the volume being set")
        gg.put_volume(test_channel,f"r0.25")
        if .75 != round(gg.read_volume()[test_channel]["volume"],2):
            raise ex.testError("issue with the volume being set")
        gg.put_volume(test_channel,f"r-1")
        if 0 != round(gg.read_volume()[test_channel]["volume"],2):
            raise ex.testError("issue with the volume being set")
        gg.put_volume(test_channel,vol)
        if vol != round(gg.read_volume()[test_channel]["volume"],2):
            raise ex.testError("issue with the volume being set")
        
        # classic mute control test
        muted=gg.read_volume()[test_channel]["muted"]
        gg.put_mute(test_channel,not muted)
        if gg.read_volume()[test_channel]["muted"] == muted:
            raise ex.testError("issue with the mute being set")
        gg.put_mute(test_channel,"toggle")
        if gg.read_volume()[test_channel]["muted"] != muted:
            raise ex.testError("issue with the mute being set")
    
    gg.put_streamer_mode(True)
    for streamer_slider in gg.streamer_sliders:
        for test_channel in gg.channels:
            
            # stream volume control tests
            vol = gg.read_volume()[test_channel][streamer_slider]["volume"]
            gg.put_volume(test_channel,.5,streamer_slider)
            if .5 != round(gg.read_volume()[test_channel][streamer_slider]["volume"],2):
                raise ex.testError("issue with the volume being set")
            gg.put_volume(test_channel,f"r0.25",streamer_slider)
            if .75 != round(gg.read_volume()[test_channel][streamer_slider]["volume"],2):
                raise ex.testError("issue with the volume being set")
            gg.put_volume(test_channel,f"r-1",streamer_slider)
            if 0 != round(gg.read_volume()[test_channel][streamer_slider]["volume"],2):
                raise ex.testError("issue with the volume being set")
            gg.put_volume(test_channel,vol,streamer_slider)
            if vol != round(gg.read_volume()[test_channel][streamer_slider]["volume"],2):
                raise ex.testError("issue with the volume being set")
            
            # stream mute control test
            muted=gg.read_volume()[test_channel][streamer_slider]["muted"]
            gg.put_mute(test_channel,not muted,streamer_slider)
            if gg.read_volume()[test_channel][streamer_slider]["muted"] == muted:
                raise ex.testError("issue with the mute being set")
            gg.put_mute(test_channel,"toggle",streamer_slider)
            if gg.read_volume()[test_channel][streamer_slider]["muted"] != muted:
                raise ex.testError("issue with the mute being set")
            
        for test_channel in gg.EQ_channels:
        
            #stream redirection tests
            enable=gg.read_redirections()[streamer_slider][test_channel]
            gg.put_redirections_isEnabled(test_channel,not enable,streamer_slider)
            if gg.read_redirections()[streamer_slider][test_channel] == enable:
                raise ex.testError("issue with the redirection being set")
            gg.put_redirections_isEnabled(test_channel,"toggle",streamer_slider)
            if gg.read_redirections()[streamer_slider][test_channel] != enable:
                raise ex.testError("issue with the redirection being set")
            
    gg.put_streamer_mode(streamer_mode)
    
    # device function tests
    devices=gg.get_devices()
    device_id=None
    for device in devices["devices"]:
        if device["connected"]==1 and device["deviceTypeName"]=="Headset" and device["wireless_device_information"]:
            device_id=device["id"]
    if device_id:
        gg.get_device(device_id)
        gg.post_device_battery(device_id)
        gg.post_device_connection_status(device_id)
        gg.get_device_configurations(device_id)

    # random functions
    gg.get_scanned_games()
    gg.get_locale()
    gg.get_known_games()
    gg.get_chat_mix()
    gg.get_applications()
    gg.get_application_settings()

if __name__ == "__main__":
    test_all()
