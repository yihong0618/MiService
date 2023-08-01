from aiohttp import ClientSession
import asyncio
import logging
import json
import os
import sys
from pathlib import Path

from miservice import (
    MiAccount,
    MiNAService,
    MiIOService,
    miio_command,
    miio_command_help,
)


def usage():
    print("MiService %s - XiaoMi Cloud Service\n")
    print("Usage: The following variables must be set:")
    print("           export MI_USER=<Username>")
    print("           export MI_PASS=<Password>")
    print("           export MI_DID=<Device ID|Name>\n")
    print(miio_command_help(prefix="micli" + " "))


def find_device_id(hardware_data, mi_did):
    for h in hardware_data:
        if h.get("miotDID", "") == str(mi_did):
            return h.get("deviceID")
        else:
            continue
    else:
        raise Exception(f"we have no mi_did: please use `micli mina` to check")


async def main(args):
    try:
        async with ClientSession() as session:
            env = os.environ
            account = MiAccount(
                session,
                env.get("MI_USER"),
                env.get("MI_PASS"),
                os.path.join(str(Path.home()), ".mi.token"),
            )
            result = ""
            mina_service = MiNAService(account)
            if args.startswith("mina"):
                if len(args) > 4:
                    await mina_service.send_message(result, -1, args[4:])
            elif args.split(" ")[0].strip() in ["play", "pause"]:
                result = await mina_service.device_list()
                if not env.get("MI_DID"):
                    raise Exception("Please export MI_DID in your env")
                device_id = find_device_id(result, env.get("MI_DID", ""))
                args_list = args.split(" ")
                if len(args_list) == 1:
                    if args_list[0] == "pause":
                        await mina_service.player_pause(device_id)
                    else:
                        print("Please provice play url")
                    return
                # make device_id
                await mina_service.play_by_url(device_id, args_list[1])
                return
            else:
                service = MiIOService(account)
                result = await miio_command(
                    service, env.get("MI_DID"), args, sys.argv[0] + " "
                )
            if not isinstance(result, str):
                result = json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        result = e
    print(result)


def micli():
    argv = sys.argv
    argc = len(argv)
    if argc > 1 and argv[1].startswith("-v"):
        argi = 2
        index = int(argv[1][2]) if len(argv[1]) > 2 else 4
        level = [
            logging.NOTSET,
            logging.FATAL,
            logging.ERROR,
            logging.WARN,
            logging.INFO,
            logging.DEBUG,
        ][index]
    else:
        argi = 1
        level = logging.WARNING
    if argc > argi:
        if level != logging.NOTSET:
            _LOGGER = logging.getLogger("miservice")
            _LOGGER.setLevel(level)
            _LOGGER.addHandler(logging.StreamHandler())
        asyncio.run(main(" ".join(argv[argi:])))
    else:
        usage()


if __name__ == "__main__":
    micli()
