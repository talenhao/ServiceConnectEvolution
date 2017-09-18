python_require_common_package:
  pkg.installed:
    - pkgs:
      - gcc
      - xz
      - zlib-devel
      - openssl-devel

python_setup:
  file.managed:
    - name: /usr/local/src/Python-3.6.1.tar.xz
    - source: salt://SCE/files/Python-3.6.1.tar.xz
    - mode: 644
  cmd.run:
    - name: if test -f /usr/local/_python3.6.1/ok.file ; then echo OK ; else tar xf Python-3.6.1.tar.xz && cd Python-3.6.1 && ./configure --prefix=/usr/local/_python3.6.1 >> /tmp/python3.6.1.make.info && make >> /tmp/python3.6.1.make.info && make install >>/tmp/python3.6.1.make.info ; fi
    - cwd: /usr/local/src/
    - require: 
      - pkg: python_require_common_package
      - file: python_setup
#    - creates:
#      - /usr/local/_python3.6.1
    - output_loglevel: quiet


ServiceConnectionEvolution:
  file.recurse:
    - name: /usr/local/_ServiceConnectionEvolution
    - source: salt://SCE/files/ServiceConnectionEvolution
    - require:
      - cmd: python_setup

python_requirements:
  cmd.run:
    - name: /usr/local/_python3.6.1/bin/pip3 install -r /usr/local/_ServiceConnectionEvolution/sce_requirements.txt --no-index --find-links=file:///usr/local/_ServiceConnectionEvolution/pip_requirements/
    - cwd: /usr/local/_ServiceConnectionEvolution
    - watch:
      - file: ServiceConnectionEvolution


ok_file:
  file.touch:
    - name: /usr/local/_python3.6.1/ok.file
    - require:
      - cmd: python_requirements
