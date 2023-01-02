import streamlit as st
import pandas as pd

#bokehグラフ
from bokeh.plotting import figure, show
from bokeh.io import export_png

##df_calc編集関数
def df_calc_edit(df_calc,date,date1):      
    try:
        df_calc = df_calc[['社員番号','入金','集計','朝','売場','新人',date,date1]]
    except KeyError:
        st.write('指定した日付が範囲外です')
    #欠損値(出勤しない人)を消す
    df_calc = df_calc.dropna(subset=[date])
    
    #データ型をfloatにそろえる
    s = df_calc[date]
    s1 = df_calc[date1]
    s =s.astype('float64')
    s1 =s1.astype('float64')
    df_calcs=pd.concat([s,s1],axis=1)
    df_calc = pd.concat([df_calcs,df_calc[['社員番号','入金','集計','朝','売場','新人']]],axis=1)

    #index列作成
    df_calc['index'] = df_calc.index

    #拘束時間、最少休憩時間、労働時間計算
    df_calc['拘束時間'] = df_calc[date1] - df_calc[date]
    rest_list=[]
    for p in df_calc['index']:
        if df_calc.at[p,'拘束時間']<=4.5: #4.5以下なら休憩時間なし
            rest_list.append(0)
        elif df_calc.at[p,'拘束時間']<=9: #9時間以内なら1時間
            rest_list.append(1)
        else:
            rest = df_calc.at[p,'拘束時間']-8 #それ以外、Fとかは8時間引いた分
            rest_list.append(rest)
    df_calc['最少休憩時間']=rest_list
    df_calc['労働時間']= df_calc['拘束時間']- df_calc['最少休憩時間']
    df_calc['当番'] = '-'
    return df_calc

#スライダーによる拘束時間、休憩時間編集
def rest_edit(df_calc,date,date1):
    with st.sidebar:
        df_calc['休憩開始1']=0
        df_calc['休憩終了1']=0
        df_calc['休憩開始2']=0
        df_calc['休憩終了2']=0
        for i,t,a,b,c,d in zip(df_calc['index'],df_calc['最少休憩時間'],df_calc[date],df_calc[date1],df_calc['拘束時間'],df_calc['新人']):
            #if t != 0.0:    #これを入れると最少休憩時間0分の人は除外される
            ex = st.expander(i+'　最少休憩時間：'+str(t)+'　拘束時間:'+str(c) if d!=1 else i+'（新人）'+'　最少休憩時間：'+str(t)+'　拘束時間:'+str(c))

            if ex.checkbox('拘束時間',key=i+'job'):
                jobtime = ex.slider('拘束時間編集',max_value=a,min_value=b,value=(a,b),step=0.5,key='拘束'+i)
                df_calc.at[i,date] = jobtime[0]
                df_calc.at[i,date1] = jobtime[1]
                df_calc.at[i,'拘束時間'] = jobtime[1] - jobtime[0]  #拘束時間更新
            
            if ex.checkbox('休憩時間1',key=i+'rest1'):
                resttime = ex.slider('休憩時間編集',max_value=a,min_value=b,value=(a,b),step=0.5,key='休憩1'+i)
                df_calc.at[i,'休憩開始1'] = resttime[0]
                df_calc.at[i,'休憩終了1'] = resttime[1]
            
            if ex.checkbox('休憩時間2',key=i+'rest2'):
                resttime = ex.slider('休憩時間編集',max_value=a,min_value=b,value=(a,b),step=0.5,key='休憩2'+i)
                df_calc.at[i,'休憩開始2'] = resttime[0]
                df_calc.at[i,'休憩終了2'] = resttime[1]

            df_calc.at[i,'休憩時間1'] = df_calc.at[i,'休憩終了1'] - df_calc.at[i,'休憩開始1']
            df_calc.at[i,'休憩時間2'] = df_calc.at[i,'休憩終了2'] - df_calc.at[i,'休憩開始2']
            df_calc.at[i,'労働時間'] = df_calc.at[i,'拘束時間'] - df_calc.at[i,'休憩時間1'] - df_calc.at[i,'休憩時間2']

    return df_calc 

#17時以降の労働時間集計
def separate_17(df_calc,date,date1):
    df_calc['~17時']=0
    df_calc['17時~']=0
    #拘束時間で分ける
    for i,x1,x2,a in zip(df_calc['index'],df_calc[date],df_calc[date1],df_calc['拘束時間']):
        if x2<17 :#退勤が17時前
            df_calc.at[i,'~17時'] = a
        elif x1>17 : #出勤が17時あと
            df_calc.at[i,'17時~'] = a
        else:   
            df_calc.at[i,'~17時'] = 17-x1
            df_calc.at[i,'17時~'] = x2-17
    
    ##休憩時間引き算
    def minus_resttime(df_calc,times):
        for i,y1,y2,b17,a17,a in zip(df_calc['index'],df_calc['休憩開始'+times],df_calc['休憩終了'+times],df_calc['~17時'],df_calc['17時~'],df_calc['休憩時間'+times]):
            if y1 != 0:
                if y2<17 : #休憩時間が17時前の時
                    df_calc.at[i,'~17時'] = b17-a
                elif y1>17 : #休憩時間が17時以降の時
                    df_calc.at[i,'17時~'] = a17-a
                else:
                    df_calc.at[i,'~17時'] = b17 - (17-y1)
                    df_calc.at[i,'17時~'] = a17 - (y2-17)
        return df_calc

    df_calc = minus_resttime(df_calc,'1')    #休憩時間1を引き算
    df_calc = minus_resttime(df_calc,'2')    #休憩時間2を引き算
            
    return df_calc

##出勤時間グラフ作成関数
def make_graph(df_calc,date,date1,height):
    p = figure(y_range=df_calc['index'], x_range=(8,21), width=723, height=height, toolbar_location=None,title="シフト")
    p.hbar(y=df_calc['index'], left=df_calc[date], right=df_calc[date1], height=0.1,line_width=10)  #拘束時間グラフ
    p.hbar(y=df_calc['index'], left=df_calc['休憩開始1'], right=df_calc['休憩終了1'], height=0.1,line_width=10,color='white')  #休憩時間グラフ
    p.hbar(y=df_calc['index'], left=df_calc['休憩開始2'], right=df_calc['休憩終了2'], height=0.1,line_width=10,color='white')  #休憩時間グラフ

    p.ygrid.grid_line_color = None
    p.xaxis.axis_label = "勤務時間"
    p.xaxis.major_label_text_font_size = '20px'
    p.yaxis.major_label_text_font_size = '20px'
    p.outline_line_color = None
    #罫線のスタイル
    p.xaxis.bounds = (8,22)
    p.xaxis.ticker.max_interval=1
    p.xaxis.ticker.num_minor_ticks = 2
    p.xgrid.minor_grid_line_color = 'black'
    p.xgrid.minor_grid_line_dash = [6,4]
    p.xgrid.minor_grid_line_alpha = 0.1
    
    return p

#当番選択関数
def define_role(df_calc,df_calc_s,role,date,border):
    st.write(role + 'メンバー')
    df_role = df_calc[[role,'index']]
    df_role = df_calc[df_calc[role]==1]
    df_role_s = df_calc_s[[role,'index']]
    df_role_s = df_calc_s[df_calc_s[role]==1]
    role_list = []
    
    for y in df_role['index']:
        if df_calc.at[y,date] == border:   #出勤時間がborder時の人だけ抽出
            if st.checkbox(str(y),key=role+y):
                role_list.append(y)
                df_calc.at[y,'当番']=role
    for y in df_role_s['index']:
        if df_calc_s.at[y,date] == border:
            if st.checkbox(str(y),key=role+y):
                role_list.append(y)
                df_calc_s.at[y,'当番']=role
    return role_list

#csvコンバーター
def convert_df(df):
    return df.to_csv().encode('Shift-JIS')