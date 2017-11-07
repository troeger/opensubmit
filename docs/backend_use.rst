Teacher manual
==============

The unique capability of OpenSubmit is the support for submission validation.

Students upload their programming exercise solution as archive, which typically contains a set of source code files.   Any attachment to an assignment solution is unpacked and tested by scripts provided by the course tutors or the course owner.

Validation makes the life of the corrector less miserable, because after the deadline, all gradable solutions are 'valid' (e.g. compile). Students also seem to like the idea of having a validated solution, so that they do not fail due to technical difficulties at the correctors side.

Since OpenSubmit is only for assignment submissions, it has no management of course participants. 
Everybody who can perform a successful login can submit solutions. 

Submission states
-----------------

A student submission can be in different states. Each of the states is represented in a different way in student frontend and the teacher backend. 

The internal states are represented in different ways to frontend and backend users:

.. literalinclude:: ../web/opensubmit/models/submission.py
   :language: python
   :lines: 95-201



