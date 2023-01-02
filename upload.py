##ファイル読み込み
import streamlit as st
from datetime import datetime
import pandas as pd
import numpy as np
#bokehグラフ
from bokeh.plotting import figure
from bokeh.io import export_png
#関数ファイル
import function as fun
import makepdf as mp
#基本シフト表
df_kihon = pd.read_excel('基本シフト表集計.xlsx',index_col=0)

st.title('ベルーフ静岡店 シフト作成アプリ')
st.caption('作成者：松澤  ver1.0 2023/1/2') 

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
    st.sidebar.write('社員編集(レジに入る時間のみ編集してください)')
    df_calc_s = fun.rest_edit(df_calc_s,date,date1)
      
    #make_graph関数でグラフ作成
    p = fun.make_graph(df_calc,date,date1,1023)
    ps = fun.make_graph(df_calc_s,date,date1,200)

    #シフトグラフのタブ化
    taba,tabb,tabc = st.tabs(['シフトグラフ','不足確認グラフ','出勤データ'])

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

    #不足ヒストグラム作成
    p1 = figure(height=350, width=723 ,x_range=(8,21), title="不足確認グラフ",toolbar_location=None, tools="")
    p1.vbar(x=df_syukei['index'], top=df_syukei['不足'], width=0.3)
    #罫線のスタイル
    p1.xaxis.bounds = (8,22)
    p1.xaxis.ticker.max_interval=1
    p1.yaxis.ticker.max_interval=1
    p1.xaxis.ticker.num_minor_ticks = 2
    p1.yaxis.ticker.num_minor_ticks = 0
    p1.xgrid.minor_grid_line_color = 'black'
    p1.xgrid.minor_grid_line_dash = [6,4]
    p1.xgrid.minor_grid_line_alpha = 0.1
    p1.xaxis.axis_label = "勤務時間"
    p1.yaxis.axis_label = "不足人数"
    p1.xaxis.major_label_text_font_size = '20px'
    p1.yaxis.major_label_text_font_size = '20px'

    with tabb:
        st.bokeh_chart(p1, use_container_width=True)
    with tabc:
        st.dataframe(df_calc)

    st.header('役割決定')
    tab1, tab2, tab3 ,tab4 = st.columns(4)
    with tab1:
        asa  = fun.define_role(df_calc,df_calc_s,'朝',date,8.5)
    with tab2:
        uriba = fun.define_role(df_calc,df_calc_s,'売場',date1,20.5)
    with tab3:
        nyukin = fun.define_role(df_calc,df_calc_s,'入金',date1,20.5)
    with tab4:
        nyukei = fun.define_role(df_calc,df_calc_s,'集計',date1,20.5)
    
    if st.button('確定') :
        ##グラフのエクスポート
        export_png(p, filename="sift.png",width=723,height=1023)
        export_png(ps, filename="shain.png",width=723,height=200)

        ##不足のみヒストグラム(帳票出力用)
        df_husoku = df_syukei[['index','不足']]
        df_husoku = df_husoku[df_husoku['不足']<0]
        #図のy軸を５に固定、万が一６以上の時
        max_husoku = df_husoku['不足'].min()
        if max_husoku<-3:
            y_husoku = max_husoku
        else:
            y_husoku = -3
        #グラフ作成
        p2 = figure(height=210, width=723 ,x_range=(8,21), y_range=(y_husoku,0),title="不足確認グラフ",toolbar_location=None, tools="")
        p2.vbar(x=df_husoku['index'], top=df_husoku['不足'], width=0.5)
        #罫線のスタイル
        p2.xaxis.bounds = (8,22)
        p2.xaxis.ticker.max_interval=1
        p2.xaxis.ticker.num_minor_ticks = 2
        p2.xgrid.minor_grid_line_color = 'black'
        p2.xgrid.minor_grid_line_dash = [6,4]
        p2.xgrid.minor_grid_line_alpha = 0.1
        p2.xaxis.axis_label = "勤務時間"
        p2.yaxis.axis_label = "不足人数"
        p2.xaxis.major_label_text_font_size = '20px'
        p2.yaxis.major_label_text_font_size = '20px'
        p2.yaxis.ticker = list(range(y_husoku,1))
        export_png(p2, filename="husoku.png",width=723,height=210)

        ##pdf出力
        mp.makepdf(df_calc,df_calc_s,d,sum_staff,sum_s,total_work,sum_new)
        
        ##df_calc出力
        df_calc = fun.separate_17(df_calc,date,date1)
        df_calc_s = fun.separate_17(df_calc_s,date,date1)
        df_all = pd.concat([df_calc,df_calc_s])
        csv = fun.convert_df(df_all)
        st.download_button(label="データ出力",data=csv,file_name='出勤データ'+str(d)+'.csv',mime='text/csv')       