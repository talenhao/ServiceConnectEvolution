python_require_common_package:
  pkg.installed:
    - pkgs:
      - gcc
      - xz
      - zlib-devel
      - openssl-devel
ok_file_missing:
  file.missing:
    - name: /usr/local/_python3.6.1/ok.file

python_setup:
  file.managed:
    - name: /usr/local/src/Python-3.6.1.tar.xz
    - source: salt://SCE/files/Python-3.6.1.tar.xz
    - mode: 644
  cmd.run:
    - name: tar xf Python-3.6.1.tar.xz && cd Python-3.6.1 && ./configure --prefix=/usr/local/_python3.6.1 >> /tmp/python3.6.1.make.info && make >> /tmp/python3.6.1.make.info && make install >>/tmp/python3.6.1.make.info
    - cwd: /usr/local/src/
    - require: 
      - pkg: python_require_common_package
      - file: python_setup
      - file: ok_file_missing
#    - creates:
#      - /usr/local/_python3.6.1
    - output_loglevel: quiet

ok_file:
  file.touch:
    - name: /usr/local/_python3.6.1/ok.file
    - require:
      - cmd: python_requirements

ServiceConnectionEvolution:
  file.recurse:
    - name: /usr/local/_ServiceConnectionEvolution
    - source: salt://SCE/files/ServiceConnectionEvolution
    - require:
      - file: sce_requirements.txt

sce_requirements.txt:
  file.managed:
    - name: /usr/local/_ServiceConnectionEvolution/sce_requirements.txt
    - source: salt://SCE/files/ServiceConnectionEvolution/sce_requirements.txt
    - makedirs: True
    - require:
      - cmd: python_setup
      
python_requirements:
  cmd.run:
    - name: /usr/local/_python3.6.1/bin/pip3 install --trusted-host pypi.python.org -r sce_requirements.txt
    - cwd: /usr/local/_ServiceConnectionEvolution
    - watch:
      - file: sce_requirements.txt
