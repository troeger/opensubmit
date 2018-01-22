This directory contains a set of submission cases,
each simulating a possible student submission scenario. 

Each case is stored in a subdirectory with a name
that encodes the particular case. The meaning of the 
different character positions in the directory name
is the following:

- Pos 1: Number and kind of of code files:
  - '0': Zero code files
  - '1': One working code file
  - 'b': One broken code file (compilation failure)
  - 'd': One deadlocked code file (execution timeout)
- Pos 2: Number of non-code files ('0'/'1')
- Pos 3: Number of Makefiles ('0'/'1')
- Pos 4: Number of configure files ('0'/'1')
- Pos 5: Submission zipped ('t'rue/'f'alse)
- Pos 6: Submission files in single subdirectory in archive ('t'rue/'f'alse)
- Pos 7: Validator format:
  - 't': Zipped (validator.zip)
  - 'f': Not zipped (validator.py)
  - 'm': Zipped (validator.zip), but missing validator.py file inside

Folders that start with 'regression_' do not follow the pattern above,
but represent single cases for regressions to be tested.
