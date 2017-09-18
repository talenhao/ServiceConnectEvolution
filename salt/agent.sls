ServiceConnectionEvolution:
  file.recurse:
    - name: /usr/local/_ServiceConnectionEvolution
    - source: salt://SCE/files/ServiceConnectionEvolution

python_requirements:
  cmd.run:
    - name: /usr/local/_python3.6.1/bin/pip3 install --upgrade -r /usr/local/_ServiceConnectionEvolution/sce_requirements.txt --no-index --find-links=file:///usr/local/_ServiceConnectionEvolution/pip_requirements/
    - cwd: /usr/local/_ServiceConnectionEvolution
    - watch:
      - file: ServiceConnectionEvolution

service_collect_agent:
  cmd.run:
    - name: /usr/local/_python3.6.1/bin/python3.6 /usr/local/_ServiceConnectionEvolution/scripts/collect.py
    - cwd: /usr/local/_ServiceConnectionEvolution
    - require:
      - cmd: python_requirements
