from django.db import models
from .tool import tech_func as tf
import pandas as pd
# Create your models here.

class Calc_etc(models.Model):
    df = pd.read_csv("calc/1961.csv")
    df["EMA30"] = df["close"].ewm(span=30).mean()

    def ave(self):
        ave = self.sum / self.numbers
        return ave