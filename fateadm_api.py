# coding=utf-8
import os,sys;
import base64;
import hashlib;
import time;
import urllib;
import json;
import string;
import requests;

FATEA_PRED_URL  = "http://pred.fateadm.com"

def LOG(log):
    # 不需要测试时，注释掉日志就可以了
    # print(log);
    log = None;

class TmpObj():
    def __init__(self):
        self.value  = None;

class Rsp():
    def __init__(self):
        self.ret_code   = -1;
        self.cust_val   = 0.0;
        self.err_msg    = "succ";
        self.pred_rsp   = TmpObj();

    def ParseJsonRsp(self, rsp_data):
        if rsp_data is None:
            self.err_msg     = "http request failed, get rsp Nil data";
            return
        jrsp                = json.loads( rsp_data);
        self.ret_code       = int(jrsp["RetCode"]);
        self.err_msg        = jrsp["ErrMsg"];
        self.request_id     = jrsp["RequestId"];
        if self.ret_code == 0:
            rslt_data   = jrsp["RspData"];
            if rslt_data is not None and rslt_data != "":
                jrsp_ext    = json.loads( rslt_data);
                if "cust_val" in jrsp_ext:
                    data        = jrsp_ext["cust_val"];
                    self.cust_val   = float(data);
                if "result" in jrsp_ext:
                    data        = jrsp_ext["result"];
                    self.pred_rsp.value     = data;

def CalcSign(usr_id, passwd, timestamp):
    md5     = hashlib.md5();
    md5.update((timestamp + passwd).encode());
    csign   = md5.hexdigest();

    md5     = hashlib.md5();
    md5.update((usr_id + timestamp + csign).encode());
    csign   = md5.hexdigest();
    return csign;

def CalcCardSign(cardid, cardkey, timestamp, passwd):
    md5     = hashlib.md5();
    md5.update(passwd + timestamp + cardid + cardkey);
    return md5.hexdigest();

def HttpRequest(url, body_data):
    rsp         = Rsp();
    post_data   = body_data;
    header      = {
            'User-Agent': 'Mozilla/5.0',
            };
    rsp_data    = requests.post(url, post_data, headers=header);
    rsp.ParseJsonRsp( rsp_data.text);
    return rsp;

class FateadmApi():
    def __init__(self, app_id, app_key, usr_id, usr_key):
        self.app_id     = app_id;
        if app_id is None:
            self.app_id = "";
        self.app_key    = app_key;
        self.usr_id     = usr_id;
        self.usr_key    = usr_key;
        self.host       = FATEA_PRED_URL;

    def SetHost(self, url):
        self.host       = url;
    #
    # 查询余额
    #
    def QueryBalc(self):
        tm      = str( int(time.time()));
        sign    = CalcSign( self.usr_id, self.usr_key, tm);
        param   = {
                "user_id": self.usr_id,
                "timestamp":tm,
                "sign":sign
                };
        url     = self.host + "/api/custval"
        rsp     = HttpRequest(url, param);
        if rsp.ret_code == 0:
            LOG("query succ ret: {} cust_val: {} rsp: {} pred: {}".format( rsp.ret_code, rsp.cust_val, rsp.err_msg, rsp.pred_rsp.value));
        else:
            LOG("query failed ret: {} err: {}".format( rsp.ret_code, rsp.err_msg.encode('utf-8')));
        return rsp;

    #
    # 查询网络延迟
    #
    def QueryTTS(self, pred_type):
        tm          = str( int(time.time()));
        sign        = CalcSign( self.usr_id, self.usr_key, tm);
        param       = {
                "user_id": self.usr_id,
                "timestamp":tm,
                "sign":sign,
                "predict_type":pred_type,
                }
        if self.app_id != "":
            #
            asign       = CalcSign(self.app_id, self.app_key, tm);
            param["appid"]     = self.app_id;
            param["asign"]      = asign;
        url     = self.host + "/api/qcrtt";
        rsp     = HttpRequest(url, param);
        if rsp.ret_code == 0:
            LOG("query rtt succ ret: {} request_id: {} err: {}".format( rsp.ret_code, rsp.request_id, rsp.err_msg));
        else:
            LOG("predict failed ret: {} err: {}".format( rsp.ret_code, rsp.err_msg.encode('utf-8')));
        return rsp;

    #
    # 识别验证码
    #
    def Predict(self, pred_type, img_data, head_info = ""):
        tm          = str( int(time.time()));
        sign        = CalcSign( self.usr_id, self.usr_key, tm);
        img_base64  = base64.b64encode( img_data);
        param       = {
                "user_id": self.usr_id,
                "timestamp":tm,
                "sign":sign,
                "predict_type":pred_type,
                "img_data":img_base64,
                }
        if head_info is not None or head_info != "":
            param["head_info"] = head_info;
        if self.app_id != "":
            #
            asign       = CalcSign(self.app_id, self.app_key, tm);
            param["appid"]     = self.app_id;
            param["asign"]      = asign;
        url     = self.host + "/api/capreg";
        rsp     = HttpRequest(url, param);
        if rsp.ret_code == 0:
            LOG("predict succ ret: {} request_id: {} pred: {} err: {}".format( rsp.ret_code, rsp.request_id, rsp.pred_rsp.value, rsp.err_msg));
        else:
            LOG("predict failed ret: {} err: {}".format( rsp.ret_code, rsp.err_msg.encode('utf-8')));
            if rsp.ret_code == 4003:
                #lack of money
                LOG("cust_val <= 0 lack of money, please charge immediately");
        return rsp;

    #
    # 从文件进行验证码识别
    #
    def PredictFromFile( self, pred_type, file_name, head_info = ""):
        with open(file_name, "rb") as f:
            data = f.read();
        return self.Predict( pred_type, data, head_info);

    #
    # 识别失败，进行退款请求
    # 注意:
    #    Predict识别接口，仅在ret_code == 0时才会进行扣款，才需要进行退款请求，否则无需进行退款操作
    # 注意2:
    #   退款仅在正常识别出结果后，无法通过网站验证的情况，请勿非法或者滥用，否则可能进行封号处理
    #
    def Justice(self, request_id):
        if request_id == "":
            #
            return ;
        tm          = str( int(time.time()));
        sign        = CalcSign( self.usr_id, self.usr_key, tm);
        param       = {
                "user_id": self.usr_id,
                "timestamp":tm,
                "sign":sign,
                "request_id":request_id
                }
        url     = self.host + "/api/capjust";
        rsp     = HttpRequest(url, param);
        if rsp.ret_code == 0:
            LOG("justice succ ret: {} request_id: {} pred: {} err: {}".format( rsp.ret_code, rsp.request_id, rsp.pred_rsp.value, rsp.err_msg));
        else:
            LOG("justice failed ret: {} err: {}".format( rsp.ret_code, rsp.err_msg.encode('utf-8')));
        return rsp;

    #
    # 充值接口
    #
    def Charge(self, cardid, cardkey):
        tm          = str( int(time.time()));
        sign        = CalcSign( self.usr_id, self.usr_key, tm);
        csign       = CalcCardSign(cardid, cardkey, tm, self.usr_key);
        param       = {
                "user_id": self.usr_id,
                "timestamp":tm,
                "sign":sign,
                'cardid':cardid,
                'csign':csign
                }
        url     = self.host + "/api/charge";
        rsp     = HttpRequest(url, param);
        if rsp.ret_code == 0:
            LOG("charge succ ret: {} request_id: {} pred: {} err: {}".format( rsp.ret_code, rsp.request_id, rsp.pred_rsp.value, rsp.err_msg));
        else:
            LOG("charge failed ret: {} err: {}".format( rsp.ret_code, rsp.err_msg.encode('utf-8')));
        return rsp;

def TestFunc(file_name):
    pd_id           = "xxx";     #用户信息页可以查询到pd信息
    pd_key          = "xxxx";
    app_id          = "xxx";     #开发者分成用的账号，在开发者中心可以查询到
    app_key         = "xxxx";
    #识别类型，
    #具体类型可以查看官方网站的价格页选择具体的类型，不清楚类型的，可以咨询客服
    pred_type       = "30600";
    api             = FateadmApi(app_id, app_key, pd_id, pd_key);
    api.QueryBalc();
    #如果不是通过文件识别，则调用Predict接口
    file_name       = file_name;
    rsp             = api.PredictFromFile( pred_type, file_name);
    just_flag    = False;
    if just_flag :
        if rsp.ret_code == 0:
            #识别的结果如果与预期不符，可以调用这个接口将预期不符的订单退款
            # 退款仅在正常识别出结果后，无法通过网站验证的情况，请勿非法或者滥用，否则可能进行封号处理
            api.Justice( rsp.request_id);

    #card_id         = "123";
    #card_key        = "123";
    #充值
    #api.Charge(card_id, card_key);
    LOG("print in testfunc");
    return rsp.pred_rsp.value



