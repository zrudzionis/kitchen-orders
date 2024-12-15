#!/bin/bash

pylint src/ test/

exit_code=$?

# 1 fatal, 2 error
if [[ $exit_code -eq 1 || $exit_code -eq 2 ]]; then
  exit 1
else
  exit 0
fi
