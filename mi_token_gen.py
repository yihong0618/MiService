# mi_token_gen.py
import os
import asyncio
import hashlib
import logging
import json
import aiohttp
from miservice import MiAccount, MiTokenStore
from miservice.miaccount import get_random

_LOGGER = logging.getLogger(__name__)

# ==========================================
# 注入增强版半自动化验证代码 (含详细排查日志)
# ==========================================
async def custom_login(self, sid):
    if not self.token:
        self.token = {"deviceId": get_random(16).upper()}
    try:
        # 第一步：获取登录环境参数
        resp = await self._serviceLogin(f"serviceLogin?sid={sid}&_json=true")
        
        if resp.get("code") != 0:
            # 【新增：安全检查与异常诊断】
            if "qs" not in resp:
                print("\n❌ [第一步握手失败] 服务器未返回预期的参数 (qs)。")
                print(f"📄 服务器实际返回: {json.dumps(resp, ensure_ascii=False)}")
                
                if resp.get("code") == 87001:
                    print("\n⚠️ 诊断结果：触发了小米的【图形验证码 / 频繁请求风控】！")
                    print("💡 建议解决方案：")
                    print("   1. 暂缓几小时后再试，或")
                    print("   2. 更换你当前运行脚本的网络 IP（比如把电脑连到手机的 4G/5G 热点上再试一次）。")
                
                raise Exception(f"握手失败，缺少 qs 参数。详情: {resp}")

            # 组装密码等数据，发起第二步验证
            data = {
                "_json": "true",
                "qs": resp["qs"],
                "sid": resp["sid"],
                "_sign": resp["_sign"],
                "callback": resp["callback"],
                "user": self.username,
                "hash": hashlib.md5(self.password.encode()).hexdigest().upper(),
            }
            resp = await self._serviceLogin("serviceLoginAuth2", data)
            
            # 如果账号密码错误，这里也会报错，提前拦截打印
            if resp.get("code") != 0 and "notificationUrl" not in resp:
                 print(f"\n❌ [账号密码验证失败] 返回信息: {json.dumps(resp, ensure_ascii=False)}")
                 if resp.get("code") == 70016:
                     print("⚠️ 诊断结果：密码不正确！请检查 MI_PASS 是否填写正确。")
                 raise Exception(f"验证失败: {resp}")

        # --- 处理二次验证（notificationUrl）---
        if "userId" not in resp:
            notification_url = resp.get("notificationUrl")
            if not notification_url:
                raise Exception(f"无 userId 且无 notificationUrl: {resp}")

            print("\n" + "=" * 60)
            print("⚠️ 需要短信验证码验证")
            print("请按以下步骤操作：")
            print(f"1. 在浏览器中打开下方链接（可右键复制）：\n   {notification_url}\n")
            print("2. 点击「发送验证码」，输入手机/或邮箱收到的验证码并提交")
            print("3. 验证成功后，浏览器可能会跳401，没有关系，打开 https://account.xiaomi.com 完成登录")
            print("4. 打开开发者工具 (F12) → Application (存储) → Cookies")
            print("5. 找到 https://account.xiaomi.com 域下的以下两个值：")
            print("   - passToken (较长字符串)")
            print("   - userId (纯数字)\n")
            
            pass_token = input("请粘贴 passToken: ").strip()
            user_id = input("请粘贴 userId (纯数字): ").strip()

            if not pass_token or not user_id:
                raise Exception("未提供 passToken 或 userId，登录中止")

            self.token["passToken"] = pass_token
            self.token["userId"] = user_id

            print("正在使用提供的 token 重新验证...")
            resp = await self._serviceLogin("serviceLoginAuth2", data)
            if resp.get("code") != 0 or "userId" not in resp:
                raise Exception(f"二次验证后登录失败: {resp}")
            print("✅ 二次验证通过，继续获取 serviceToken...")
        # -------------------------------------------

        print(f"✅ Login successful for {self.username}")
        self.token["userId"] = resp["userId"]
        self.token["passToken"] = resp["passToken"]

        serviceToken = await self._securityTokenService(
            resp["location"], resp["nonce"], resp["ssecurity"]
        )
        self.token[sid] = (resp["ssecurity"], serviceToken)
        if self.token_store:
            self.token_store.save_token(self.token)
        return True

    except Exception as e:
        self.token = None
        if self.token_store:
            self.token_store.save_token()
        _LOGGER.exception("Exception on login %s: %s", self.username, e)
        return False

# 猴子补丁：替换掉原生库的 login 方法
MiAccount.login = custom_login

# ==========================================
# 执行生成逻辑
# ==========================================
async def main():
    # ⚠️ 请确保这里填入了你真实的账号和密码！
    MI_USER = os.getenv("MI_USER", "你的小米账户邮箱/手机号写在这里") 
    MI_PASS = os.getenv("MI_PASS", "你的真实密码写在这里") 
    
    TOKEN_PATH = os.path.join(os.path.expanduser("~"), ".mi.token")
    print(f"准备生成小米凭证到: {TOKEN_PATH}")
    
    store = MiTokenStore(TOKEN_PATH)
    
    async with aiohttp.ClientSession() as session:
        account = MiAccount(session, MI_USER, MI_PASS, store)
        success = await account.login("micoapi")
    
    if success:
        print(f"\n🎉 凭证获取成功！已保存至 {TOKEN_PATH}")
    else:
        print("\n❌ 凭证获取失败，请根据上方的日志排查问题。")

if __name__ == "__main__":
    asyncio.run(main())