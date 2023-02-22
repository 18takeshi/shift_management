import streamlit as st

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.lib.units import cm,mm
from reportlab.lib.pagesizes import A4, portrait
import os

### PDFファイルを生成する ###
def makepdf(df_calc,df_calc_s,d,sum_staff,sum_s,sum_con,total_work,sum_new,shift,shain):
    file_name = str(d)+'_シフト.pdf'    # ファイル名を設定
    pdf = canvas.Canvas(file_name, pagesize=portrait(A4))    # PDFを生成、サイズはA4
    pdf.saveState()    # セーブ

    pdf.setAuthor('matsu')
    pdf.setTitle(str(d)+'シフト')
    pdf.setSubject('TEST')

    ##グラフの追加
    pdf.drawInlineImage(shift, 55*mm, 55*mm, 140*mm, 220*mm)
    pdf.drawInlineImage(shift, 55*mm, 275*mm, 140*mm, 220*mm)
    pdf.drawInlineImage(shain, 55*mm, 15*mm, 140*mm, 40*mm)
    ### 四角形を描画して２枚目の社員グラフを隠す###
    pdf.setFillColorRGB(255,255,255)
    pdf.rect(55*mm, 279*mm, 195*mm, 297*mm, stroke=0, fill=1)
    pdf.setFillColorRGB(0, 0, 0)

    ### 線の描画 ###
    pdf.setLineWidth(0.8)
    pdf.line(5*cm, 27.5*cm, 5*cm, 2*cm)
    pdf.line(3.3*cm, 27.5*cm, 3.3*cm, 2*cm)
    pdf.line(2*cm, 27.5*cm, 2*cm, 2*cm)

    ### フォント、サイズを設定 ###
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiKakuGo-W5'))
    pdf.setFont('HeiseiKakuGo-W5', 12)
    pdf.drawString(2.2*cm, 27.7*cm, '確認')
    pdf.drawString(3.6*cm, 27.7*cm, '当番')
    pdf.drawString(19.6*cm, 27.7*cm, '時間')
    #労働時間集計
    pdf.drawString(2*cm, 0.5*cm, '労働時間集計')
    pdf.drawString(5*cm, 0.5*cm, '一般：'+str(sum_staff))
    pdf.drawString(8*cm, 0.5*cm, '新人：'+str(sum_new))
    pdf.drawString(10.5*cm, 0.5*cm, '社員：'+str(sum_s))
    pdf.drawString(13*cm, 0.5*cm, '契約：'+str(sum_con))
    pdf.drawString(15.5*cm, 0.5*cm, '総計：'+str(total_work))

    #労働時間,当番の反映
    def write_role(le,sta,df_calc):
        length = le/len(df_calc['労働時間'])
        strart = sta-length/2
        rev = df_calc.iloc[::-1, :] #逆にする
        for k,r in zip(rev['労働時間'],rev['当番']):
            pdf.drawString(19.7*cm, float(strart)*cm, str(k))
            pdf.drawString(3.6*cm, float(strart)*cm, r)
            strart = strart - length

    write_role(21.4,27.25,df_calc)  #スタッフ分
    write_role(3.4,5.3,df_calc_s)  #社員分

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