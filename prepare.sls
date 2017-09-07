python_require_common_package:
  pkg.installed:
    - pkgs:
      - gcc

python_setup:
  file.managed:
    - name: /usr/local/src/Python-3.6.1.tar.xz
    - source: salt://SCE/files/Python-3.6.1.tar.xz
    - mode: 644
  cmd.run:
    - name: tar xf Python-3.6.1.tar.xz && cd Python-3.6.1 && ./configure --prefix=/usr/local/_python3.6.1 && make && make install
    - cwd: /usr/local/src/
    - require: 
      - pkg: python_require_common_package
#    - onchanges:
#      - file: python_setup
    - creates:
      - /usr/local/_python3.6.1
#    - unless: test -d /usr/local/_python3.6.1

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
      
python_requirements:
  cmd.run:
    - name: /usr/local/_python3.6.1/bin/pip3 install -r sce_requirements.txt
    - cwd: /usr/local/_ServiceConnectionEvolution
    - require:
      - cmd: python_setup
    - watch:
      - file: sce_requirements.txt
