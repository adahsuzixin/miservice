from fastapi import FastAPI, Depends
from aiohttp import ClientSession
import asyncio
import logging
import json
import os
from pathlib import Path

from miservice import (
    MiAccount,
    MiNAService,
    MiIOService,
    miio_command,
    miio_command_help,
)

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    # 读取环境变量
    env = os.environ
    MI_USER = env.get("MI_USER")
    MI_PASS = env.get("MI_PASS")
    MI_DID = env.get("MI_DID")

    # 创建全局客户端会话
    client_session = ClientSession()

    # 创建 MiAccount 实例
    account = MiAccount(
        client_session,
        MI_USER,
        MI_PASS,
        os.path.join(str(Path.home()), ".mi.token"),
    )

    # 在应用状态中存储会话和服务实例
    app.state.client_session = client_session
    app.state.account = account
    app.state.miio_service = MiIOService(account)
    app.state.mina_service = MiNAService(account)
    app.state.mi_did = MI_DID

@app.on_event("shutdown")
async def shutdown_event():
    # 关闭客户端会话
    await app.state.client_session.close()

# 依赖项：获取 miio_service 实例
async def get_miio_service():
    return app.state.miio_service

# 依赖项：获取 mina_service 实例
async def get_mina_service():
    return app.state.mina_service

# miio 命令接口
@app.post("/miio/command")
async def execute_miio_command(data: dict, miio_service: MiIOService = Depends(get_miio_service)):
    """
    请求数据应包含：
    - command: str
    - mi_did: str（可选，默认为环境变量中的 MI_DID）
    """
    MI_DID = data.get("mi_did") or app.state.mi_did
    command = data.get("command")

    if not command:
        return {"error": "需要提供命令"}
    if not MI_DID:
        return {"error": "需要提供设备 ID（mi_did）"}

    try:
        result = await miio_command(
            miio_service, MI_DID, command, ""
        )
        if not isinstance(result, str):
            result = json.dumps(result, indent=2, ensure_ascii=False)
    except Exception as e:
        result = str(e)
    return {"result": result}

# mina 命令接口
@app.post("/mina/command")
async def execute_mina_command(data: dict, mina_service: MiNAService = Depends(get_mina_service)):
    """
    请求数据应包含：
    - command: str
    """
    command = data.get("command")
    if not command:
        return {"error": "需要提供命令"}

    try:
        device_list = await mina_service.device_list()
        if len(command) > 4:
            result = await mina_service.send_message(device_list, -1, command[4:])
        else:
            result = "命令长度太短"
    except Exception as e:
        result = str(e)
    return {"result": result}

# 主函数，运行应用程序
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
