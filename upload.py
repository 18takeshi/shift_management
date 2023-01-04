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

st.title('ベルーフ静岡店 シフト作成アプリ')
st.caption('ver1.0 2023/1/4') 

##シフト表アップロード
uploaded_file = st.file_uploader("勤務シフト表をアップロードしてください", type='xlsx')
if uploaded_file is not None:
    df = pd.read_excel(uploaded_file,index_col=1)
    df = df.drop('出退勤')

    #日付
    d = st.date_input("作成するシフトの日付",datetime.now())

    #日だけを取り出す
    date = d.strftime('%d')
    date = int((date))
    date1 = float(date)+0.1
    
    #当日出勤df編集
    df_calc = df[df['社員']!=1]     #社員以外
    df_calc_s = df[df['社員']==1]   #社員

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
    df_calc = df_calc.sort_values(date,ascending=False)

    #拘束時間、休憩時間編集スライダー
    st.sidebar.write('休憩時間編集')
    df_calc = fun.rest_edit(df_calc,date,date1)
    st.sidebar.write('社員編集')
    st.sidebar.caption('※仕様上,レジに入らない労働時間も不足グラフに反映されます')
    df_calc_s = fun.rest_edit(df_calc_s,date,date1)
      
    #make_graph関数でグラフ作成
    p = fun.make_graph(df_calc,date,date1,1023)
    ps = fun.make_graph(df_calc_s,date,date1,200)

    #タブ化
    taba,tabb,tabc,tabd,tabe = st.tabs(['シフトグラフ','不足確認グラフ','出勤データ','役割選択','帳票出力'])

    with taba:
        st.bokeh_chart(p, use_container_width=True)
        st.bokeh_chart(ps, use_container_width=True)

    #時間別集計
    ind = np.arange(8,22,0.5)
    df_syukei = pd.DataFrame(columns=['集計'],index=ind)
    df_syukei = df_syukei.fillna(0)

    df_nonew = df_calc[df_calc['新人'] != 1] 
    df_new = df_calc[df_calc['新人'] == 1]
    df_beteran = pd.concat([df_nonew,df_calc_s],axis=0) #ベテランは不足グラフに反映する

    sum_staff = df_nonew['労働時間'].sum()
    sum_new = df_new['労働時間'].sum()
    sum_s = df_calc_s['労働時間'].sum()
    total_work = sum_staff + sum_new + sum_s

    st.header('労働時間集計')
    st.write('スタッフ労働時間合計：'+str(sum_staff))
    st.write('社員労働時間合計：'+str(sum_s))
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

    ##不足のみヒストグラム(帳票出力用)p2
    df_husoku = df_syukei[['index','不足']]
    df_husoku = df_husoku[df_husoku['不足']<0]
    #図のy軸を５に固定、万が一６以上の時
    max_husoku = df_husoku['不足'].min()
    if max_husoku<-3:
        y_husoku = max_husoku
    else:
        y_husoku = -3
    #グラフ作成
    p2 = figure(height=210, width=723 ,x_range=(8,21), y_range=(y_husoku,0),title="不足確認グラフ", tools="save")
    p2.vbar(x=df_husoku['index'], top=df_husoku['不足'], width=0.5)
    p2 = fun.husoku_edit(p2)
    p2.yaxis.ticker = list(range(y_husoku,1))

    with tabb:
        st.bokeh_chart(p1, use_container_width=True)
        st.caption('この下↓のグラフを保存してください')
        st.bokeh_chart(p2, use_container_width=True)

    with tabc:
        st.caption('仕様上、数字の列は1桁のものは拘束開始時間、～.1のものは拘束終了時間を示します')
        st.dataframe(df_calc)

    with tabd:
        column1, column2, column3 ,column4 = st.columns(4)
        with column1:
            fun.define_role(df_calc,df_calc_s,'朝',date,8.5)
        with column2:
            fun.define_role(df_calc,df_calc_s,'売場',date1,20.5)
        with column3:
            fun.define_role(df_calc,df_calc_s,'入金',date1,20.5)
        with column4:
            fun.define_role(df_calc,df_calc_s,'集計',date1,20.5)
    
    with tabe:
        st.header('最終確認')
        st.checkbox('すべての時間帯で後方が存在しますか？')
        st.checkbox('連続労働時間が5時間を超えるスタッフはいませんか？')
        shift = fun.png_upload('シフトグラフをアップロードしてください')
        shain = fun.png_upload('社員シフトグラフをアップロードしてください')
        husoku = fun.png_upload('不足グラフをアップロードしてください')
        
        st.caption('※すべてのファイルをアップロードしてからOKを押してください')
        if st.button('OK'):
            mp.makepdf(df_calc,df_calc_s,d,sum_staff,sum_s,total_work,sum_new,shift,shain,husoku)
            
            ##df_calc出力
            df_calc = fun.separate_17(df_calc,date,date1)
            df_calc_s = fun.separate_17(df_calc_s,date,date1)
            df_all = pd.concat([df_calc,df_calc_s])
            csv = fun.convert_df(df_all)
            st.download_button(label="データ出力",data=csv,file_name=str(d)+'_出勤データ.csv',mime='text/csv')       