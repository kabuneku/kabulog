from django.shortcuts import render
from .models import Calc_etc
from plotly.subplots import make_subplots
from .tool import tech_func as tf
import pandas as pd


# Create your views here.
def calc_ave(request): 
    df = pd.read_csv("calc/1961.csv")
    df["EMA30"] = df["close"].ewm(span=30).mean()
    fig = make_subplots(rows=1, cols=1)
    tf.plot_Candle(fig,df,"1961",1,1)
    tf.plot_Scatter(fig,df,"datetime","EMA30","blue",1,1)
    tf.fig_update_layout(fig,"1961")
    tf.date_break(fig,df)
    tf.fig_update_axes(fig)
    return render(request, 'calc/calc_ave.html', {})
