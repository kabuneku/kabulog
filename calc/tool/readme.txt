フォルダをパッケージ化するのに
_init.py
という名の空ファイルが必要であることに注意！

from tool import tech_func as tf
とmain の program に記述すれば

program_folder
	|_mainprogram.py
	|_tool ( フォルダ )   ← パッケージ．モジュールの詰め合わせ．
	     |_  _init_.py
	     |_tech_func.py    ← これを読み込む.モジュールは関数の詰め合わせ．