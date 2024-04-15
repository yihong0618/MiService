# MiService
XiaoMi Cloud Service for mi.com 
This is a fork from https://github.com/Yonsm/MiService made some change for xiaogpt

# 如果有无法登陆的问题请参考置顶 issue, 如果还是不行请留言

## 本 fork 新增功能

## -> 播放音乐

```
micli play ${mp3_url} 
micli pause
```

## -> 播放音乐高级版

```
micli loop ${mp3_url}  # 循环播放
micli pause

# make a playlist name test.txt
cat test.txt
# http://192.168.6.212:8000/public/s4.mp3
# http://192.168.6.212:8000/public/s1.mp3
# http://192.168.6.212:8000/public/s2.mp3
# http://193.168.6.212:8000/public/s3.mp3

micli play_list test.txt # play the list
```

## -> 播放 suno.ai trending

```
micli suno 
```

## -> 播放 suno.ai trending random

```
micli suno_random
```

## -> 查看硬件信息

```
micli mina
```

## Install
```
pip3 install -U miservice_fork
or 
pip3 install .
```

## Library
```
MiService：XiaoMi Cloud Service
  |
  |-- MiAccount：Account Srvice
  |-- MiBaseService：(TODO if needed)
  |     |
  |     |-- MiIOService：MiIO Service (sid=xiaomiio)
  |     |     |
  |     |     |-- MIoT_xxx：MIoT Service, Based on MiIO
  |     |
  |     |-- MiNAService：MiAI Service (sid=micoapi)
  |     |
  |     |-- MiAPIService：(TODO)
  |-- MiIOCommand：MiIO Command Style Interface
```

## Command Line
```
Usage: The following variables must be set:
           export MI_USER=<Username>
           export MI_PASS=<Password>
           export MI_DID=<Device ID|Name>

Get Props: micli <siid[-piid]>[,...]
           micli 1,1-2,1-3,1-4,2-1,2-2,3
Set Props: micli <siid[-piid]=[#]value>[,...]
           micli 2=#60,2-2=#false,3=test
Do Action: micli <siid[-piid]> <arg1|#NA> [...] 
           micli 2 #NA
           micli 5 Hello
           micli 5-4 Hello #1

Call MIoT: micli <cmd=prop/get|/prop/set|action> <params>
           micli action '{"did":"267090026","siid":5,"aiid":1,"in":["Hello"]}'

Call MiIO: micli /<uri> <data>
           micli /home/device_list '{"getVirtualModel":false,"getHuamiDevices":1}'

Devs List: micli list [name=full|name_keyword] [getVirtualModel=false|true] [getHuamiDevices=0|1]
           micli list Light true 0

MIoT Spec: micli spec [model_keyword|type_urn] [format=text|python|json]
           micli spec
           micli spec speaker
           micli spec xiaomi.wifispeaker.lx04
           micli spec urn:miot-spec-v2:device:speaker:0000A015:xiaomi-lx04:1

MIoT Decode: micli decode <ssecurity> <nonce> <data> [gzip]
```

## 套路，例子：

`请在 Mac OS 或 Linux 下执行，Windows 下要支持也应该容易但可能需要修改？`

### 1. 先设置账号

```
export MI_USER=<Username>
export MI_PASS=<Password>
```

### 2. 查询自己的设备

```
micli list
```
可以显示自己账号下的设备列表，包含名称、类型、DID、Token 等信息。

### 3. 设置 DID

为了后续操作，请设置 Device ID（来自上面这条命令的结果）。

```
export MI_DID=<Device ID|Name>
```

### 4. 查询设备的接口文档

查询设备的 MIoT 接口能力描述：
```
micli spec xiaomi.wifispeaker.lx04
```
其中分为属性获取、属性设置、动作调用三种描述。

### 5. 查询音量属性

```
micli.py 2-1
```
其中 `2` 为 `siid`，`1` 为 `piid`（如果是 `1` 则可以省略），可从 spec 接口描述中查得。

### 6. 设置音量属性

```
micli.py 2=#60
```
`siid` 和 `piid` 规则同属性查询命令。注意 `#` 号的意思是整数类型，如果不带则默认是文本字符串类型，要根据接口描述文档来确定类型。

### 7. 动作调用：TTS 播报和执行文本

以下命令执行后小爱音箱会播报“您好”：
```
micli.py 5 您好
```
其中，5 为 `siid`，此处省略了 `1` 的 `aiid`。

以下命令执行后相当于直接对对音箱说“小爱同学，查询天气”是一个效果：
```
micli.py 5-4 查询天气 #1
```

其中 `#1` 表示设备语音回应，如果要执行默默关灯（不要音箱回应），可以如下：
```
micli.py 5-4 关灯 #0
```

## 8. 播放音乐

```
micli play ${mp3_url} 
micli pause
```

## 9. 播放音乐高级版

```
micli loop ${mp3_url}  # 循环播放
micli pause

# make a playlist name test.txt
cat test.txt
# http://192.168.6.212:8000/public/s4.mp3
# http://192.168.6.212:8000/public/s1.mp3
# http://192.168.6.212:8000/public/s2.mp3
# http://193.168.6.212:8000/public/s3.mp3

micli play_list test.txt # play the list
```

### 10. 其它应用

在扩展插件中使用，比如，参考 [ZhiMsg 小爱同学 TTS 播报/执行插件](https://github.com/Yonsm/ZhiMsg)
