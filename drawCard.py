import time
import requests
import json
import sys
from bs4 import BeautifulSoup
from prettytable import PrettyTable
from skimage import io


def main():
    ts=0
    if(len(sys.argv)>1):
        arg=int(sys.argv[1])
        #print(arg)
        if(arg>5000):
            ts=int(arg/5000)
        elif(arg>0):
            ts=arg
        else:
            ts=0
    print("For MiniMaX use! 帐密放在cc98.json")
    f = open('cc98.json')
    cc98User = json.load(f)
    #ac=input("用户名:")
    #pw=input("密码:")
    if(ts==0):
        ts=int(input("抽卡次数:"))
    else:
        print("要花费的魔力值：%d，抽卡次数：%d"%(arg,ts))
    draw_card_v3_1(username=cc98User["username"], password=cc98User["password"], times=ts, action=2)
    #print(ts)

def draw_card_v3_1(username: '用户名', 
                 password: '密码', 
                 times: '抽卡次数', 
                 action: '1表示抽一次，2表示抽十一次'=1) -> None:
                 #if_destroy: '是否自动分解重复卡牌'=True) -> None:
    
    least_wealth = 500 if action == 1 else 5000
    
    # 1. 登录CC98登录中心
    s = requests.session()
    r = s.get('https://openid.cc98.org/Account/LogOn')
    bs = BeautifulSoup(r.text, 'html.parser')

    data = {
      'UserName': username,
      'Password': password,
      'ValidTime': '',
      '__RequestVerificationToken': bs.find('input', {'name':'__RequestVerificationToken'})['value']
    }

    r = s.post('https://openid.cc98.org/Account/LogOn', 
               headers={'content-type': 'application/x-www-form-urlencoded'}, 
               data=data)

    r = s.get('https://card.cc98.org/Account/LogOn')

    # 2. 授权给CC98抽卡中心
    r = s.get(r.url)
    bs = BeautifulSoup(r.text, 'html.parser')
    data = {
        'Scopes': 'openid',
        'IsConsent': 'true',
        'RememberConsent': 'false', 
        '__RequestVerificationToken': bs.find('input', {'name':'__RequestVerificationToken'})['value']
    }
    r = s.post(r.url, 
               headers={'content-type': 'application/x-www-form-urlencoded'}, 
               data=data)

    bs = BeautifulSoup(r.text, 'html.parser')
    data = {
        'code': bs.find('input', {'name':'code'})['value'],
        'id_token': bs.find('input', {'name':'id_token'})['value'],
        'scope': bs.find('input', {'name':'scope'})['value'],
        'state': bs.find('input', {'name':'state'})['value'],
        'session_state': bs.find('input', {'name':'session_state'})['value'],
    }
    r = s.post('https://card.cc98.org/signin-cc98',
               headers={'content-type': 'application/x-www-form-urlencoded'}, 
               data=data)

    # 3. 抽卡
    r = s.get('https://card.cc98.org/Draw')
    bs = BeautifulSoup(r.text, 'html.parser')
    data = {'__RequestVerificationToken':bs.find('input', {'name':'__RequestVerificationToken'})['value'],
            'X-Requested-With': 'XMLHttpRequest'}
        
    count = num_N = num_R = num_SR = num_SSR = num_M = 0
    while count < times:
        current_wealth = requests.get("https://api.cc98.org/user/name/{}".format(username)).json()['wealth']
        if current_wealth < least_wealth:
            print('财富值不足。')
            break
        if action == 1:
            print('当前财富值: {:7d}, 抽一次:'.format(current_wealth), end=' ')
        else:
            print('当前财富值: {:7d}, 抽十一次:'.format(current_wealth), end=' ')
        
        
        # 开抽！
        r = s.post('https://card.cc98.org/Draw/Run/{}'.format(action), 
                   data=data,
                   headers={"content-type":"application/x-www-form-urlencoded; charset=UTF-8"},
                  )
        bs = BeautifulSoup(r.text, 'html.parser')
    
        N_cards = bs.find_all('div', {'data-level':'0'})
        R_cards = bs.find_all('div', {'data-level':'1'})
        SR_cards = bs.find_all('div', {'data-level':'2'})
        SSR_cards = bs.find_all('div', {'data-level':'3'})
        M_cards = bs.find_all('div', {'data-level':'4'})
        
        num_N += len(N_cards)
        num_R += len(R_cards)
        num_SR += len(SR_cards)
        num_SSR += len(SSR_cards)
        num_M += len(M_cards)
        count += 1
        
        print('抽到{:2d} 张N卡, {:2d} 张R卡, {:2d} 张SR卡, {:2d} 张SSR卡, {:2d} 张M卡！'.format(len(N_cards), len(R_cards), len(SR_cards), len(SSR_cards), len(M_cards)))
    
    num_cards = [num_N, num_R, num_SR, num_SSR, num_M]
    table = PrettyTable(['\033[33m等级\033[0m','N', 'R', 'SR', 'SSR', 'Mystery'])
    table.add_row(['\033[33m数量\033[0m'] + num_cards)
    print('\n\033[1;31m抽卡情况总览:\033[0m\n', table)

#    SSR_M = SSR_cards + M_cards
#    if SSR_M:
#        for i in SSR_M:
#            img_src = i.find_all('img')[1]['src']
#            image = io.imread('https://card.cc98.org'+img_src)
#            io.imshow(image)
#            io.show()


    def if_destroy():
        # 分解重复卡牌
        r = s.get('https://card.cc98.org/Home/Collection')
        bs = BeautifulSoup(r.text, 'html.parser')
        data = {
            '__RequestVerificationToken': bs.find('input', {'name':'__RequestVerificationToken'})['value']
        }

        r = s.get('https://card.cc98.org/Card/Refund?X-Requested-With=XMLHttpRequest&_='+str(int(time.time()*1000)))
        bs = BeautifulSoup(r.text, 'html.parser')
        refund = bs.find('strong', class_="text-success").text
        
        s.post('https://card.cc98.org/Card/DestroyAll', data=data)
        print(f'分解重复卡牌得到{refund}个财富值。')

#%%time
main()

