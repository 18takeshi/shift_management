##ファイル読み込み
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
#bokehグラフ
from bokeh.plotting import figure
#関数ファイル
import function as fun
import makepdf as mp
#基本シフト表
df_kihon = pd.read_excel('基本シフト表集計.xlsx',index_col=0)

st.title('シフト作成アプリ')
st.caption('ver1.02 2023/3/09') 

##シフト表アップロード
uploaded_file = st.file_uploader("勤務シフト表をアップロードしてください", type='xlsx')
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file,index_col=0)
    
    df = df.drop('出退勤')

    #日付
    d = st.date_input("作成するシフトの日付",datetime.now())

    #日だけを取り出す
    date = d.strftime('%d')
    date = int((date))
    date1 = float(date)+0.1
    
    #当日出勤df編集
    df_calc = df.query('社員!=1 and 契約社員!=1') #社員以外
    df_calc_s = df.query('社員==1 | 契約社員==1')   #社員,契約社員

    #df_calc_edit関数で編集
    df_calc = fun.df_calc_edit(df_calc,date,date1)
    df_calc_s = fun.df_calc_edit(df_calc_s,date,date1)

    st.header(str(d)+"シフト編集")
    #出勤しない人選択エキスパンダー
    expander = st.expander('出勤しない人選択')
    for i,r in zip(df_calc['index'],df_calc['新人']):
        if expander.checkbox(str(i) if r!=1 else str(i)+'（新人）',key=i+'in'):
            df_calc = df_calc.drop(i)
    for i in df_calc_s['index']:
        if expander.checkbox(str(i),key=i+'in'):
            df_calc_s = df_calc_s.drop(i)

    #社員以外出勤時間分ソート
    df_calc = df_calc.sort_values(date,ascending=True)

    #拘束時間、休憩時間編集スライダー
    st.sidebar.write('休憩時間編集')
    df_calc = fun.rest_edit(df_calc,date,date1)
    st.sidebar.write('社員編集')
    st.sidebar.caption('※仕様上,レジに入らない労働時間も不足グラフに反映されます')
    df_calc_s = fun.rest_edit(df_calc_s,date,date1)
    
    #グラフとサイドバー合わせるためにもう一回ソート
    df_calc = df_calc.sort_values(date,ascending=False)
    #グラフで不足さんを下に持ってくるためにdf_calc編集
    df_calc_f = df_calc.query("時給==0")
    df_calc_b = df_calc.query("時給!=0")
    df_calc = pd.concat([df_calc_f,df_calc_b])

    #make_graph関数でグラフ作成
    p = fun.make_graph(df_calc,date,date1,1100)
    ps = fun.make_graph(df_calc_s,date,date1,200)

    #タブ化
    taba,tabb,tabc,tabd = st.tabs(['シフトグラフ','不足確認グラフ','役割選択','帳票出力'])

    with taba:
        st.bokeh_chart(p, use_container_width=True)
        st.bokeh_chart(ps, use_container_width=True)

    #時間別集計
    ind = np.arange(8,22,0.5)
    df_syukei = pd.DataFrame(columns=['集計'],index=ind)
    df_syukei = df_syukei.fillna(0)

    df_nonew = df_calc[df_calc['新人'] != 1] 
    df_new = df_calc[df_calc['新人'] == 1]
    df_beteran = pd.concat([df_nonew,df_calc_s],axis=0) #ベテラン(新人でない人全部)は不足グラフに反映する

    sum_staff = df_nonew['労働時間'].sum()
    sum_new = df_new['労働時間'].sum()

    #社員と契約社員分ける
    df_s = df_calc_s.query('契約社員!=1')
    df_con = df_calc_s.query('契約社員==1')
    sum_s = df_s['労働時間'].sum()
    sum_con = df_con['労働時間'].sum()

    total_work = sum_staff + sum_new + sum_s + sum_con

    st.header('労働時間集計')
    st.write('スタッフ労働時間合計：'+str(sum_staff))
    st.write('社員労働時間合計：'+str(sum_s))
    #st.write('契約社員労働時間合計：'+str(sum_con))
    st.write('新人労働時間合計：'+str(sum_new))
    st.write('合計労働時間：'+str(total_work))

    for t in ind:   #勤務時間を集計
        for s,f in zip(df_beteran[date],df_beteran[date1]):
            if s<=t and t<f:
                df_syukei.at[t,'集計'] = df_syukei.at[t,'集計']+1
    
    for t in ind:   #休憩時間を集計して減算
        for s,f in zip(df_beteran['休憩開始1'],df_beteran['休憩終了1']):
            if s<=t and t<f:
                df_syukei.at[t,'集計'] = df_syukei.at[t,'集計']-1

    for t in ind:   #休憩時間を集計して減算
        for s,f in zip(df_beteran['休憩開始2'],df_beteran['休憩終了2']):
            if s<=t and t<f:
                df_syukei.at[t,'集計'] = df_syukei.at[t,'集計']-1

    week = d.strftime('%a')
    df_syukei['基本シフト'] = df_kihon[week]
    df_syukei['不足'] = df_syukei['集計'] - df_syukei['基本シフト']
    df_syukei['index'] = df_syukei.index

    ##不足ヒストグラム作成p1
    p1 = figure(height=350, width=362 ,x_range=(8,21), title="不足確認グラフ", toolbar_location=None)
    p1.vbar(x=df_syukei['index'], top=df_syukei['不足'], width=0.3)
    p1 = fun.husoku_edit(p1)

    with tabb:
        st.caption('仕様上、新人は不足グラフには反映されません')
        st.bokeh_chart(p1, use_container_width=True)

    with tabc:
        column1, column2, column3 ,column4 = st.columns(4)
        with column1:
            fun.define_role(df_calc,df_calc_s,'朝',date,8.5)
        with column2:
            fun.define_role(df_calc,df_calc_s,'売場',date1,20.5)
        with column3:
            fun.define_role(df_calc,df_calc_s,'入金',date1,20.5)
        with column4:
            fun.define_role(df_calc,df_calc_s,'集計',date1,20.5)
    
    with tabd:
        st.header('最終確認')
        st.checkbox('すべての時間帯で後方が存在しますか？')
        st.checkbox('連続労働時間が5時間を超えるスタッフはいませんか？')
        shift = fun.png_upload('シフトグラフをアップロードしてください')
        shain = fun.png_upload('社員シフトグラフをアップロードしてください')
        
        st.caption('※すべてのファイルをアップロードしてからOKを押してください')
        if st.button('OK'):
            mp.makepdf(df_calc,df_calc_s,d,sum_staff,sum_s,sum_con,total_work,sum_new,shift,shain,date,date1)