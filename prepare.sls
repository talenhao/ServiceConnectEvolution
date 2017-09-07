python_require_common_package:
  pkg.installed:
    - pkgs:
      - gcc

python_for_collect:
  file.managed:
    - name: /var/local/python2.7.13.tar.gz
    - source: salt://collect2yed/files/python2.7.13.tar.gz
    - mode: 644
  cmd.run:
    - name: tar zxf python2.7.13.tar.gz
    - cwd: /var/local/
    - require: 
      - file: python_for_collect
      - pkg: python_require_common_package
    - onchanges:
      - file: python_for_collect
