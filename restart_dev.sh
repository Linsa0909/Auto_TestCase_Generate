#!/bin/bash
kill $(ps aux | grep -E 'uvicorn|vite' | grep -v grep | awk '{print $2}')
  cd /mnt/c/Users/Linsa/Test_Case_Auto && bash dev.sh
