#材料リストを読み込む
import openpyxl
import os
import re
from bs4 import BeautifulSoup
import requests
import pprint
import time
import jaconv
import itertools
from fractions import Fraction
import math
import tkinter as tk
from tkinter import font
from PIL import Image, ImageTk
import webbrowser

#ユーザーに入力してもらう
path=os.path.abspath('ingredients_dict.xlsx')
read=openpyxl.load_workbook(path)
sheet=read["Sheet1"]
header=None
ingredient_dictlist=[]
for data in sheet.rows:
    if data[0].row==1:
        header=data
    else:
        ingredient_dict={}
        for i,j in zip(header,data):
            ingredient_dict[i.value]=j.value
        ingredient_dictlist.append(ingredient_dict)

while True:
    # 材料チェック
    key_ingredient=str(input("\n食材名を入力してください\n>>>"))
    key_number=0
    for i in ingredient_dictlist:
        if bool(re.fullmatch(i["name"],key_ingredient))==True:
            key_number=i['number']
    if key_number==0:
        print("その材料を検索する能力がまだありません。ごめんなさい。")
    else:
        break

# 量チェック
info_amount=ingredient_dictlist[key_number-1]["g_amount"]
info_tan=ingredient_dictlist[key_number-1]["tan"]
print("\n参考：{0} は {1} あたり {2}g です\n".format(key_ingredient,info_tan,info_amount))
key_amount=int(input("材料をグラム単位で入力してください　(例：200)\n>>>"))

while True:
    # 日数チェック
    key_dates=int(input("\n使い切りたい日数を入力してください　(例：3)\n>>>"))
    if 1<=key_dates<=7:
        break
    else:
        print('日数は7日以内です。')

print('\n*****************************\n')
# 2.利用するレシピの条件をチェックする関数を作る(人数分、材料名、量についての)

#URLをsoupにして返してくれる関数
def htmlparser(url):
    beforeurl=requests.get(url)
    soup=BeautifulSoup(beforeurl.text,"html.parser")
    return(soup)

# 2-1.何人前かチェックする関数
def check_persons(recipesoup):
    # 人数が明記してあるタグをセット
    find_person=recipesoup.find('div',class_="content")
    persons=0
    for child in find_person:
        i=jaconv.z2h(child.string,digit=True,ascii=True)
        if child==find_person.find('span',class_="servings_for yield") and bool(re.search(r"\d",i))==True:
            persons=re.search(r"\d",i).group()
    # 何人前かを数字で返す
    # 人数を表すタグがある　かつ　数字がある　(0ではない)→　採用
    return persons

# 2-2.材料をリスト化して、辞書を参照し,入力された材料が含まれているかチェックする関数
def check_ingredient(recipesoup,key_number):
    time.sleep(1)
    find_ingredient=recipesoup.find_all('span',class_="name")#リストで返ってくる
    #材料のリストを作る関数
    def ingredient_name(find_ingredient):
        list=[]
        for child in find_ingredient:#入れ子になっている材料も入手する
            if bool(child.string)==True:
                list.append(child.string)
            else:
                for grandchild in child.descendants:
                    list.append(grandchild.string)
                    break
        return list
    ingredient_name_list=ingredient_name(find_ingredient)

    # 辞書を参照し、材料リストの中にキーワードがあるか確認する
    check_ingredient=0
    for ingredient_name in ingredient_name_list:
        # try:
        if bool(re.fullmatch(ingredient_dictlist[key_number-1]["name"],ingredient_name))==True:
            check_ingredient=1
        # except:
        #     pass
    # 材料名のリストと材料チェックの結果を返す
    # 材料名チェックの結果が1　→　採用
    return ingredient_name_list,check_ingredient

# 2-3.材料の量をリスト化する関数
def check_amount(recipesoup,key_number,check_ingredient):
    time.sleep(1)
    find_amount=recipesoup.find_all('div',class_="ingredient_quantity amount")
    def ingredient_amount(find_amount):
        list=[]
        for amount in find_amount:
            list.append(amount.string)
        return(list)
    ingredient_amount_list=ingredient_amount(find_amount)

    # 材料と量を合わせて辞書にする
    ingredient_dict={}
    for i,j in zip(ingredient_name_list,ingredient_amount_list):
        ingredient_dict[i]=j
        if bool(re.fullmatch(ingredient_dictlist[key_number-1]["name"],i))==True:
            # 量を材料リストから取り出して半角にしたものを格納する
            check_amount=jaconv.z2h(ingredient_dict[i],digit=True,ascii=True)
    if check_ingredient==0:
        check_amount=""

    # 量を材料リストから取り出して半角にしたものを格納する

    # 量に数字がないもの、()が含まれているものをNGとする
    if bool(re.findall(r"\d",check_amount))==False or bool(re.findall("~|\(|\)",check_amount))==True:
        judge_amount=0
    else:
        judge_amount=1
    # 材料名と量を組み合わせた辞書と指定された材料名と量のチェックの結果が返ってくる
    # 量のチェックの結果が1　→　採用
    return ingredient_dict,judge_amount

print('\n*****************************\n')
# 3. (2)で作成した関数を用いて、レシピをチェックし、採用されたレシピのリストを作成する
recipe_list=[]
counter=0
while counter<10:
    # 入力された材料を検索したページからレシピのURLを取得してリスト化
    basesoup=htmlparser('https://cookpad.com/search/'+key_ingredient+'?order=date&page='+str(counter+1))
    recipetags=basesoup.find_all(class_="recipe-title font13")
    recipeurls=[]
    for recipetag in recipetags:
        recipeurls.append(recipetag.attrs['href'])
    # 各レシピのページに飛び、条件を満たすかチェックする
    for j in recipeurls:
        time.sleep(1)
        recipesoup=htmlparser('https://cookpad.com'+j)
        persons=check_persons(recipesoup)
        print('\n*****************************\n')
        print(persons)
        ingredient_name_list,check_ingredient_result=check_ingredient(recipesoup,key_number)
        print(ingredient_name_list)
        print(check_ingredient_result)
        ingredient_dict,judge_amount=check_amount(recipesoup,key_number,check_ingredient_result)
        print(ingredient_dict)
        print(judge_amount)
        print('\n*****************************\n')
        # もし満たす場合は、レシピ情報を追加する (20コになったら条件チェックを終わる)
        if persons!=0 and check_ingredient_result==1 and judge_amount==1:
            basedata={}
            basedata['recipe_name']=recipesoup.find('h1',class_="recipe-title fn clearfix").string.replace('\n','')
            basedata['recipe_url']='https://cookpad.com'+j
            basedata['img_url']=recipesoup.find("img",class_="photo large_photo_clickable").attrs["src"]
            basedata['persons']=persons
            basedata['ingredient']=ingredient_dict
            # basedata['key']=key.replace(" ","")
            recipe_list.append(basedata)
            counter=counter+1
            print(counter)
            if counter==10:
                break
for i in recipe_list:
    print(i)

print('\n*****************************\n')
#4.指定された材料の1人分を求めて、更新する
def UpdateToOne(recipedata):
    for i in range(len(recipedata)):#dataの数(50コ)分だけ繰り返す,iはレシピの順番
        for name in recipedata[i]["ingredient"]:
            print(name)
            if bool(re.findall(name,ingredient_dictlist[key_number-1]["name"]))==True:
                key1=name
                amount=recipedata[i]['ingredient'][name]#dataの材料の辞書の中の指定された材料の量を取り出す
                print(amount)
        if bool(re.search("g",amount))==True:#単位がグラムのとき
            a=int(re.search(r"\d+",amount).group())/int(recipedata[i]['persons'])
            recipedata[i]['ingredient'][key1]=a
        else:#単位がグラム以外のとき
            if re.search("/",amount):#分数のとき
                a=Fraction(re.search("\d+/\d+",amount).group())*ingredient_dictlist[key_number-1]['g_amount']
                a=int(a/int(recipedata[i]['persons']))
                recipedata[i]['ingredient'][key1]=a
            else:#整数のとき
                a=(int(re.search(r"\d+",amount).group())*ingredient_dictlist[key_number-1]['g_amount'])/int(recipedata[i]['persons'])
                recipedata[i]['ingredient'][key1]=a
    return a,recipedata
a,recipe_list=UpdateToOne(recipe_list)
pprint.pprint(recipe_list)
print(a)

print('*****************************\n')
#5-1.指定された材料とレシピデータから、量のリストを作成する
#※関数内のingredientはグローバル変数
def MakeAmountlist(recipedata,key_ingredient):
    amountlist=[]#量のリストのオブジェクトを作成
    for i in range(len(recipedata)):#dataの数(50コ)分だけ繰り返す,iはレシピの順番
        for j in recipedata[i]['ingredient'].keys():#材料名をfor文でまわす
            if bool(re.findall(ingredient_dictlist[key_number-1]["name"],j))==True:#入力された材料の量を取り出す
                amountlist.append(recipedata[i]['ingredient'][j])#量のリストに材料の量を追加する
    return amountlist

amountlist=MakeAmountlist(recipe_list,key_ingredient)
print(amountlist)
print('*****************************\n')
#5-2.量のリストと要素番号のリストそれぞれの組み合わせを列挙したリストと合計のリストを作成
#量のリスト(amountlist)の要素番号=レシピのリスト(recipedata)の要素番号である
#あとからレシピを探せるように要素番号のリストと量のリストを紐づけできるようにしておく
def Make_pick_index(amountlist,key_dates,key_amount):
    #要素番号のリストから組み合わせを列挙したものをリスト化する
    indexlist=[]#要素番号記録用のリストを作る
    for i in range(0,len(amountlist)):#要素番号は0~量リストの要素数-1(0~49)
        indexlist.append(i)#要素番号のリストの完成
    combindexlist=[]
    for i in itertools.combinations(indexlist,key_dates):
        combindexlist.append(i)
    combamountlist=[]
    #量のリストから組み合わせを列挙したものをリスト化する
    for i in itertools.combinations(amountlist,key_dates):
        combamountlist.append(i)
    print(combamountlist)
    #各組み合わせ内の和を計算し、sumlistに格納
    sumlist=[]
    for i in combamountlist:
        sumlist.append(sum(i))
    differ=key_amount-sumlist[0]
    pick_index=[]
    for total in sumlist:
        if abs(key_amount-total) <= abs(differ):
            differ=key_amount-total
            pick_sum=total
            index=sumlist.index(total)
    pick_index=list(combindexlist[index])
    pick_index_omake=[]
    if -15<=differ<=15:#近似値の差が+-15以内だったら
        print("A")
        print(pick_sum)
        return pick_index,pick_index_omake
    elif 15<differ:#近似値の差が15以上大きかったら(各要素の量が極端に少ないということ)
        #残りがなくなるまで追加のレシピを考える
        print("B")
        left=key_amount-pick_sum
        while left>0:
            differ2=abs(left-amountlist[0])
            for i in range(len(amountlist)):
                if (i in pick_index):
                    pass
                else:
                    if abs(left-amountlist[i]) <= differ2:
                        differ2=abs(left-amountlist[i])
                        index=i
            pick_index_omake.append(index)
            print(left)
            left=left-amountlist[index]
        return pick_index,pick_index_omake
    else:#近似値の差が15以上小さかったら(一つの量が多すぎる)残りがなくなるまで追加のレシピを考える
        print("C")
        return Make_pick_index(amountlist,key_dates-1,key_amount)

pick_index,pick_index_omake=Make_pick_index(amountlist,key_dates,key_amount)
print(pick_index)
print(pick_index_omake)

print('*****************************\n')
#近似値を持つ組み合わせを最終データ(pickrecipe)として抽出
def Make_pickrecipelist(recipe_list,pick_index):
    pick_recipe_list=[]
    for i in pick_index:
        pick_recipe_list.append(recipe_list[i])
    return pick_recipe_list

pick_recipe_list=Make_pickrecipelist(recipe_list,pick_index)
pick_recipe_list_omake=Make_pickrecipelist(recipe_list,pick_index_omake)
print(pick_recipe_list)

print('*****************************\n')
#レシピ情報の組み合わせを出力する
urllist=[]
for recipe in pick_recipe_list:
    urllist.append(recipe['img_url'])
print(urllist)
urllist2=[]
for recipe in pick_recipe_list_omake:
    urllist2.append(recipe["img_url"])

def download(urllist):
    file_name_list=[]
    wh=[]
    link_name_list=[]
    for i in range(len(urllist)):
        time.sleep(1)
        file_name="recipe{0}.png".format(i)
        link_name="link{0}".format(i)
        url=urllist[i]
        res=requests.get(url)
        image=res.content
        file_name_list.append(file_name)
        link_name_list.append(link_name)
        with open(file_name,"wb") as f:
            f.write(image)
        im=Image.open(file_name)
        w,h=im.size
        wh.append((w,h))
    return file_name_list,wh,link_name_list

def download2(urllist):
    file_name_list2=[]
    wh2=[]
    link_name_list2=[]
    for i in range(len(urllist)):
        time.sleep(1)
        file_name2="recipe2_{0}.png".format(i)
        link_name2="link{0}".format(i)
        url=urllist[i]
        res=requests.get(url)
        image=res.content
        file_name_list2.append(file_name2)
        link_name_list2.append(link_name2)
        with open(file_name2,"wb") as f:
            f.write(image)
        im=Image.open(file_name2)
        w,h=im.size
        wh2.append((w,h))
    return file_name_list2,wh2,link_name_list2

def callback(url):
    webbrowser.open_new(url)

file_name_list,wh,link_name_list=download(urllist)
file_name_list2,wh2,link_name_list2=download2(urllist2)

images=[]
linklist=[]
def MakeWindow(pick_recipe_list,key_amount,key_ingredient,file_name_list,wh):
    for i in range(len(pick_recipe_list)):
        for name in pick_recipe_list[i]["ingredient"]:
            if bool(re.findall(name,ingredient_dictlist[key_number-1]["name"]))==True:
                key2=name
                amount=pick_recipe_list[i]['ingredient'][name]#dataの材料の辞書の中の指定された材料の量を取り出す
        #何日目か表示
        font0=font.Font(size=15)
        day=tk.Label(frame,text="{0}日目".format(i+1),font=font0,fg="#FF0000")
        day.grid(row=1,column=i+1)
        #レシピ名の表示
        font1=font.Font(size=15)
        recipe_name=tk.Label(frame,text="【{0}】".format(pick_recipe_list[i]['recipe_name']),font=font1,fg="#008000")
        recipe_name.grid(row=2,column=i+1)
        #画像の表示
        img=Image.open(file_name_list[i])
        img=img.resize((300,300))
        img=ImageTk.PhotoImage(img)
        images.append(img)
        cv=tk.Canvas(frame,bg="white",width=300,height=300)
        cv.grid(row=3,column=i+1)
        cv.create_image(0,0,image=img,anchor=tk.NW)
        #リンクの表示
        font2=font.Font(size=10)
        def cleateButton(url,i):
            link = tk.Label(frame, text=f'{url}', fg="blue", cursor="hand2",font=font2)
            link.grid(row=4,column=i+1)
            button = link.bind('<Button-1>',  lambda e: callback(url))
        cleateButton(pick_recipe_list[i]["recipe_url"],i)        #レシピの材料表示
        font3=font.Font(size=15)
        ing=tk.Label(frame,text="{0}：{1} /{2} g".format(key_ingredient,amount,key_amount),font=font3)
        ing.grid(row=5,column=i+1)


images_2=[]
linklist_2=[]
def MakeWindow2(pick_recipe_list,key_amount,key_ingredient,file_name_list,wh):
    for i in range(len(pick_recipe_list)):
        for name in pick_recipe_list[i]["ingredient"]:
            if bool(re.findall(name,ingredient_dictlist[key_number-1]["name"]))==True:
                key3=name
                amount=pick_recipe_list[i]['ingredient'][name]#dataの材料の辞書の中の指定された材料の量を取り出す
        # key=pick_recipe_list[i]["key"]
        #おまけの表示
        font0=font.Font(size=15)
        day=tk.Label(frame,text="おススメの作り置きレシピ{0}".format(i+1),font=font0,fg="#FF0000")
        day.grid(row=7,column=i+1)
        #レシピ名の表示
        font1=font.Font(size=15)
        recipe_name=tk.Label(frame,text="【{0}】".format(pick_recipe_list[i]['recipe_name']),font=font1,fg="#008000")
        recipe_name.grid(row=8,column=i+1)
        #画像の表示
        img=Image.open(file_name_list[i])
        img=img.resize((300,300))
        img=ImageTk.PhotoImage(img)
        images.append(img)
        cv=tk.Canvas(frame,bg="white",width=300,height=300)
        cv.grid(row=9,column=i+1)
        cv.create_image(0,0,image=img,anchor=tk.NW)
        #リンクの表示
        font2=font.Font(size=10)
        def cleateButton(url,i):
            link2 = tk.Label(frame, text=f'{url}', fg="blue", cursor="hand2",font=font2)
            link2.grid(row=10,column=i+1)
            button = link2.bind('<Button-1>',  lambda e: callback(url))
        cleateButton(pick_recipe_list[i]["recipe_url"],i)
        #レシピの材料表示
        font3=font.Font(size=15)
        ing=tk.Label(frame,text="{0}：{1} /{2} g".format(key_ingredient,amount,key_amount),font=font3)
        ing.grid(row=11,column=i+1)

#メインのウィンドウの作成
window = tk.Tk()
window.title("おススメレシピ")
window.geometry("600x600")
# Canvas Widget を生成
canvas = tk.Canvas(window,width = 3000, height = 1000)

# スクロール を生成して配置
scroll_y= tk.Scrollbar(window, orient=tk.VERTICAL)
scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
scroll_y.config(command=canvas.yview)

scroll_x= tk.Scrollbar(window, orient=tk.HORIZONTAL)
scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
scroll_x.config(command=canvas.xview)

# Canvas Widget を配置
canvas.config(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
canvas.config(scrollregion=(0,0,2000,2000)) #スクロール範囲
canvas.pack(side=tk.LEFT, fill=tk.BOTH)

# Frame Widgetを 生成
frame = tk.Frame(canvas)

# Frame Widgetを Canvas Widget上に配置
canvas.create_window((0,0), window=frame, anchor=tk.NW, width=3000,height=1000)

MakeWindow(pick_recipe_list,key_amount,key_ingredient,file_name_list,wh)
if len(pick_recipe_list_omake)!=0:
    MakeWindow2(pick_recipe_list_omake,key_amount,key_ingredient,file_name_list2,wh2)

window.mainloop()
