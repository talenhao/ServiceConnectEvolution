nohup salt '*' state.apply SCE.agent --out=yaml --out-file-append --out-file=/tmp/agent.log.`date +%F` &
