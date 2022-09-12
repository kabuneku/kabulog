import sys
import time
import pandas as pd
import numpy as np
#from yahoo_finance_api2 import share
#from yahoo_finance_api2.exceptions import YahooFinanceError
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os
#import plotly.io as pio
#import talib as ta
"""
pio.kaleido.scope.default_format = "png"  # デフォルトは "png" #画像保存のデフォルト設定
#pio.kaleido.scope.default_width  = 1326    # デフォルトは 700
pio.kaleido.scope.default_width  = 1278    # デフォルトは 700
#pio.kaleido.scope.default_height = 848    # デフォルトは 500
pio.kaleido.scope.default_height = 1071    # デフォルトは 500

def date_timedelta() :
    now=datetime.datetime.now()
    if now.weekday() ==5 : #Sat のときは-1
        timedelta = -1
    elif now.weekday() == 6 : #Sun
        timedelta = -2
    else :
        if 0 <= now.hour <= 8 :  # 平日寄り付き前限定
            if now.weekday() == 0: # Mon の寄り付き前は -3
                timedelta = -3
            else :
                timedelta = -1
        else :
            timedelta = 0
    date = now.date()+datetime.timedelta(days = timedelta)
    return date

def get_histricaldata(freq, y_period, code):
    my_share = share.Share(code)
    symbol_data = None

    try:
        if freq == "d" :
            symbol_data = my_share.get_historical(
                share.PERIOD_TYPE_YEAR,y_period ,
                share.FREQUENCY_TYPE_DAY, 1)
        else :
            symbol_data = my_share.get_historical(
                share.PERIOD_TYPE_YEAR,y_period ,
                share.FREQUENCY_TYPE_WEEK, 1)
    except YahooFinanceError as e:
        print(e.message)
        #sys.exit(1)
    df= pd.DataFrame(symbol_data)
    if df.empty == False :
        df["timestamp"] = df["timestamp"]#+9*60*60*10**3
        df["datetime"] = pd.to_datetime(df.timestamp, unit="ms")
    return df

def EMA (df ,*args) :
     Name_list = []
     for i in args:
         df[f"EMA{i}"] = df["close"].ewm(span=i).mean()
         Name_list.append(f"EMA{i}")
     return Name_list

def SMA_V (df, *args) :
    for i in args :
        df[f"V_{i}"] = df["volume"].rolling(i).mean()

def SMA(df,*args):
    Name_list = []
    for i in args :
        df[f"SMA{i}"] = df["close"].rolling(i).mean()
        Name_list.append(f"SMA{i}")
    return Name_list

def DEMA ( df , *args) :
    for i in args:
        df[f"DEMA{i}"] = 2*df[f"EMA{i}"] - df[f"EMA{i}"].ewm(span=i).mean()
    return df

def MACD ( df ) :
    EMA (df, 12, 26 )
    DEMA ( df, 12, 26 )
    df["MACD"] = df["DEMA12"] - df["DEMA26"]
    #df["MACD_Signal"] = df["MACD"].rolling(9).mean()   #Signal を単純平均で計算
    df["MACD_Signal"] = df["MACD"].ewm(span=9).mean() #Signal を指数平滑化で計算
    df["MACD_H"] = df["MACD"] - df["MACD_Signal"]
    Name_list = ["MACD", "MACD_Signal", "MACD_H"]
    return Name_list
 
def MACD_W ( df ) :   #週足スケールのMACDを日足グラフに再現 1W = 5D
    EMA (df, 60, 130 )
    DEMA (df, 60, 130 )
    df["MACD_W"] = df["DEMA60"] - df["DEMA130"]
    df["MACD_W_Signal"] = df["MACD_W"].ewm(span = 45).mean()
    df["MACD_W_H"] = df["MACD_W"] - df["MACD_W_Signal"]
    return ["MACD_W", "MACD_W_Signal", "MACD_W_H"]

def trend_checker ( df ) :
    close_max_10_list = []
    close_min_10_list = []
    for i in range(len(df)) :
        if i < 9 :
            close_max_10_list.append(np.nan)
        else :        
            max_10 = df["close"][i-9:i+1].max()
            close_max_10_list.append(max_10)
        
    for i in range(len(df)):
        if i < 9 :
            close_min_10_list.append(np.nan)
        else:
            min_10 = df["close"][i-9:i+1].min()
            close_min_10_list.append(min_10)
    df["max_10"] = close_max_10_list
    df["min_10"] = close_min_10_list
    df["diff_max_10"] = df["max_10"] - df["min_10"]
    df["ATR"] = ta.ATR(df["high"], df["low"],df["close"])
    df["trend_checker"] = df["diff_max_10"] / df["ATR"]
        

def MI (df,span, rollingspan):
    #df["upEMA"] = df["up"].ewm(span = span).mean() 
    #df["downEMA"] = df["down"].ewm(span =span).mean() 
    #df["MI"] = df["upEMA"] - df["downEMA"]
    df["MI"] = ( df["up"] - df["down"] ).ewm(span=span).mean()  #デフォは200
    df["MI_S"] = df["MI"].rolling(rollingspan).mean() #だいたい10か9 → NHLI と同じ25→50
    df["MI_H"] = df["MI"] - df["MI_S"]
    Name_list = ["MI", "MI_S", "MI_H"]
    return Name_list

def NHLI (df, span, rollingspan ) :
    df["NHLI"] = (df["N_H"] - df["N_L"]).ewm(span =span).mean() #50ぐらい
    df["NHL_S"] = df["NHLI"].rolling(rollingspan).mean() # 25
    df["NHL_H"] = df["NHLI"] - df["NHL_S"]
    Name_list = ["NHLI", "NHL_S", "NHL_H"]
    return Name_list

def VI_Inverse (df ) :
    df["VI_I"] = df["close"]*(-1)
    return df

def RS(df,df2 , span):  #rollingspan=33 ぐらい？
    df["RS"] = df["close"] / df2["close"]
    df["RS_S"] = df["RS"].rolling(span).mean()  #単純移動平均，指数とどちらが良いか？
    #df["RS_S"] = df["RS"].ewm(span = span).mean()  #単純移動平均，指数とどちらが良いか？
    #df["RS_H"] = df["RS"] - df["RS_Signal"]
    return ["RS", "RS_S"] #RS_Singnal は長すぎた

def RS_1(df,df2 , span1, span2):  #rollingspan=33 ぐらい？
    df["RS_1"] = df["close"] / df2["close"]
    #df[f"RS_S_1"] = df["RS_1"].rolling(span).mean()  #単純移動平均，指数とどちらが良いか？
    df[f"RSE{span1}"] = df["RS_1"].ewm(span = span1).mean()  #単純移動平均，指数とどちらが良いか？
    df[f"RSE{span2}"] = df["RS_1"].ewm(span = span2).mean()  #単純移動平均，指数とどちらが良いか？
    #df["RS_S"] = df["RS"].ewm(span = span).mean()  #単純移動平均，指数とどちらが良いか？
    #df["RS_H"] = df["RS"] - df["RS_Signal"]
    #return ["RS_1", "RS_S_1"] #RS_Singnal は長すぎた
    return ["RS_1", f"RSE{span1}",f"RSE{span2}"] #RS_Singnal は長すぎた

def RS_2 ( df, df2, span1,span2) :
    df["RS_2"] = df["close"] / df2["close"]
    #df["RS_S_2"] = df["RS_2"].rolling(span).mean()
    df[f"R2E{span1}"] = df["RS_2"].ewm(span = span1).mean()  #単純移動平均，指数とどちらが良いか？
    df[f"R2E{span2}"] = df["RS_2"].ewm(span = span2).mean() 
    return ["RS_2",  f"R2E{span1}",f"R2E{span2}"]

def RS_3 ( df, df2, span1,span2) :
    df["RS_3"] = df["close"] / df2["close"]
    #df["RS_S_3"] = df["RS_3"].rolling(span).mean()
    df[f"R3E{span1}"] = df["RS_3"].ewm(span = span1).mean()  #単純移動平均，指数とどちらが良いか？
    df[f"R3E{span2}"] = df["RS_3"].ewm(span = span2).mean() 
    return ["RS_3", f"R3E{span1}",f"R3E{span2}"]
"""
def set_Cdata(df,name,ilcolor,dlcolor,ifcolor,dfcolor):
    d = go.Candlestick(x =df["datetime"], close=df["close"],
                       open=df["open"], high = df["high"], low = df["low"],
                       increasing_line = dict(color =ilcolor, width = 0.75),
                       decreasing_line = dict(color = dlcolor,width=0.75),
                       increasing_fillcolor = ifcolor, decreasing_fillcolor = dfcolor,
                       opacity = 1,name=name)
    return d

def plot_Candle(fig,df,name,row,col):
        d = set_Cdata(df,name, "black","black","white","black")
        fig.add_trace(d,row=row, col=col)
        
def D2W (df,**kwarg) :  #日足データを週足に変換して返す
    df["datetime"] = pd.to_datetime(df["datetime"]) # 日付け化
    df = df.set_index("datetime")
    agg_dict = kwarg
    df = df.resample("W").agg(agg_dict)
    df = df.dropna() # 2019GW期間の NaN列を削除
    df = df.reset_index()
    return df

def D2M (df,**kwarg):
    df["datetime"] = pd.to_datetime(df["datetime"]) # 日付け化
    df = df.set_index("datetime")
    agg_dict = kwarg
    df = df.resample("M").agg(agg_dict)
    #df = df.dropna() # 2019GW期間の NaN列を削除
    df = df.reset_index()
    return df

def D2M_v2 (df,col_date, **kwarg) :
    df[col_date] = pd.to_datetime(df[col_date])
    df = df.set_index(col_date)
    agg_dict = kwarg
    df = df.resample("M").agg(agg_dict)
    df = df.reset_index()
    return df

def set_Sdata (df, x, y,color ):
    d = go.Scatter(x = df[x], y = df[y], name=y, marker = dict(color=color),
                   )
    return d

def plot_Scatter (fig,df, x, y,  color, row, col):
    d = set_Sdata(df, x, y,  color )
    fig.add_trace( d, row = row, col = col )

def set_Mdata(df,x,y,color):
    d = go.Scatter(x = df[x],y = df[y], name=y,mode = "markers",
                   marker = dict(size = 12, color = color))
    return d

def plot_Marker(fig,df,x,y,color,row,col):
    d = set_Mdata(df,x,y,color)
    fig.add_trace(d,row=row, col = col)

def set_Bdata ( df, x, y, color ) :
    d = go.Bar ( x = df[x], y = df[y], name = y, marker = dict(color = color))
    return d

def plot_Bar ( fig,df, x, y, color, row, col ) :
    d = set_Bdata ( df, x, y,  color )
    fig.add_trace ( d, row = row, col = col )

def save_fig (fig,path, fname) :  #path はフォルダ名まで, fname は日付け，拡張子なしで
    #now = datetime.datetime.now()
    #date = now.date()
    date = date_timedelta()
    if os.path.exists(path) == False :
        os.mkdir(path)
    fig.write_image(path+"/"+fname+"_"+str(date)[:-3]+".png")


def date_break ( fig,df ) :
    df["datetime"] = pd.to_datetime(df["datetime"])
    d_all = pd.date_range(start=df['datetime'].iloc[0],end=df['datetime'].iloc[-1]) #営業日だけ表示
    d_obs = [d.strftime("%Y-%m-%d") for d in df['datetime']]
    d_breaks = [d for d in d_all.strftime("%Y-%m-%d").tolist() if not d in d_obs]
    fig.update_xaxes(rangebreaks=[dict(values=d_breaks)])

def fig_update_axes (fig) :
    fig.update_xaxes(rangeslider_visible = False, showgrid = False)
    fig.update_yaxes(gridcolor = "grey", tickcolor = "grey", linecolor="grey",
                     zerolinecolor = "grey")

def fig_update_layout (fig, titletext):
    fig.update_layout(
        title = dict(text= "<b>"+titletext,
                     font = dict(size=26, color = "grey"), y = 0.965 ), #0.95から修正．
        #dragmode = "drawopenpath", #ドラッグでいつでもフリーな線を引ける
        newshape_line = dict(color = "black",width = 1.5),
        plot_bgcolor = "#DCE3EF",paper_bgcolor = "papayawhip",
        )


def config() :
    config = dict(
                   {"scrollZoom":True,
                    'doubleClickDelay': 1000,
        "modeBarButtonsToAdd": [
        'drawline',  # 直線
        'eraseshape',  # 図形の削除
        'toggleSpikelines',  # ホバーしたプロットに垂直・水平な線
        'hoverclosest',  # 直近のプロット1点をホバー
        'hovercompare',  # 直近のプロットと同じxのプロット全点をホバー
    ]}
                  )
    return config

def get_sequence(series,x):

    zone = [[]]
    flag = 0
    if x == "red":
        N = 2
    elif x=="green":
        N = 0
    elif x=="blue" :
        N = -2
    Flag = []
    #print(x)
    for num, i in enumerate(series):
        
            if num != len(series)-1 :
                if i == N:
                    if  flag == 0 :
                        if num != 0 :
                             zone[-1].append(num-1)
                        else :
                             zone[-1].append(num)
                        flag=1
                        #Flag.append(flag)
                    #else:
                        #Flag.append(flag)
                else :
                    if flag == 1:
                         zone[-1].append(num-1)
                         zone.append([])
                         flag=0
                         #Flag.append(flag)
                    #else:
                        #Flag.append(flag)
            else :
                if i ==N:
                    if flag == 1:
                         zone[-1].append(num)
                         flag=0
                         #Flag.append(flag)
                    else :
                        zone[-1].append(num-1)
                        zone[-1].append(num)
                        flag=0
                        #Flag.append(flag)
                else:
                    if flag == 1:
                        zone[-1].append(num-1)
                        flag=0
                        #Flag.append(flag)
                    #else:
                        #Flag.append(flag)
    #DataFrame = pd.DataFrame({"IS":df["IS"],"Flag":Flag})
    #print(DataFrame)
    #DataFrame.to_csv("check.csv")
    zone = list(filter(None, zone))
    #print( f"zone_{x}")
    return  zone

def vrect(x0,x1,fillcolor = "red",opacity=0.2, width=0, color = None,layer="below"):
    dct = dict(x0=x0, x1 = x1, fillcolor = fillcolor, opacity = opacity,
               line = dict(width = width, color =color), layer = layer)
    return dct

def fill_vertical(fig,row,col,*args):
    for kwarg in args:
        fill = vrect(**kwarg)
        fig.add_vrect(**fill,row=row,col=col)   #こいつの処理にめちゃくちゃ時間がかかる

def select_fill(fig,df,row,col):
    ZONE = {}
    for i in ["red", "green", "blue"]:
        ZONE[f"zone_{i}"] = get_sequence(df["IS"],i)
        ans = []
        #print(ZONE)
        q_date = df.loc[int(len(df) - len(df) / 4 ),"datetime"]
        for x0,x1 in ZONE[f"zone_{i}"][int(1*len(ZONE[f"zone_{i}"])/2):len(ZONE[f"zone_{i}"])]:
        #for x0,x1 in ZONE[f"zone_{i}"]:
            if q_date < df.loc[x0,"datetime"] :
                fill = dict(x0 =df.loc[x0,"datetime"], x1 = df.loc[x1,"datetime"], opacity=0.2,
                            layer="below",  ##DCE3EF
                            fillcolor = i)   #塗りつぶしの描画時間短縮のため 3/4 カットしている↑
                ans.append(fill)
        #print(ans)
        fill_vertical(fig,row,col,*ans)
        #fill_vertical(**fill)
def check(x):
    if x >= 0 :
        x = 1
    else :
        x = -1
    return  x

def diff (df,x) :
    df[f"{x}_diff"] = df[f"{x}"].diff()
    return df
def diff_b (df,x,b) :  #b = before
    df[f"{x}_diff{b}"] = df[f"{x}"].diff(b)
    return df
def IS (df):
    MACD(df)
    diff(df,"EMA22")
    diff(df,"MACD_H")
    df["EMA22_diff"] = df["EMA22_diff"].apply(check)
    df["MACD_H_diff"] = df["MACD_H_diff"].apply(check)
    df["IS"] = df["EMA22_diff"] + df["MACD_H_diff"]
    return df

def get_Sctdata (Sct_code, Sct_name) : #,timedelta):
    baseUrl = "https://kabutan.jp/stock/?code=0"+str(Sct_code) #水産・農林業
    S = pd.read_html(baseUrl,match="始値")
    L = S[0]
    M = L[[0,1]]
    M = M.transpose() #行と列を入れ替え
    M.columns = ["open", "high", "low", "close" ]
    M=M.drop(0)
    M = M.reset_index(drop = True)
    #print(M)
    now = datetime.datetime.now()
    if now.weekday() ==5 : #Sat のときは-1
        timedelta = -1
    elif now.weekday() == 6 : #Sun
        timedelta = -2
    else :
        if 0 <= now.hour <= 8 :  # 平日寄り付き前限定
            if now.weekday() == 0: # Mon の寄り付き前は -3
                timedelta = -3
            else :
                timedelta = -1
        else :
            timedelta = 0
    
    date = now.date()+datetime.timedelta(days = timedelta)
    date_string = date.strftime("%Y-%m-%d") #日付けデータを年月日表示にする
    M["datetime"] = date_string
    M = M.reindex(columns = ["datetime", "close", "open", "high", "low"]) #株探から最新データ取得
    df = pd.read_csv("Backup_33/"+Sct_name+"_D.csv")  #バックアップのものを読む
    df = df.append(M,ignore_index = True)  #過去データに最新データを下にくっつける
    return df


def get_CVtable(V,num,minvolume_man): #volume の単位は万
    baseUrl = V.loc[num,"URL"]
    S = pd.read_html(baseUrl)
    L = S[0]
    M =L.loc[:,["証券コード","売買高（株）"]]
    M = M.set_axis(["code","volume"],axis = 1)
    drop_index = M.index[M['volume'] < minvolume_man*10000]  #出来高が20万未満を除く
    M = M.drop(drop_index)
    return M

def minvolume():  #プログラムを走らせる時間によって出来高最低ラインを変える
    now = datetime.datetime.now()
    hour = now.hour
    if 9 <= hour <=13 :
        minvolume = 10
    elif 13 < hour <= 14 :
        minvolume = 15
    else :
        minvolume = 20
    return minvolume

def maxprice():  #自身の資産状況によって増減させる
    return 4000

def sleeptime():
    now = datetime.datetime.now()
    hour = now.hour
    """
    if 22 <= hour <= 6 :
        sleeptime = 2
    else:
        sleeptime = 0.5
    """
    sleeptime=1.0#0.5
    return sleeptime
    
def str2date2str ( x ) :  #株探で使用
    date_str = x
    date_dt = datetime.datetime.strptime(date_str, '%y/%m/%d')
    date_dt = pd.to_datetime(date_dt)
    date = str(date_dt)[:-9]
    return date


    
    



