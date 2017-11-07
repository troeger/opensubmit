Teacher manual
==============

OpenSubmit distinguishes between the **student frontend**, the **teacher backend** and the **test machines**. This manual only deals with the **teacher backend**.

Managing study programs
-----------------------

Managing courses
----------------

Managing grading schemes
------------------------

Managing assignments
--------------------

Managing submissions
--------------------

A student submission can be in different states. Each of the states is represented in a different way in student frontend and the teacher backend. 

The internal states are represented in different ways to frontend and backend users:

.. literalinclude:: ../web/opensubmit/models/submission.py
   :language: python
   :lines: 95-201



