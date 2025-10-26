import json
import logging

from .miaccount import MiAccount, get_random

_LOGGER = logging.getLogger(__package__)

_USE_PLAY_MUSIC_API = [
    "LX04",
    "LX05",
    "L05B",
    "L05C",
    "L06",
    "L06A",
    "X08A",
    "X10A",
    "X08C",
    "M01",
    "X08E",
    "X8F",
]


class MiNAService:
    def __init__(self, account: MiAccount):
        self.account = account
        self.device2hardware = {}

    async def mina_request(self, uri, data=None):
        requestId = "app_ios_" + get_random(30)
        if data is not None:
            data["requestId"] = requestId
        else:
            uri += "&requestId=" + requestId
        headers = {
            "User-Agent": "MiHome/6.0.103 (com.xiaomi.mihome; build:6.0.103.1; iOS 14.4.0) Alamofire/6.0.103 MICO/iOSApp/appStore/6.0.103"
        }
        return await self.account.mi_request(
            "micoapi", "https://api2.mina.mi.com" + uri, data, headers
        )

    async def device_list(self, master=0):
        result = await self.mina_request("/admin/v2/device_list?master=" + str(master))
        return result.get("data") if result else None

    async def ubus_request(self, deviceId, method, path, message):
        message = json.dumps(message)
        result = await self.mina_request(
            "/remote/ubus",
            {"deviceId": deviceId, "message": message, "method": method, "path": path},
        )
        return result

    async def get_latest_ask(self, deviceId):
        from typing import TypedDict

        class result_message(TypedDict):
            class result_response(TypedDict):
                class response_answer(TypedDict):
                    domain: str
                    action: str
                    content: str
                    question: str

                answer: list[response_answer]

            request_id: str
            timestamp_ms: int
            response: result_response

        messages = []
        result = await self.ubus_request(deviceId, "nlp_result_get", "mibrain", {})
        if 0 != result["data"]["code"]:
            return messages
        result = json.loads(result["data"]["info"])["result"]
        for item in result:
            if not "nlp" in item:
                continue
            nlp = json.loads(item["nlp"])
            msg = result_message(
                request_id=nlp["meta"]["request_id"],
                timestamp_ms=int(nlp["meta"]["timestamp"]),
                response=result_message.result_response(answer=[]),
            )
            assert 1 == len(nlp["response"]["answer"])
            for answer in nlp["response"]["answer"]:
                msg["response"]["answer"].append(
                    result_message.result_response.response_answer(
                        domain=answer["domain"],
                        action=answer["action"],
                        content=answer["content"]["to_speak"],
                        question=answer["intention"]["query"],
                    )
                )
            messages.append(msg)
        return messages

    async def text_to_speech(self, deviceId, text):
        return await self.ubus_request(
            deviceId, "text_to_speech", "mibrain", {"text": text}
        )

    async def player_set_volume(self, deviceId, volume):
        return await self.ubus_request(
            deviceId,
            "player_set_volume",
            "mediaplayer",
            {"volume": volume, "media": "app_ios"},
        )

    async def player_pause(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_play_operation",
            "mediaplayer",
            {"action": "pause", "media": "app_ios"},
        )

    async def player_stop(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_play_operation",
            "mediaplayer",
            {"action": "stop", "media": "app_ios"},
        )

    async def player_play(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_play_operation",
            "mediaplayer",
            {"action": "play", "media": "app_ios"},
        )

    async def player_get_status(self, deviceId):
        return await self.ubus_request(
            deviceId,
            "player_get_play_status",
            "mediaplayer",
            {"media": "app_ios"},
        )

    async def player_set_loop(self, deviceId, type=1):
        return await self.ubus_request(
            deviceId,
            "player_set_loop",
            "mediaplayer",
            {"media": "common", "type": type},
        )

    async def play_by_url(self, deviceId, url, _type=2):
        if deviceId not in self.device2hardware:
            await self._init_devices()
        hardware = self.device2hardware[deviceId]
        if hardware in _USE_PLAY_MUSIC_API:
            return await self.play_by_music_url(deviceId, url, _type)
        else:
            return await self.ubus_request(
                deviceId,
                "player_play_url",
                "mediaplayer",
                {"url": url, "type": _type, "media": "app_ios"},
            )

    async def _init_devices(self):
        hardware_data = await self.device_list()
        for h in hardware_data:
            deviceId = h.get("deviceID", "")
            hardware = h.get("hardware", "")
            if deviceId and hardware:
                self.device2hardware[deviceId] = hardware

    async def play_by_music_url(
        self, deviceId, url, _type=2, audio_id="1582971365183456177", id="355454500"
    ):
        _LOGGER.debug("play_by_music_url url:%s, type:%d", url, _type)
        audio_type = ""
        if _type == 1:
            # If set to MUSIC, the light will be on
            audio_type = "MUSIC"
        music = {
            "payload": {
                "audio_type": audio_type,
                "audio_items": [
                    {
                        "item_id": {
                            "audio_id": audio_id,
                            "cp": {
                                "album_id": "-1",
                                "episode_index": 0,
                                "id": id,
                                "name": "xiaowei",
                            },
                        },
                        "stream": {"url": url},
                    }
                ],
                "list_params": {
                    "listId": "-1",
                    "loadmore_offset": 0,
                    "origin": "xiaowei",
                    "type": "MUSIC",
                },
            },
            "play_behavior": "REPLACE_ALL",
        }
        return await self.ubus_request(
            deviceId,
            "player_play_music",
            "mediaplayer",
            {"startaudioid": audio_id, "music": json.dumps(music)},
        )

    async def send_message(self, devices, devno, message, volume=None):  # -1/0/1...
        result = False
        for i in range(0, len(devices)):
            if (
                devno == -1
                or devno != i + 1
                or devices[i]["capabilities"].get("yunduantts")
            ):
                _LOGGER.debug(
                    "Send to devno=%d index=%d: %s", devno, i, message or volume
                )
                deviceId = devices[i]["deviceID"]
                result = (
                    True
                    if volume is None
                    else await self.player_set_volume(deviceId, volume)
                )
                if result and message:
                    result = await self.text_to_speech(deviceId, message)
                if not result:
                    _LOGGER.error("Send failed: %s", message or volume)
                if devno != -1 or not result:
                    break
        return result
