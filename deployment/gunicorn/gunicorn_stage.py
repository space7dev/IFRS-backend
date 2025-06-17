# BINDING SOCKET HERE
bind = "unix:/run/staging-gunicorn.sock"

# 'NUMBER_OF_WORKERS_IN_INT' usually 2*cpu_core + 1
workers = 1  # assuming single core cpu

# USER
user = "django"
