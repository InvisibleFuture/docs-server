# -*- coding:utf-8 -*-
from email import header
import time, os, shutil, uvicorn, zipfile, ctypes, platform, uuid, requests
from fastapi import FastAPI, Request, Response, HTTPException, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from pydantic import BaseModel
from auth import Auth
import random, string

# 检查是否有静态文件夹,没有则并创建
for item in ['static', 'templates', 'tmps']:
    if not os.path.exists(item):
        os.mkdir(item)

# 创建FastAPI实例
app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# HOME(声明返回HTML)
@app.get("/", response_class=HTMLResponse)
def read_item(request: Request):
    print(request.path_params)
    return 'HELLO WORLD !'

session_list = {}

class Signin(BaseModel):
    mobile: str
    code: str


# 获取环境变量值
APP_ID="cli_a3a8a7faa4b8d00b"
APP_SECRET="IoyMD1BmClcX4BNbEwF2BdDNIS2lkJYb"
FEISHU_HOST="https://open.feishu.cn"


# 用获取的环境变量初始化免登流程类Auth
auth = Auth(FEISHU_HOST, APP_ID, APP_SECRET)


# 获取 user_access_token
def get_user_access_token(code):
    url = "https://open.feishu.cn/open-apis/auth/v3/app_access_token/internal"
    # "app_id" 和 "app_secret" 位于HTTP请求的请求体
    req_body = {"app_id": APP_ID, "app_secret": APP_SECRET}
    response = requests.post(url, req_body)
    if response.status_code != 200:
        raise response.raise_for_status()
    response_dict = response.json()
    code = response_dict.get("code", -1)
    if code != 0:
        raise HTTPException(status_code=code, detail=response_dict.get("msg"))
    return response_dict.get("app_access_token")


# 获取用户信息
def get_user_info(user_access_token):
    url = "https://open.feishu.cn/open-apis/authen/v1/user_info"
    headers = {
        "Authorization": "Bearer " + user_access_token,
        "Content-Type": "application/json",
    }
    response = requests.get(url=url, headers=headers)
    response_dict = response.json()
    print(response_dict)
    return response_dict.get("data")


# 通过手机号获取用户信息
def get_user_info_mobile(mobile):
    url = 'https://api-saas.lzhhjs.cn/apaas/openapi/form/smart/62fb0c62e4b0a9d4b9f53a10/query'
    headers = { 'Authorization': 'rv3lR5AnOsczhmd7rSx1uIyxMeBACe5X', 'Content-Type': 'application/json;charset=UTF-8' }
    response = requests.post(url=url, headers=headers, json={'tel':mobile})
    response_dict = response.json()
    # print(response_dict['result'])
    # 取 tel 等于 mobile 的
    user = None
    for item in response_dict['result']:
        if item['tel'] == mobile:
            user = item
            break
    return user


# 飞书登录
@app.get("/feishu/callback")
def feishu_callback(code:str, response:Response):
    auth.authorize_user_access_token(code)
    item = auth.get_user_info()
    print('user_info:', item)

    # 从平台获取用户信息
    user_info = get_user_info_mobile(item.mobile)
    print('user_info:', user_info)
    if user_info is None:
        raise HTTPException(status_code=401, detail='手机号未注册')

    # 生成 session
    session = str(uuid.uuid4())
    session_list[session] = {item.mobile}
    response.set_cookie(key="session", value=session)
    return {"msg": "登录成功", "userinfo": user_info}


@app.get("/feishu/get_appid")
def feishu_appid():
    return { "appid": "cli_a3a8a7faa4b8d00b" }

# 获取账户信息
@app.get("/sign", summary="获取资料")
def profile(session:str=Cookie(None)):
    mobile = session_list.get(session)
    print("session:", session)
    print("mobile:", mobile)
    if mobile is None:
        return {
            'online': False,
            'admin': False,
            'name':'Lemon',
            'email':'Lemon@disp.com',
            'avatar':'https://avatars.githubusercontent.com/u/6184465?v=4',
        }
    return {
        'online': True,
        'admin': True,
        'name':'Lemon',
        'email':'Lemon@disp.com',
        'avatar':'https://avatars.githubusercontent.com/u/6184465?v=4',
    }

code_list = {}

# 发送短信验证码
@app.post("/sign/sendcode", summary="发送短信验证码")
def send_tpl_sms(mobile:str):
    # 先判断手机号是否存在(从平台获取)
    user = get_user_info_mobile(mobile)
    if user is None:
        return { 'code': 400, 'message': '手机号不存在' }
    
    # 生成随机验证码(6位数)
    code = ''.join(random.sample(string.digits, 6))

    # 清理过期验证码(5分钟)
    for key in code_list.keys():
        if time.time() - code_list[key]['time'] > 300:
            code_list.pop(key)

    # 存储验证码
    code_list[mobile] = {
        'code': code,
        'time': time.time()
    }

    # 发送短信验证码
    url = 'https://sms.yunpian.com/v2/sms/tpl_single_send.json'
    headers = { "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8" }
    data = 'apikey=870bb619c2d1ebc3519789a845ba5dca&mobile='+mobile+'&tpl_id=5227126&tpl_value=%2523code%2523%3D'+code
    response = requests.post(url=url, headers=headers, data=data)
    response_dict = response.json()
    print(response_dict)
    return response_dict


# 登录账户(默认数据从平台获取)
@app.post("/sign", summary="登录账户", status_code=200)
def signin(item:Signin, response:Response):
    user_info = get_user_info_mobile(item.mobile)
    print('user_info:', user_info)
    
    # 判断验证码是否正确, 判断验证码是否过期(5分钟)
    code = code_list.get(item.mobile)
    if (code is None) or (time.time() - code['time'] > 300):
        return { 'code': 400, 'message': '验证码已过期' }
    if code['code'] != item.code:
        return { 'code': 400, 'message': '验证码错误' }

    # 生成 session
    session = str(uuid.uuid4())
    session_list[session] = {item.mobile}
    response.set_cookie(key="session", value=session)
    return {"msg": "登录成功", "userinfo": user_info}


# 退出登录
@app.delete("/sign", summary="退出登录")
def signout(response=Response):
    response.delete_cookie(key="session")
    return {"code": 200, "msg": "已退出"}


# 模糊检索文件
@app.get("/search", summary="模糊检索")
def search_files(name: str):
    # 从 static 文件夹遍历搜索文件或文件夹名中包含搜索词name的文件或文件夹
    result = []
    for root, dirs, files in os.walk('static'):
        for each in files:
            if name in each:
                result.append({'type':'file', 'path':os.path.join(root, each)})
        for each in dirs:
            if name in each:
                result.append({'type':'dir', 'path':os.path.join(root, each)})
    return result


def count(path, count: int = 0):
    for root, dirs, files in os.walk(path):
        for each in files:
            count += 1
    return count


def size(path):
    m = 0
    lt = os.listdir(path)  # 展开目录下的信息
    for i in lt:  # 遍历目录下信息
        if os.path.isdir(os.path.join(path, i)):  # 判断是否为目录
            m = m + size(os.path.join(path, i))  # 调用递归，求得目录大小
        else:
            m = m + os.path.getsize(os.path.join(path, i))  # 若不是目录，加上该文件的大小
    return m  # 返回目录总大小

def get_free_space(folder):
    """ Return folder/drive
     space (in bytes)
    """
    if platform.system() == 'Windows':
        free_bytes = ctypes.c_ulonglong(0)
        ctypes.windll.kernel32.GetDiskFreeSpaceExW(ctypes.c_wchar_p(folder), None, None, ctypes.pointer(free_bytes))
        return free_bytes.value
    else:
        st = os.statvfs(folder)
        return st.f_bavail * st.f_frsize

def get_zip_file(input_path, result):
    """
    对目录进行深度优先遍历
    :param input_path:
    :param result:
    :return:
    """
    files = os.listdir(input_path)
    for file in files:
        if os.path.isdir(input_path + '/' + file):
            get_zip_file(input_path + '/' + file, result)
        else:
            result.append(input_path + '/' + file)

def zip_file_path(input_path, output_path, output_name):
    """
    压缩文件，相对路径
    :param input_path: 压缩的文件夹路径
    :param output_path: 解压（输出）的路径
    :param output_name: 压缩包名称
    :return:
    """
    f = zipfile.ZipFile(output_path + '/' + output_name, 'w', zipfile.ZIP_DEFLATED)
    filelists = []
    get_zip_file(input_path, filelists)
    for file in filelists:
        f.write(file)
    f.close()
    return output_path + r"/" + output_name


# 中间件, 文件和文件夹
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    print('中间件', request.url.path)

    # 压缩文件夹
    if request.url.path.startswith('/zip/'):
        paths = request.url.path.split('/')
        dir = 'static/' + '/'.join(paths[2:])
        print('path:', paths)
        # 处理 GET 请求
        if request.method == 'GET':
            # 判断文件夹是否存在(返回文件夹详情)
            if os.path.isdir(dir):
                # 将指定的目录压缩为 zip, 并提供下载
                print(paths[-1])
                path = zip_file_path(dir, 'tmps', paths[-1]+'.zip')
                return FileResponse(path)
        return Response(status_code=400, content='400 操作禁止')

    # 静态文件夹
    if request.url.path.startswith('/api/'):
        path = request.url.path.split('/')
        dir = 'static/' + '/'.join(path[2:])
        print('path:', path)
        # 处理 GET 请求
        if request.method == 'GET':
            # 判断文件夹是否存在(返回文件夹详情)
            if os.path.isdir(dir):
                data = []
                for i in os.listdir(dir):
                    item = dir + '/' + i
                    if os.path.isdir(item):
                        data.append({'name': i, 'type': 'dir', 'size': size(item), 'count': count(item)})
                    else:
                        data.append({'name': i, 'type': 'file', 'size': os.path.getsize(item)})
                # 分别统计文件夹下各类型文件大小和数量(视频, 图片 其它) (递归 item 下的所有子目录)
                video_size, image_size, other_size = 0, 0, 0
                video_count, image_count, other_count = 0, 0, 0
                for root, dirs, files in os.walk(dir):
                    for j in files:
                        if j.endswith(('.mp4', '.mkv', '.avi', '.rmvb')):
                            video_count+=1
                            video_size += os.path.getsize(root + '/' + j)
                        elif j.endswith(('.jpg', '.png', '.gif', '.jpeg')):
                            image_count+=1
                            image_size += os.path.getsize(root + '/' + j)
                        else:
                            other_count+=1
                            other_size += os.path.getsize(root + '/' + j)
                return JSONResponse({
                    'name': path[-1],
                    'free': get_free_space(dir),
                    'size': size(dir),
                    'count': count(dir),
                    'type': 'dir',
                    'list': data,
                    'sizes':{
                        'videos': video_size,
                        'images': image_size,
                        'document': other_size,
                    },
                    'counts':{
                        'videos': video_count,
                        'images': image_count,
                        'document': other_count,
                    },
                })
            # 判断文件是否存在(提供文件下载)
            elif os.path.isfile(dir):
                print('文件')
                return FileResponse(dir)
            else:
                print('不存在')
                return Response(status_code=404, content='404 Not Found')
        # 处理PUT请求(创建文件夹)
        elif request.method == 'PUT':
            if not os.path.exists(dir):
                os.mkdir(dir)
            return JSONResponse({'status': True, 'name': path[-1]})
        # 处理PATCH请求(修改文件夹)
        elif request.method == 'PATCH':
            print('PATCH', request.query_params)
            new_name = request.query_params.get('name')
            new_dir = 'static/' + '/'.join(path[2:-1]) + '/' + new_name
            if os.path.exists(dir) and not os.path.exists(new_dir):
                os.rename(dir, new_dir)
                return JSONResponse({'status': True, 'name': new_name})
            return Response(status_code=400, content='文件名已存在')
        # 处理POST请求(批量上传文件)
        elif request.method == 'POST':
            form = await request.form()
            file = form.getlist('file')
            for i in file:
                print(dir + '/' + i.filename)
                with open(dir + '/' + i.filename, 'wb') as f:
                    f.write(i.file.read())
            return JSONResponse({'status': True, 'name': path[-1]})
        # 处理DELETE请求(删除文件夹或文件)
        elif request.method == 'DELETE':
            if os.path.exists(dir):
                if os.path.isdir(dir):
                    shutil.rmtree(dir)
                else:
                    os.remove(dir)
            return JSONResponse({'status': True, 'name': path[-1]})

    # 中间件预处理完毕执行主体请求
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", port=2333, reload=True, workers=1)
