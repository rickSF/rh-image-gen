#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RunningHub 工作流调用脚本 - Plus模式
支持传入3张参考图，保持角色场景一致性
"""

import os
import sys
import json
import time
import requests
from pathlib import Path

# 配置
API_HOST = "www.runninghub.cn"
WORKFLOW_ID = "2037737258933030913"  # 新工作流（支持3图+尺寸设置）

# 节点映射
NODE_PROMPT = "21"       # 正面提示词
NODE_NEGATIVE = "43"     # 负面提示词
NODE_REF_NODES = {       # 参考图节点映射 (LoadImage)
    1: "15",             # 参考图1 (image1)
    2: "44",             # 参考图2 (image2)
    3: "47",             # 参考图3 (image3)
}
NODE_WIDTH = "49"        # 图片宽度设置
NODE_HEIGHT = "48"       # 图片高度设置
NODE_OUTPUT = "19"       # 输出节点 (SaveImage)

# 固定负面提示词
NEGATIVE_PROMPT = (
    "worst quality, low quality, normal quality, lowres, blurry, out of focus, "
    "grainy, noisy, ugly, deformed, disfigured, bad anatomy, text, watermark, "
    "signature, cartoon, 3d render, anime, illustration, painting, sketch, "
    "monochrome, grayscale, overexposed, underexposed"
)


def get_api_key():
    """从环境变量或配置文件获取API Key"""
    api_key = os.environ.get("RUNNINGHUB_API_KEY")
    if api_key:
        return api_key
    
    # 尝试读取配置文件
    config_path = Path.home() / ".openclaw" / "config" / "runninghub.json"
    if config_path.exists():
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
            return config.get("api_key")
    
    raise ValueError("未找到 RUNNINGHUB_API_KEY，请设置环境变量或配置文件")


def upload_file(api_key: str, file_path: str) -> str:
    """
    上传文件到 RunningHub
    返回: api/xxx.png 格式的文件路径
    """
    url = f"https://{API_HOST}/task/openapi/upload"
    
    print(f"   正在上传: {os.path.basename(file_path)} ({os.path.getsize(file_path)} bytes)")
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {'apiKey': api_key, 'fileType': 'input'}
        response = requests.post(url, files=files, data=data)
    
    # 调试: 打印原始响应
    print(f"   HTTP状态: {response.status_code}")
    if response.status_code != 200:
        print(f"   错误响应: {response.text[:200]}")
        raise RuntimeError(f"上传HTTP错误: {response.status_code}")
    
    try:
        result = response.json()
    except json.JSONDecodeError as e:
        print(f"   JSON解析错误: {e}")
        print(f"   原始响应: {response.text[:500]}")
        raise RuntimeError(f"上传返回非JSON: {response.text[:200]}")
    
    if result.get("code") != 0:
        raise RuntimeError(f"上传失败: {result.get('msg')}")
    
    return result["data"]["fileName"]


def submit_task(api_key: str, workflow_id: str, node_info_list: list) -> str:
    """
    提交任务到 RunningHub
    返回: task_id
    """
    url = f"https://{API_HOST}/task/openapi/create"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "apiKey": api_key,
        "workflowId": workflow_id,
        "nodeInfoList": node_info_list
    }
    
    response = requests.post(url, headers=headers, json=payload)
    result = response.json()
    
    if result.get("code") != 0:
        raise RuntimeError(f"提交任务失败: {result.get('msg')}")
    
    return result["data"]["taskId"]


def query_task_outputs(api_key: str, task_id: str, timeout: int = 300) -> list:
    """
    轮询查询任务结果
    返回: 输出文件URL列表
    """
    url = f"https://{API_HOST}/task/openapi/outputs"
    headers = {'Content-Type': 'application/json'}
    payload = {"apiKey": api_key, "taskId": task_id}
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        
        if result.get("code") != 0:
            msg = result.get('msg', '')
            # APIKEY_TASK_IS_RUNNING 是正常状态，继续轮询
            if 'TASK_IS_RUNNING' in msg:
                print("⏳ 任务运行中...")
                time.sleep(5)
                continue
            raise RuntimeError(f"查询失败: {msg}")
        
        data = result.get("data", {})
        
        # 处理不同响应格式
        if isinstance(data, list):
            # 任务完成，data是输出列表
            return [item.get("fileUrl") for item in data if item.get("fileUrl")]
        
        # 任务进行中，data是状态字典
        task_status = data.get("taskStatus")
        
        if task_status == 2:  # 成功
            outputs = data.get("outputs", [])
            return [item.get("fileUrl") for item in outputs if item.get("fileUrl")]
        elif task_status == 3:  # 失败
            error_msg = data.get("errorMsg", "未知错误")
            raise RuntimeError(f"任务失败: {error_msg}")
        
        print("⏳ 任务运行中...")
        time.sleep(5)
    
    raise TimeoutError("任务超时")


def generate_image(
    shot: str,
    prompt: str,
    ref1: str = None,
    ref2: str = None,
    ref3: str = None,
    width: int = 1080,
    height: int = 1920,
    output_dir: str = "./06_images"
) -> str:
    """
    生成单张分镜图 (Plus模式)
    
    Args:
        shot: 分镜编号，如 "001"
        prompt: 正面提示词
        ref1: 参考图1路径（角色）
        ref2: 参考图2路径（场景）
        ref3: 参考图3路径（风格）
        width: 输出图片宽度（默认1080）
        height: 输出图片高度（默认1920）
        output_dir: 输出目录
    
    Returns:
        输出文件路径
    """
    api_key = get_api_key()
    
    # 构建 node_info_list
    node_info_list = [
        {"nodeId": NODE_PROMPT, "fieldName": "text", "fieldValue": prompt},
        {"nodeId": NODE_NEGATIVE, "fieldName": "text", "fieldValue": NEGATIVE_PROMPT},
        {"nodeId": NODE_WIDTH, "fieldName": "value", "fieldValue": str(width)},
        {"nodeId": NODE_HEIGHT, "fieldName": "value", "fieldValue": str(height)},
    ]
    
    # 新工作流支持3张参考图，分别上传到节点15/44/47
    refs = [(1, ref1), (2, ref2), (3, ref3)]
    for idx, ref_path in refs:
        if ref_path and os.path.exists(ref_path):
            print(f"📤 上传参考图{idx}: {ref_path}")
            ref_url = upload_file(api_key, ref_path)
            node_id = NODE_REF_NODES.get(idx)
            if node_id:
                node_info_list.append({
                    "nodeId": node_id,
                    "fieldName": "image",
                    "fieldValue": ref_url
                })
                print(f"   已添加到节点 {node_id} (image{idx})")
            else:
                print(f"   ⚠️  节点{idx}未配置，跳过")
    
    # 提交任务
    print(f"🚀 提交任务生成 shot_{shot}...")
    print(f"   尺寸: {width}x{height}")
    task_id = submit_task(api_key, WORKFLOW_ID, node_info_list)
    print(f"📝 Task ID: {task_id}")
    
    # 查询结果
    print("⏳ 等待生成完成...")
    file_urls = query_task_outputs(api_key, task_id)
    
    if not file_urls:
        raise RuntimeError("未获取到输出图片")
    
    # 下载图片
    output_path = Path(output_dir) / f"shot_{shot}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"⬇️  下载图片到: {output_path}")
    img_response = requests.get(file_urls[0])
    with open(output_path, "wb") as f:
        f.write(img_response.content)
    
    print(f"✅ 生成完成: {output_path}")
    return str(output_path)


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="RunningHub 图片生成工具 - Plus模式")
    subparsers = parser.add_subparsers(dest="command", help="子命令")
    
    # workflow generate 子命令
    gen_parser = subparsers.add_parser("workflow", help="工作流模式")
    gen_subparsers = gen_parser.add_subparsers(dest="workflow_cmd")
    
    generate_parser = gen_subparsers.add_parser("generate", help="生成单张图片(Plus模式)")
    generate_parser.add_argument("--shot", required=True, help="分镜编号")
    generate_parser.add_argument("--prompt", required=True, help="正面提示词")
    generate_parser.add_argument("--ref1", help="参考图1路径（角色）")
    generate_parser.add_argument("--ref2", help="参考图2路径（场景）")
    generate_parser.add_argument("--ref3", help="参考图3路径（风格）")
    generate_parser.add_argument("--width", type=int, default=1080, help="输出宽度(默认1080)")
    generate_parser.add_argument("--height", type=int, default=1920, help="输出高度(默认1920)")
    generate_parser.add_argument("--output-dir", default="./06_images", help="输出目录")
    
    args = parser.parse_args()
    
    if args.command == "workflow" and args.workflow_cmd == "generate":
        generate_image(
            shot=args.shot,
            prompt=args.prompt,
            ref1=args.ref1,
            ref2=args.ref2,
            ref3=args.ref3,
            width=args.width,
            height=args.height,
            output_dir=args.output_dir
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
