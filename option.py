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
            # TODO: 从上一级抄写 ADMIN?
            self.option = {'private': [], 'admin': []}
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
        # 保存到文件
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)


    # 是否有权限管理
    def isAdmin(self, name):
        return name in set(self.option['admin'])


    # 设置权限(授权用户或者取消授权)
    def setAdmin(self, name, value):
        if value:
            self.option['admin'].append(name)
        else:
            self.option['admin'].remove(name)
        with open(self.filename, "w", encoding="utf-8") as f:
            yaml.dump(self.option, f)

