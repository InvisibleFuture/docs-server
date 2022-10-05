# -*- coding:utf-8 -*-
import time, os, shutil, uvicorn, zipfile, ctypes, platform
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

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

    ## 静态文件服务(未鉴权)
    #elif request.url.path.startswith('/static/'):
    #    return FileResponse(request.url.path[1:])
    ## 静态文件服务
    #elif request.url.path.startswith('/favicon.ico'):
    #    return Response(status_code=404, content='404 Not Found')
    #    #return FileResponse('static/favicon.ico')

    print('--------------------------------------------')
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

if __name__ == "__main__":
    uvicorn.run("main:app", port=2333, reload=True, workers=1)
