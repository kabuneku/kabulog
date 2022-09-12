from django.db import models

# Create your models here.

class Calc_etc(models.Model):
    n1 = 1
    n2 = 2
    n3 = 3
    sum = n1 + n2 + n3
    numbers = 3

    def ave(self):
        ave = self.sum / self.numbers
        return ave