import streamlit as st

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import cm,mm
from reportlab.lib.pagesizes import A4, portrait

def makepdf(df_calc,df_calc_s,d,sum_staff,sum_s,total_work,sum_new):
### PDFファイルを生成する ###
    file_name = str(d)+'_シフト.pdf'    # ファイル名を設定
    pdf = canvas.Canvas(file_name, pagesize=portrait(A4))    # PDFを生成、サイズはA4
    pdf.saveState()    # セーブ

    pdf.setAuthor('matsu')
    pdf.setTitle(str(d)+'シフト')
    pdf.setSubject('TEST')

    pdf.drawInlineImage('sift.png', 55*mm, 85*mm, 140*mm, 197*mm)
    pdf.drawInlineImage('shain.png', 60*mm, 45*mm, 135*mm, 40*mm)
    pdf.drawInlineImage('husoku.png', 65*mm, 5*mm, 130*mm, 40*mm)

    ### 線の描画 ###
    pdf.setLineWidth(0.8)
    pdf.line(5*cm, 27.66*cm, 5*cm, 5.5*cm)
    pdf.line(3.3*cm, 27.66*cm, 3.3*cm, 5.5*cm)
    pdf.line(2*cm, 27.66*cm, 2*cm, 5.5*cm)

    ### フォント、サイズを設定 ###
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    pdf.setFont('HeiseiKakuGo-W5', 12)
    pdf.drawString(2.2*cm, 28*cm, '確認')
    pdf.drawString(3.6*cm, 28*cm, '当番')
    pdf.drawString(19*cm, 28*cm, '労働時間')
    #労働時間集計
    pdf.drawString(2.5*cm, 4.7*cm, '労働時間集計')
    pdf.drawString(1.8*cm, 3.7*cm, 'スタッフ合計：'+str(sum_staff))
    pdf.drawString(1.8*cm, 2.7*cm, '新人合計：'+str(sum_new))
    pdf.drawString(1.8*cm, 1.7*cm, '社員合計：'+str(sum_s))
    pdf.drawString(1.8*cm, 0.7*cm, '合計労働時間：'+str(total_work))

    #労働時間,当番の反映
    length = 18.14/len(df_calc['労働時間'])
    strart = 27.5-length/2
    rev = df_calc.iloc[::-1, :] #逆にする
    for k,r in zip(rev['労働時間'],rev['当番']):
        pdf.drawString(19.7*cm, float(strart)*cm, str(k))
        pdf.drawString(3.6*cm, float(strart)*cm, r)
        strart = strart - length
    
    length = 2.42/len(df_calc_s['労働時間'])
    rev = df_calc_s.iloc[::-1, :] #逆にする
    strart = 7.8-length/2
    for k,r in zip(rev['労働時間'],rev['当番']):
        pdf.drawString(19.7*cm, float(strart)*cm, str(k))
        pdf.drawString(3.6*cm, float(strart)*cm, r)
        strart = strart - length 

    ### 文字を描画 ###
    pdf.setFont('HeiseiKakuGo-W5', 20)    # フォントサイズの変更
    width, height = A4  # A4用紙のサイズ
    week = d.strftime('%a')
    if week == 'Sun':
        jweek = '日'
    elif week == 'Mon':
        jweek = '月'
    elif week == 'Tue':
        jweek = '火'
    elif week == 'Wed':
        jweek = '水'
    elif week == 'Thu':
        jweek = '木'
    elif week == 'Fri':
        jweek = '金'
    else:
        jweek = '土'
    pdf.drawCentredString(width / 2, height - 12*mm, '売場シフト表　'+str(d)+' ('+str(jweek)+') ')

    #pdfをセーブしてダウンロードボタンに合う形式にする
    pdf.restoreState()
    try:
        pdf.save()
    except PermissionError:
        st.write('作成したシフトグラフと同じ日のPDFファイルを閉じてください')
    with open(file_name,'rb') as pdf_file:  
        PDFbyte = pdf_file.read()

    st.download_button(label="帳票出力",data=PDFbyte,file_name=file_name,mime="application/octet-stream")
    #社員番号入れれる