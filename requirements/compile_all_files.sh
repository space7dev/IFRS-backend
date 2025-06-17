rm base.txt dev.txt local.txt production.txt staging.txt
pip-compile base.in && pip-compile dev.in && pip-compile local.in && pip-compile staging.in && pip-compile production.in