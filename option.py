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
            self.option = {'private': [], 'admin': [], 'order':[]}
            with open(self.filename, "w", encoding="utf-8") as f:
                yaml.dump(self.option, f)

    # 验证指定文件是否私有
    def isPrivate(self, name):
        return name in set(self.option['private'])

    # 设置私有(设为私有或公开)
    def setPrivate(self, name, value):
        if value:
            self.option['private'].append(name)
        else:
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
        else:
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
