import requests, time, re


# 全部账户列表
account_list = []


# 当前时间戳
account_last = 0.0


# 更新用户列表到内存(每10分钟被动触发一次全部重载)
def update_account_list():
    global account_list
    global account_last
    if time.time() - account_last < 600:
        return
    print('重新下载用户列表')
    url = 'https://api-saas.lzhhjs.cn/apaas/openapi/form/smart/62fb0c62e4b0a9d4b9f53a10/query'
    headers = { 'Authorization': 'rv3lR5AnOsczhmd7rSx1uIyxMeBACe5X', 'Content-Type': 'application/json;charset=UTF-8' }
    response = requests.post(url=url, headers=headers, json={}) # json={'tel':mobile}
    response_dict = response.json()
    print('用户列表下载完毕')

    # 从 response_dict 提取使用的字段
    new_account_list = []
    for item in response_dict['result']:
        new_account_list.append({
            'id': item['userId'],
            'name': item['name'],
            'mobile': item['tel'],
            'avatar': item['userList']['userDetailList'][0]['headImg'],
        })
    account_list = new_account_list
    
    #account_list = response_dict['result']
    account_last = time.time()

# 获取用户
def queryAccount(id:str=None, mobile:str=None, name:str=None):
    update_account_list()
    user = None
    if id == '0' or mobile == '0':
        return {
            'id': '0',
            'name': '测试账户',
            'mobile': '00000000',
            'avatar': 'https://satori.love/api/avatar/93ac7001f4eeca1a793a72c3aa1d92ea.jpg',
        }
    for item in account_list:
        if mobile and item['mobile'] == mobile:
            user = item
        if id and item['id'] == id:
            user = item
        if name and item['name'] == name:
            user = item
    return user

# 查询用户列表(支持按名字模糊查询)
def queryAccountList(id:str=None, mobile:str=None, name:str=None):
    update_account_list()
    data = account_list
    if id is not None:
        data = [i for i in data if re.search(id, i['id'])]
    if mobile is not None:
        data = [i for i in data if re.search(mobile, i['mobile'])]
    if name is not None:
        data = [i for i in data if re.search(name, i['name'])]
    return data
