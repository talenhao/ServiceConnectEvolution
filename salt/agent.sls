ServiceConnectionEvolution:
  file.recurse:
    - name: /usr/local/_ServiceConnectionEvolution
    - source: salt://SCE/files/ServiceConnectionEvolution

      
service_collect_agent:
  cmd.run:
    - name: /usr/local/_python3.6.1/bin/python3.6 /usr/local/_ServiceConnectionEvolution/service_collect_agent.py
    - cwd: /usr/local/_ServiceConnectionEvolution
    - require:
      - file: ServiceConnectionEvolution
