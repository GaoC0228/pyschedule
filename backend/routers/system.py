from fastapi import APIRouter, HTTPException
import httpx
import asyncio

router = APIRouter(prefix="/api/system", tags=["系统信息"])


@router.get("/public-ip")
async def get_public_ip():
    """
    获取服务器公网IP信息
    包括IP地址、地理位置、ISP等信息
    """
    try:
        # 使用多个API服务，提高成功率
        apis = [
            {
                "url": "https://api.ipify.org?format=json",
                "parse": lambda data: {"ip": data.get("ip")}
            },
            {
                "url": "http://ip-api.com/json/",
                "parse": lambda data: {
                    "ip": data.get("query"),
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "region": data.get("regionName"),
                    "city": data.get("city"),
                    "isp": data.get("isp"),
                    "org": data.get("org"),
                    "timezone": data.get("timezone"),
                    "lat": data.get("lat"),
                    "lon": data.get("lon")
                }
            },
            {
                "url": "https://ipapi.co/json/",
                "parse": lambda data: {
                    "ip": data.get("ip"),
                    "country": data.get("country_name"),
                    "country_code": data.get("country_code"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "isp": data.get("org"),
                    "timezone": data.get("timezone"),
                    "lat": data.get("latitude"),
                    "lon": data.get("longitude")
                }
            }
        ]
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 尝试第一个API（只获取IP）
            try:
                response = await client.get(apis[0]["url"])
                if response.status_code == 200:
                    basic_info = apis[0]["parse"](response.json())
                    
                    # 尝试获取详细信息
                    for api in apis[1:]:
                        try:
                            detail_response = await client.get(api["url"])
                            if detail_response.status_code == 200:
                                detailed_info = api["parse"](detail_response.json())
                                # 合并信息
                                return {
                                    "success": True,
                                    "data": {**basic_info, **detailed_info}
                                }
                        except Exception:
                            continue
                    
                    # 如果详细信息获取失败，返回基本信息
                    return {
                        "success": True,
                        "data": basic_info
                    }
            except Exception as e:
                # 如果第一个API失败，尝试其他API
                for api in apis[1:]:
                    try:
                        response = await client.get(api["url"])
                        if response.status_code == 200:
                            info = api["parse"](response.json())
                            return {
                                "success": True,
                                "data": info
                            }
                    except Exception:
                        continue
                
                raise Exception("所有IP查询API均失败")
                
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取公网IP失败: {str(e)}"
        )


@router.get("/server-info")
async def get_server_info():
    """
    获取服务器基本信息
    """
    import platform
    import psutil
    from datetime import datetime
    
    try:
        # 获取系统信息
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # 获取启动时间
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        
        return {
            "success": True,
            "data": {
                "os": platform.system(),
                "os_version": platform.version(),
                "python_version": platform.python_version(),
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_total": memory.total,
                "memory_used": memory.used,
                "disk_percent": disk.percent,
                "disk_total": disk.total,
                "disk_used": disk.used,
                "boot_time": boot_time.isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取服务器信息失败: {str(e)}"
        )
