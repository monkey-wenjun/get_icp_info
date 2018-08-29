#!/usr/bin/env python3
#-*-coding:utf-8-*-
# Auth :awen
# Email: hi@awen.me


import requests
import fateadm_api
from bs4 import BeautifulSoup
import random

requests_session = requests.session()


# 获取验证码进行解析，这里调用 http://www.fateadm.com/price.html 打码平台的接口获取验证码

def get_verify_code():
    url = "http://www.miitbeian.gov.cn/getVerifyCode?"+str(random.randint(1,100))

    headers = {
        'Accept': "image/webp,image/apng,image/*,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
        'Cache-Control': "no-cache",
        'Connection': "keep-alive",
        'DNT': "1",
        'Host': "www.miitbeian.gov.cn",
        'Pragma': "no-cache",
        'Referer': "http://www.miitbeian.gov.cn/icp/publish/query/icpMemoInfo_showPage.action",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    }

    response = requests_session.get(url, headers=headers)
    if response.status_code == 200:
        with open('code.jpg', 'wb') as file:
            file.write(response.content)
    verifyCode = fateadm_api.TestFunc('code.jpg')
    return verifyCode


# 模拟输入验证码后判断验证码是否输入正确

def check_verify_code(validateValue):
    url = "http://www.miitbeian.gov.cn/common/validate/validCode.action"

    payload = {"validateValue": validateValue}
    headers = {
        'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        'Accept': "application/json, text/javascript, */*",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
        'Cache-Control': "no-cache",
        'Connection': "keep-alive",
        'Content-Length': "20",
        'Content-Type': "application/x-www-form-urlencoded",
        'DNT': "1",
        'Host': "www.miitbeian.gov.cn",
        'Origin': "http://www.miitbeian.gov.cn",
        'Pragma': "no-cache",
        'Referer': "http://www.miitbeian.gov.cn/icp/publish/query/icpMemoInfo_showPage.action",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
        'X-Requested-With': "XMLHttpRequest",
    }

    response = requests_session.post(url, data=payload, headers=headers)
    if response.status_code != 200:
        return
    resp_json = response.json()
    return resp_json['result']


# 模拟查询并反馈备案信息
# 例如：{'name': '杭州网易质云科技有限公司', 'nature': '企业', 'icp_number': '浙ICP备17006647号-2', 'web_name': '网易云', 'domain': 'www.163yun.com', 'check_data': '2018-07-17'}

def do_request_beian(domain, verifyCode):
    url = "http://www.miitbeian.gov.cn/icp/publish/query/icpMemoInfo_searchExecute.action"
    payload = "siteName=&condition=1&siteDomain=" + domain + "&siteUrl=&mainLicense=&siteIp=&unitName=&mainUnitNature=-1&certType=-1&mainUnitCertNo=&verifyCode=" + verifyCode

    headers = {
        'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW",
        'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
        'Accept-Encoding': "gzip, deflate",
        'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8",
        'Cache-Control': "no-cache",
        'Connection': "keep-alive",
        'Content-Length': "144",
        'Content-Type': "application/x-www-form-urlencoded",
        'DNT': "1",
        'Host': "www.miitbeian.gov.cn",
        'Origin': "http://www.miitbeian.gov.cn",
        'Pragma': "no-cache",
        'Referer': "http://www.miitbeian.gov.cn/icp/publish/query/icpMemoInfo_showPage.action",
        'Upgrade-Insecure-Requests': "1",
        'User-Agent': "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36",
    }

    response = requests_session.post(url, data=payload, headers=headers)
    if response.status_code != 200:
        return
    html_context = response.text

    # 解析 html，获取对应的值存入 dict 中
    soup = BeautifulSoup(html_context, "html.parser")
    soup_msg = soup.find_all(name='td', attrs={'class': "bxy"})
    if len(soup_msg):
        icp_list = []
        for content in soup_msg:
            content = content.get_text()
            content_out = "".join(content.split())
            icp_list.append(content_out)
        icp_info = {"name": icp_list[0], "nature": icp_list[1], "icp_number": icp_list[2],
                    "web_name": icp_list[3], "domain": icp_list[4], "check_data": icp_list[-2]}
        return icp_info
    print("未备案")


if __name__ == '__main__':

    verify_code = str(get_verify_code()).upper()
    # if check_verify_code(verify_code) is True:
    print(do_request_beian("qingchan.me", verify_code))
