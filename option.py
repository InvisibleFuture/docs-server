import yaml
import os.path

class Option(object):

    # 初始化 option 到内存
    def __init__(self, dir):
        self.filename = dir + '/option.yaml'
        if os.path.isfile(self.filename):
            with open(self.filename, "r", encoding="utf-8") as f:
                self.option = yaml.load(f, Loader=yaml.FullLoader)
        else:
            self.option = {'private': [], 'admin': [], 'order':[], 'download':[], 'downloadCount':{}, 'viewsCount':{}}
            with open(self.filename, "w", encoding="utf-8") as f:
                yaml.dump(self.option, f)

    # 验证指定文件是否私有
    def isPrivate(self, name):
        return name in set(self.option['private'])

    # 设置私有(设为私有或公开)
    def setPrivate(self, name, value):
        if value:
            self.option['private'].append(name)
        elif name in self.option['private']:
            self.option['private'].remove(name)
        # 保存到文件(去重)
        self.option['private'] = list(set(self.option['private']))
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)

    # 是否有权限管理(权限向下传递)
    def isAdmin(self, id):
        return id in set(self.option['admin'])

    # 获取管理员列表(权限向下传递)
    def getAdmin(self):
        return self.option['admin']

    # 设置权限(授权用户或者取消授权)
    def setAdmin(self, id, value):
        if value:
            self.option['admin'].append(id)
        elif id in self.option['admin']:
            self.option['admin'].remove(id)
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)

    # 获取排序列表
    def getOrder(self):
        return self.option['order'] if 'order' in self.option.keys() else []

    # 设置排序列表
    def setOrder(self, data:list):
        self.option['order'] = data
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)

    # 是否禁止下载
    def isDownload(self, name):
        download = self.option['download'] if 'download' in self.option.keys() else []
        return name in set(download)

    # 设置禁止下载
    def setDownload(self, name, value):
        if 'download' not in self.option.keys():
            self.option['download'] = []
        if value:
            self.option['download'].append(name)
        else:
            self.option['download'].remove(name)
        self.option['download'] = list(set(self.option['download']))
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)

    # 下载计数器
    def getDownloadCount(self, name):
        if 'downloadCount' not in self.option.keys():
            self.option['downloadCount'] = {}
        if name not in self.option['downloadCount'].keys():
            self.option['downloadCount'][name] = 0
        return self.option['downloadCount'][name]

    # 下载计数器(每次增加1)
    def setDownloadCount(self, name):
        print(name)
        if 'downloadCount' not in self.option.keys():
            self.option['downloadCount'] = {}
        if name not in self.option['downloadCount'].keys():
            self.option['downloadCount'][name] = 0
        self.option['downloadCount'][name] += 1
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)

    # 查看计数器
    def getViewsCount(self, name):
        if 'viewsCount' not in self.option.keys():
            self.option['viewsCount'] = {}
        if name not in self.option['viewsCount'].keys():
            self.option['viewsCount'][name] = 0
        return self.option['viewsCount'][name]

    # 查看计数器(每次增加1)
    def setViewsCount(self, name):
        print('viewsCount:', name)
        if 'viewsCount' not in self.option.keys():
            self.option['viewsCount'] = {}
        if name not in self.option['viewsCount'].keys():
            self.option['viewsCount'][name] = 0
        self.option['viewsCount'][name] += 1
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)
