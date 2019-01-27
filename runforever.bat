@ECHO OFF
copy bot.py DeepCreamPy/bot.py
cd DeepCreamPy
:loop
python bot.py
goto loop