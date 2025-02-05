#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import *
import os
import json
import random
import string
import time
import pymysql
import configparser
import datetime
import qrcode
from flask_cors import CORS
from untils import generate_logger
from setting import HOST_PROXY, PORT_PROXY

from tasks import *
import celery
from PIL import Image, ImageFont, ImageDraw

from KeyWrapper.KeyWrapper import KeyWrapper
from pic import add_ideal as add_ideal_new

app = Flask(__name__)
CORS(app)
server_dir = os.path.dirname(os.path.realpath(__file__))
config_file = os.path.join(server_dir, 'config.py')
app.config.from_pyfile(config_file)

_tpl_dir = os.path.dirname(os.path.realpath(__file__))+'/templates/'
conf = configparser.ConfigParser()
conf.read(os.path.join(server_dir, "config.cfg"))
_error_log = generate_logger("error_html")
mgc = map(lambda x:x.strip(), open("mgc.txt",encoding='utf-8').readlines())
# _nor_log = generate_output_logger("")
keywrapper = KeyWrapper()

def handle_static(res, name):
    return send_from_directory(_tpl_dir+res, name)


def send_page(name):
    return send_from_directory(_tpl_dir, name)


@app.route('/js/<path:name>')
def static_js(name):
    return handle_static('js', name)


@app.route('/styles/<path:name>')
def static_css(name):
    return handle_static('styles', name)


@app.route('/images/<path:name>')
def static_img(name):
    return handle_static('images', name)


@app.route('/css/<path:name>')
def get_assets(name):
    return handle_static('css', name)


@app.route('/fonts/<path:name>')
def get_fonts(name):
    return handle_static('fonts', name)


@app.route('/share/new/<path:name>')
def get_share(name):
    return send_from_directory(server_dir+"/share/new/", name)


@app.route("/")
# @app.route('/?<user>')
def index(user=None):
    # if(random.random()>0.3):
        # return send_page("index.html")
    return send_page("index.html")

@app.route("/demo")
# @app.route('/?<user>')
def index_demo():
    # if(random.random()>0.3):
        # return send_page("index.html")
    return send_page("index_demo.html")

@app.route('/readme')
def red():
    return send_page("readme.html")


@app.route('/sendPoem', methods=['POST'])
def sendProm():
    # ip_address = request.remote_addr
    s = request.form
    #print(request)
    print(request.form)
    for i in mgc:
        if(i in s['keyword']):
            return json.dumps({'code':"mgc"})
    if(s['type'] == u'CT'):
        if(len(s['keyword']) > 4):
            return json.dumps({'code':"mgc"})
        for i in s['keyword']:
            if('0' <= i <= '9' or 'a' <= i <= 'z'):
                return json.dumps({'code':"mgc"})
    if(s['type'] == u'SC'):
        if(len(s['keyword'].split(" ")) > 4):
            return json.dumps({'code':"mgc"})
    #print(s['keyword'].encode("utf-8"))
    #for i in s['keyword'].decode("utf-8"):
        #if(not (u'\\u4e00' <= i <= u'\\u9fa5')):
            #print(i)
            #return "mgc"
    tsinghua_word = [u'自强不息',u'厚德载物',u'行胜于言',u'我爱清华',u'清华等我',u'圆梦清华',u'清小华',u'清华招生',u'无体育不清华',u'清华正芳华']

    ans_tsinghua = None
    if(s['keyword'] in tsinghua_word):
        time.sleep(random.random()*2 + 1)
        num = random.randint(1, 10)
        im = Image.open(server_dir+'/share/tsinghua/' + str(num) + '.jpg')
        time_str = str(time.time())
        filename = '/share/new/' + time_str + '.jpg'
        im.save(server_dir+filename)
        ans_tsinghua = {'code':"tsinghua", "ans":time_str + '.jpg'}

    ans = ""
    print("begin")
    # print s
    try:
        conn = pymysql.connect(
            host=conf.get("db","db_host"),
            user=conf.get("db","db_name"),
            passwd=conf.get("db","db_password"),
            db=conf.get("db","db_database"),
            charset="utf8")
        cursor = conn.cursor()

        cursor.execute("select * from result_id where user_id = %s", (s['user_id']))
        u = cursor.fetchone()

        cursor.execute("select id from list_"+s['type']+" where status = %s order by id desc limit 1", ('SUCCESS'))
        queue_start = cursor.fetchone()
        if(queue_start == None):
            queue_start = [0]
        new_flag = True
        print(u)
        if(u != None):
            result = celery.result.AsyncResult(u[2])
            status = result.status
            print(u[1], status)
            if(status == 'SUCCESS' or status == 'FAILURE'):
                new_flag = False
        if(u != None and new_flag):
            ans = str(int(u[3])-int(queue_start[0]))
        else:
            # print u
            type_top = {'type':s['type'], "yan":s['yan'], "top":s['keyword']}
            # type_top = {'type':'JJ', "yan":'7', "top":'清华'}
            poem = {'user_id':s['user_id'], 'type_top':type_top}

            # cursor.execute("select result from peom_map where type = %s and content = %s", (s['type'], jsom.dumps(type_top, sort_keys=True)))
            # poem_map = cursor.fetchone()


            # if len(poem_map) > 0:
            #     if(random.random() > 0.6):
            #         use_content = poem_map[int(random.random()*len(poem_map))]
            #         poem['used'] = use_content
            #     else:
            #         poem['used'] = None
            cele = None
            if(s['type'] == "JJ"):
                if(random.random() > 0.0):
                    print("JJ yxy")
                    cele = main_JJ.delay(json.dumps(poem))
                else:
                    print("JJ yc")
                    cele = main_JJ1.delay(json.dumps(poem))
                # print cele.id

            elif(s['type'] == "CT"):
                cele = main_CT.delay(json.dumps(poem))
            elif(s['type'] == "JJJ"):
                cele = main_JJJ.delay(json.dumps(poem))
            elif(s['type'] == "SC"):
                cele = main_SC.delay(json.dumps(poem))
            elif(s['type'] == "JueJu"):
                words = type_top['top']
                model, newwords = keywrapper.process(words.strip().split(" "))
                newwords = " ".join(newwords)
                type_top['top'] = newwords
                yan_map = {"5":"-1","7":"0"}
                print(model, "JueJu")
                if(model == 'wm'):
                    type_top['yan'] = yan_map[type_top['yan']]
                    poem = {'user_id':s['user_id'], 'type_top':type_top}
                    cele = main_SC.apply_async(args=[json.dumps(poem)], queue='JJ2_tencent')
                else:
                    poem = {'user_id':s['user_id'], 'type_top':type_top}
                    cele = main_JJ.apply_async(args=[json.dumps(poem)], queue="JJ_tencent")
            print(cele.task_id)

            cursor.execute('insert into list_'+s['type']+'(id, user_id, status) values(null, %s, %s)', (s['user_id'], "PENDING"))
            conn.commit()

            cursor.execute("select LAST_INSERT_ID();")
            u_id = cursor.fetchone()

            ans = str(int(u_id[0])-int(queue_start[0]))

            # else:
                # cursor.execute('update result set content=null, type_top=%s where user_id=%s', (json.dumps(type_top), s['user_id']))
            # print "succ"
            if(new_flag):
                cursor.execute('insert into result_id(user_id, celery_id, list_num) values(%s, %s, %s)', (s['user_id'], cele.task_id, str(u_id[0])))
            else:
                cursor.execute('update result_id set celery_id = %s, list_num = %s where user_id = %s', (cele.task_id, str(u_id[0]), u[1]))
            conn.commit()


    except pymysql.Error as e:
        _error_log.error("Mysql Error %d: %s" % (e.args[0], e.args[1]))
        print(e)
    finally:
        cursor.close()
        conn.close()
    if(ans_tsinghua is None):
        return json.dumps({"code" :"0000", "ans":ans})
    else:
        return json.dumps(ans_tsinghua)


@app.route('/getPoem', methods=['POST'])
def getProm():
    ans = {'code':'0', 'content':''}
    ip_address = request.remote_addr
    s = request.form
    # print s
    try:
        conn = pymysql.connect(
            host=conf.get("db","db_host"),
            user=conf.get("db","db_name"),
            passwd=conf.get("db","db_password"),
            db=conf.get("db","db_database"),
            charset="utf8")
        cursor = conn.cursor()

        cursor.execute("select * from result_id where user_id = %s", (s['user_id']))
        u = cursor.fetchone()

        if(u == None):
            ans['content'] = "error"
        else:
            result = celery.result.AsyncResult(u[2])
            status = result.status
            print(status)

            if(status == 'SUCCESS'):
                prom = json.loads(result.result)
                tmp = prom['result']
                print(prom)

                if(s['type'] == "SC"):
                    if(len(tmp['content']) == 1):
                        ans['content'] = tmp['content'][0]
                    else:
                        ans['content'] = tmp['content'][0] + ['-'] + tmp['content'][1]
                elif(s['type'] == "JueJu"):
                    if(len(tmp['content']) == 1):
                        ans['content'] = tmp['content'][0]
                    else:
                        ans['content'] = tmp['content'].split("\t")
                else:
                    ans['content'] = tmp['content'].split("\t")

                if(tmp['code'] == 1):
                    ans['source'] = tmp['source']
                if('type' in tmp):
                    ans['type'] = tmp['type']
                    if('state' in tmp):
                        ans['state'] = tmp['state']
                ans['code'] = '1'
                cursor.execute('INSERT INTO result_all(id, user_id, type_top, itime, content, ip) VALUES(null, %s, %s, %s, %s, %s)', (prom['user_id'], json.dumps(prom['type_top']), datetime.datetime.now(), json.dumps(prom['result']), ip_address))
                cursor.execute('update list_'+s['type']+' set status = %s where id = %s', (status, u[3]))
                conn.commit()

            elif(status == 'STARTED'):
                ans['content'] = '0'
            elif(status == 'FAILURE'):
                ans['content'] = 'error'
            else:
                cursor.execute("select id from list_"+s['type']+" where status = %s order by id desc limit 1", ('SUCCESS'))
                queue_start = cursor.fetchone()
                print(queue_start, u[3])
                if(queue_start == None):
                    queue_start = [0]
                ans['content'] = int(u[3])-int(queue_start[0]) - 1
                if(ans['content'] <= 0):
                    ans['content'] = '0'
                else:
                    ans['content'] = str(ans['content'])
    except pymysql.Error as e:
        print(e)
        _error_log.error("Mysql Error %d: %s" % (e.args[0], e.args[1]))
        ans['content'] = "error"
    finally:
        cursor.close()
        conn.close()
    print(ans)
    return json.dumps(ans)


@app.route('/sendstar', methods=['POST'])
def sendstar():
    ans = "1"
    s = request.form
    try:
        conn = pymysql.connect(
            host=conf.get("db","db_host"),
            user=conf.get("db","db_name"),
            passwd=conf.get("db","db_password"),
            db=conf.get("db","db_database"),
            charset="utf8")
        cursor = conn.cursor()
        cursor.execute('update result_all set star = %s where user_id = %s order by id desc limit 1',(str(s['star']), s['user_id']))
        conn.commit()
    except pymysql.Error as e:
        _error_log.error("Mysql Error %d: %s" % (e.args[0], e.args[1]))
        ans = "0"
    finally:
        cursor.close()
        conn.close()
    return ans

@app.route('/share', methods=['POST'])
def share():
    form = request.form
    jtype = form['type']
    if(jtype == "SC"):
        return share2(form)
    if(len(form['lk']) == 0 and random.random() < 0.3):
        return share2(form)
    return share1(form)


def share2(form):
    s = json.loads(form['share'])['content']
    # lk = request.form['lk']
    yan = form['yan']
    jtype = form['type']
    if(jtype == "SC"):
        yan = int(yan) + 1
    else:
        if(int(yan) == 7):
            yan = 1
        else:
            yan = 0
    # tt = request.form['tt']
    # if(len(lk) == 0):
    #     lk = u'九歌作'
    # print(s)
    ideal = s
    # for i in s:
        # ideal.append([])
        # for j in i:
            # ideal[-1].append(j)
    print(ideal)
    # ans = get_ans(ideal)
    ans = add_ideal_new(int(random.random()*5)+1, yan, ideal, server_dir)
    # clean()
    # print 'ans=', ans
    return ans
    # return render_template("share.html", ans = ans)
    # return render(request, "IdealColor/templates/1.html")

# @app.route('/share1', methods=['POST'])
def share1(form):
    s = json.loads(form['share'])['content']
    lk = form['lk']
    yan = form['yan']
    jtype = form['type']
    tt = form['tt']
    if(len(lk) == 0):
        lk = u'九歌作'
    # print(s)
    ideal = []
    for i in s:
        ideal.append([])
        for j in i:
            ideal[-1].append(j)
    print(ideal)
    # ans = get_ans(ideal)
    ans = add_ideal(int(random.random()*55)+1, yan, jtype, tt, ideal, lk)
    # clean()
    # print 'ans=', ans
    return ans
    # return render_template("share.html", ans = ans)
    # return render(request, "IdealColor/templates/1.html")

#@app.route('/pic_share/<path:name>')
#def pic_share(name):
#    print(name)
   # return render_template("share.html", title = "九歌分享", ans = '/share/new/' + name)
@app.route('/pic_share_html/<path:name>')
def pic_share(name):
    print(name)
    return render_template("share.html", title = u"九歌分享", ans = '/share/new/' + name, ans1 = "/share/new/"+ name.replace(".jpg", "ew.jpg"))

@app.route('/pic_share_tsinghua/<path:name>')
def pic_share_tsinghua(name):
    print(name)
    return render_template("share1.html", title = u"清华彩蛋", ans = '/share/new/' + name)

def clean():
    flist = os.listdir('IdealColor/static/images')
    now = time.strftime('%H', time.localtime(time.time()))
    print( now)
    for i in flist:
        get_time = i.split('_')[0]
        if now != get_time and len(i) > 10:
            os.remove('IdealColor/static/images/' + i)


def add_ideal(ans, yan, jtype, tt, ideal, lk = u'九歌作'):
    im = Image.open(server_dir+'/share/old/' + str(ans) + '.jpg')
    draw = ImageDraw.Draw(im)
    # newfont = ImageFont.truetype('IdealColor/static/fonts/PingFang Heavy.ttf', 150)
    newfont = ImageFont.truetype(server_dir+'/share/font/STXINGKA.ttf', 110)
    # print time.strftime('%H_%M_%S', time.localtime(time.time()))
    # print 'color', color[ans]
    # print 'pos', pos
    # print 'ideal', ideal
    # print 'font', newfont
    draw = ImageDraw.Draw(im)
    # newfont = ImageFont.truetype('IdealColor/static/fonts/PingFang Heavy.ttf', 150)
    newfont = ImageFont.truetype(server_dir+'/share/font/STXINGKA.ttf', 90)
    # print time.strftime('%H_%M_%S', time.localtime(time.time()))
    # print 'color', color[ans]
    # print 'pos', pos
    # print 'ideal', ideal
    # print 'font', newfont
    title = ""
    if(yan == u'5'):
        title = u'五绝'
    else:
        title = u'七绝'
    if(jtype == u'CT'):
        title += u'︿藏头﹀'
    elif(jtype == u'JJJ'):
        title += u'︿集句﹀'
    # print(tt.encode("utf-8"))
    title += u'·' + tt
    tmp = len(title) / 2.0 * 90
    for i in range(len(title)):
        draw.text((880, 880 + i * 90 - tmp), title[i], (0xFF,0xFF,0xFF), font=newfont)

    py = 0
    if(len(ideal[0]) == 7):
        for i in range(4):
            for j in range(7):
                draw.text((720 - i * 150, 580 + j * 90), ideal[i][j], (0xFF,0xFF,0xFF), font=newfont)
    else:
        for i in range(4):
            for j in range(5):
                draw.text((720 - i * 150, 670 + j * 90), ideal[i][j], (0xFF,0xFF,0xFF), font=newfont)
    # im.show()
    newfont = ImageFont.truetype(server_dir+'/share/font/STXINGKA.ttf', 65)
    if(lk):
        tmp = len(lk) / 2.0 * 65
        for i in range(len(lk)):
            draw.text((130 , 980 + i * 65 - tmp), lk[i], (0xFF,0xFF,0xFF), font=newfont)

    ntime = datetime.datetime.now()
    time_dy = [u'零', u'一', u'二', u'三', u'四', u'五', u'六', u'七', u'八', u'九']

    tmp = ntime.strftime("%Y")
    time_time = ""
    for i in range(4):
        time_time += time_dy[int(tmp[i])]
    time_time += u'年'
    tmp = ntime.strftime("%m")
    if(tmp[0] == '0'):
        time_time += time_dy[int(tmp[1])]
    else:
        time_time += time_dy[int(tmp[0])] + time_dy[int(tmp[1])]
    time_time += u'月'
    tmp = ntime.strftime("%d")
    if(tmp[0] == '0'):
        time_time += time_dy[int(tmp[1])]
    else:
        time_time += time_dy[int(tmp[0])] + time_dy[int(tmp[1])]
    time_time += u'日'
    # print(time_time)
    for i in range(len(time_time)):
        draw.text((130 , 1145 + i * 60), time_time[i], (0xFF,0xFF,0xFF), font=newfont)

    time_str = str(time.time())
    filename = '/share/old_new/' + time_str + '.jpg'
    im.save(server_dir+filename)
    # img = qrcode.make("https://jiuge.thunlp.cn/pic_share/"+time_str+".jpg")
    # img.save(server_dir + filename.replace(".jpg", "ew.jpg"))
    return time_str + '.jpg'


if __name__ == '__main__':
    conf.read("config.cfg")

    if app.config['DEBUG']:
        app.run(host="127.0.0.1", port = 5100, debug=True)
    else:
        app.run(host="0.0.0.0", port = 5100, debug=False)
    # add_ideal(1, [[u"清",u"华",u"大",u"学",u"我"] for i in range(4)], [u"清",u"华",u"大"])
