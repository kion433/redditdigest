@echo off
cd /d "c:\Users\HP\Desktop\newidea"
call .venv\Scripts\activate
python main.py
echo Bot run finished at %date% %time% >> bot.log
